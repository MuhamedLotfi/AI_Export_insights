"""
Vector Search Service - pgvector-powered semantic search
Uses BAAI/bge-m3 (SentenceTransformer) + PostgreSQL pgvector extension.
Enhanced with batch processing, HNSW indexing, and content hash deduplication.
"""
import logging
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class VectorService:
    """Manages vector embeddings and semantic search via pgvector"""

    _instance: Optional['VectorService'] = None

    @classmethod
    def get_instance(cls) -> 'VectorService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if VectorService._instance is not None:
            raise Exception("Use get_instance() instead")

        from backend.config import VECTOR_CONFIG
        self.embedding_model = VECTOR_CONFIG["embedding_model"]
        self.dimensions = VECTOR_CONFIG["embedding_dimensions"]
        self.enabled = VECTOR_CONFIG["enabled"]
        self.provider = VECTOR_CONFIG.get("embedding_provider", "huggingface")
        self._engine = None
        self._ready = False
        self._model_instance = None

        if self.enabled:
            self._initialize()

    def _initialize(self):
        """Set up pgvector extension, embeddings table (HNSW index), and load local model"""
        try:
            # Load local model if provider is huggingface
            if self.provider == "huggingface":
                try:
                    import torch
                    from sentence_transformers import SentenceTransformer
                    
                    # Prefer CUDA if available, else CPU
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    logger.info(f"Loading local embedding model: {self.embedding_model} on device={device}...")
                    
                    # Try loading from local cache first (skip HuggingFace HTTP checks)
                    try:
                        self._model_instance = SentenceTransformer(
                            self.embedding_model,
                            device=device,
                            local_files_only=True
                        )
                        logger.info(f"Local model loaded from cache on {device} (no network).")
                    except Exception:
                        # First-time download: model not cached yet
                        logger.info("Model not in local cache, downloading from HuggingFace...")
                        self._model_instance = SentenceTransformer(
                            self.embedding_model,
                            device=device
                        )
                        logger.info(f"Model downloaded and loaded successfully on {device}.")
                except ImportError as ie:
                    logger.error(f"sentence_transformers or torch not installed: {ie}.")
                    raise ie
                except Exception as e:
                    logger.error(f"Failed to load local model {self.embedding_model}: {e}.")
                    raise e

            from backend.ai_agent.database_service import get_engine
            self._engine = get_engine()
            if not self._engine:
                logger.warning("VectorService: no database engine available")

            if self._engine:
                from sqlalchemy import text
                with self._engine.connect() as conn:
                    # Enable pgvector extension
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    conn.commit()

                    # Create embeddings table with content_hash for dedup
                    conn.execute(text(f"""
                        CREATE TABLE IF NOT EXISTS embeddings (
                            id SERIAL PRIMARY KEY,
                            table_name VARCHAR(255) NOT NULL,
                            row_id VARCHAR(255),
                            content_text TEXT NOT NULL,
                            content_hash VARCHAR(64),
                            metadata JSONB,
                            embedding vector({self.dimensions}),
                            created_at TIMESTAMP DEFAULT NOW(),
                            updated_at TIMESTAMP DEFAULT NOW()
                        )
                    """))
                    conn.commit()

                    # Add content_hash column if missing (for existing DBs)
                    try:
                        conn.execute(text("""
                            ALTER TABLE embeddings ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64)
                        """))
                        conn.execute(text("""
                            ALTER TABLE embeddings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()
                        """))
                        conn.commit()
                    except Exception:
                        conn.rollback()

                    # Create HNSW index (better than IVFFlat for incremental inserts)
                    # Drop old IVFFlat index if it exists, create HNSW
                    try:
                        conn.execute(text("DROP INDEX IF EXISTS idx_embeddings_vector"))
                        conn.commit()
                    except Exception:
                        conn.rollback()

                    try:
                        conn.execute(text("""
                            CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw
                            ON embeddings USING hnsw (embedding vector_cosine_ops)
                            WITH (m = 16, ef_construction = 64)
                        """))
                        conn.commit()
                    except Exception as e:
                        logger.warning(f"HNSW index creation note: {e}")
                        try:
                            conn.rollback()
                        except Exception:
                            pass

                    # Create index on table_name + content_hash for fast dedup checks
                    try:
                        conn.execute(text("""
                            CREATE INDEX IF NOT EXISTS idx_embeddings_table_hash
                            ON embeddings (table_name, content_hash)
                        """))
                        conn.commit()
                    except Exception:
                        try:
                            conn.rollback()
                        except Exception:
                            pass

            self._ready = True
            logger.info(f"VectorService ready (model={self.embedding_model}, dim={self.dimensions}, provider={self.provider}, index=HNSW)")

        except Exception as e:
            logger.error(f"VectorService init error: {e}")
            self._ready = False

    # ── Embedding Generation ──────────────────────────────────────────

    def _generate_embedding(self, text_content: str) -> Optional[List[float]]:
        """Generate embedding vector for a single text"""
        try:
            if self.provider == "huggingface":
                if self._model_instance:
                    embedding = self._model_instance.encode(text_content)
                    return embedding.tolist()
                else:
                    logger.error("HuggingFace provider selected but model is not loaded")
                    return None
            elif self.provider == "ollama":
                import ollama
                response = ollama.embeddings(
                    model=self.embedding_model,
                    prompt=text_content
                )
                return response.get("embedding")
            else:
                logger.error(f"Unknown provider: {self.provider}")
                return None
        except Exception as e:
            logger.error(f"Embedding generation error ({self.provider}): {e}")
            return None

    def _generate_embeddings_batch(self, texts: List[str], batch_size: int = 64) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches.
        Uses SentenceTransformer batch encoding for 10-50x speedup.
        """
        if not texts:
            return []

        all_embeddings = []

        try:
            if self.provider == "huggingface":
                if self._model_instance:
                    # Process in batches for memory safety
                    for i in range(0, len(texts), batch_size):
                        batch = texts[i:i + batch_size]
                        batch_embeddings = self._model_instance.encode(batch, show_progress_bar=False)
                        all_embeddings.extend([emb.tolist() for emb in batch_embeddings])
                    return all_embeddings
                else:
                    logger.error("HuggingFace provider selected but model is not loaded")
                    return [None] * len(texts)
            elif self.provider == "ollama":
                # Fallback: generate one at a time for Ollama
                for text in texts:
                    emb = self._generate_embedding(text)
                    all_embeddings.append(emb)
                return all_embeddings
            else:
                logger.error(f"Unknown provider: {self.provider}")
                return [None] * len(texts)
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            return [None] * len(texts)

    @staticmethod
    def _content_hash(content: str) -> str:
        """Generate SHA-256 hash of content for dedup"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

    # ── Single Row Indexing ───────────────────────────────────────────

    def index_row(self, table_name: str, row_id: str, content: str, metadata: Optional[Dict] = None):
        """Index a single row for vector search"""
        if not self._ready:
            return

        content_hash = self._content_hash(content)

        # Check if this exact content already exists (dedup)
        try:
            from sqlalchemy import text
            with self._engine.connect() as conn:
                existing = conn.execute(text("""
                    SELECT id FROM embeddings
                    WHERE table_name = :table_name AND row_id = :row_id AND content_hash = :hash
                    LIMIT 1
                """), {"table_name": table_name, "row_id": str(row_id), "hash": content_hash})
                if existing.fetchone():
                    return  # Already indexed with same content
        except Exception:
            pass

        embedding = self._generate_embedding(content)
        if not embedding:
            return

        try:
            from sqlalchemy import text
            with self._engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO embeddings (table_name, row_id, content_text, content_hash, metadata, embedding, updated_at)
                    VALUES (:table_name, :row_id, :content, :hash, :metadata, :embedding, NOW())
                """), {
                    "table_name": table_name,
                    "row_id": str(row_id),
                    "content": content,
                    "hash": content_hash,
                    "metadata": json.dumps(metadata) if metadata else None,
                    "embedding": str(embedding)
                })
                conn.commit()
        except Exception as e:
            logger.error(f"Error indexing row: {e}")

    # ── Batch Row Indexing ────────────────────────────────────────────

    def index_rows_batch(
        self,
        table_name: str,
        rows: List[Dict[str, Any]],
        text_columns: Optional[List[str]] = None,
        batch_size: int = 64,
        skip_existing: bool = True
    ) -> int:
        """
        Batch-index rows from a table using batch embedding.
        Returns the number of rows actually indexed.
        """
        if not self._ready:
            logger.warning("VectorService not ready, skipping batch index")
            return 0

        # Build content strings and collect row IDs
        contents = []
        row_ids = []
        content_hashes = []

        for i, row in enumerate(rows):
            row_id = str(row.get("Id") or row.get("id") or i)

            # Build text content from specified columns or auto-detect
            if text_columns:
                parts = []
                for c in text_columns:
                    val = row.get(c)
                    if val is not None and str(val).strip():
                        parts.append(f"{c}: {val}")
            else:
                parts = []
                for k, v in row.items():
                    if v is not None and isinstance(v, (str, int, float)):
                        val_str = str(v).strip()
                        if len(val_str) > 1 and k.lower() not in ('id',):
                            parts.append(f"{k}: {val_str}")

            content = f"Table: {table_name} | " + " | ".join(parts)
            if len(content.strip()) <= len(f"Table: {table_name} | "):
                continue  # Skip empty content

            c_hash = self._content_hash(content)
            contents.append(content)
            row_ids.append(row_id)
            content_hashes.append(c_hash)

        if not contents:
            return 0

        # Filter out already-indexed rows if skip_existing
        if skip_existing and self._engine:
            try:
                from sqlalchemy import text
                with self._engine.connect() as conn:
                    # Get existing hashes for this table
                    result = conn.execute(text(
                        "SELECT content_hash FROM embeddings WHERE table_name = :tn"
                    ), {"tn": table_name})
                    existing_hashes = {r[0] for r in result if r[0]}

                # Filter
                filtered = [
                    (c, rid, ch) for c, rid, ch in zip(contents, row_ids, content_hashes)
                    if ch not in existing_hashes
                ]
                if not filtered:
                    logger.info(f"  [{table_name}] All {len(contents)} rows already indexed, skipping.")
                    return 0

                contents, row_ids, content_hashes = zip(*filtered)
                contents = list(contents)
                row_ids = list(row_ids)
                content_hashes = list(content_hashes)
            except Exception as e:
                logger.warning(f"Dedup check failed: {e}, proceeding without dedup")

        # Generate embeddings in batch
        logger.info(f"  [{table_name}] Generating embeddings for {len(contents)} rows...")
        embeddings = self._generate_embeddings_batch(contents, batch_size=batch_size)

        # Insert into database
        indexed_count = 0
        try:
            from sqlalchemy import text
            with self._engine.connect() as conn:
                for i in range(0, len(contents), batch_size):
                    batch_contents = contents[i:i + batch_size]
                    batch_ids = row_ids[i:i + batch_size]
                    batch_hashes = content_hashes[i:i + batch_size]
                    batch_embeddings = embeddings[i:i + batch_size]

                    for content, rid, c_hash, emb in zip(batch_contents, batch_ids, batch_hashes, batch_embeddings):
                        if emb is None:
                            continue
                        try:
                            conn.execute(text("""
                                INSERT INTO embeddings (table_name, row_id, content_text, content_hash, metadata, embedding, updated_at)
                                VALUES (:table_name, :row_id, :content, :hash, :metadata, :embedding, NOW())
                            """), {
                                "table_name": table_name,
                                "row_id": rid,
                                "content": content,
                                "hash": c_hash,
                                "metadata": json.dumps({"table": table_name}),
                                "embedding": str(emb)
                            })
                            indexed_count += 1
                        except Exception as e:
                            logger.warning(f"  Error inserting row {rid}: {e}")

                    conn.commit()

        except Exception as e:
            logger.error(f"Batch insert error for {table_name}: {e}")

        logger.info(f"  [{table_name}] Indexed {indexed_count}/{len(contents)} rows")
        return indexed_count

    # ── Legacy Batch Index (compatibility) ────────────────────────────

    def index_table(self, table_name: str, rows: List[Dict[str, Any]], text_columns: Optional[List[str]] = None):
        """Batch-index all rows from a table (uses new batch method)"""
        return self.index_rows_batch(table_name, rows, text_columns=text_columns)

    # ── Semantic Search ───────────────────────────────────────────────

    def semantic_search(self, query: str, top_k: int = 10, table_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Perform semantic similarity search"""
        if not self._ready:
            logger.warning("VectorService not ready")
            return []

        query_embedding = self._generate_embedding(query)
        if not query_embedding:
            return []

        try:
            from sqlalchemy import text

            if table_filter:
                sql = """
                    SELECT table_name, row_id, content_text, metadata,
                           1 - (embedding <=> CAST(:query_vec AS vector)) AS similarity
                    FROM embeddings
                    WHERE table_name = :table_filter
                    ORDER BY embedding <=> CAST(:query_vec AS vector)
                    LIMIT :top_k
                """
                params = {
                    "query_vec": str(query_embedding),
                    "table_filter": table_filter,
                    "top_k": top_k
                }
            else:
                sql = """
                    SELECT table_name, row_id, content_text, metadata,
                           1 - (embedding <=> CAST(:query_vec AS vector)) AS similarity
                    FROM embeddings
                    ORDER BY embedding <=> CAST(:query_vec AS vector)
                    LIMIT :top_k
                """
                params = {
                    "query_vec": str(query_embedding),
                    "top_k": top_k
                }

            with self._engine.connect() as conn:
                result = conn.execute(text(sql), params)
                results = []
                for row in result:
                    row_dict = dict(row._mapping)
                    if row_dict.get("metadata") and isinstance(row_dict["metadata"], str):
                        try:
                            row_dict["metadata"] = json.loads(row_dict["metadata"])
                        except Exception:
                            pass
                    results.append(row_dict)
                return results

        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []

    # ── Schema Indexing ───────────────────────────────────────────────

    def index_schema(self, schema_info: Dict[str, List[str]], table_descriptions: Optional[Dict[str, str]] = None):
        """Index database schema for table discovery"""
        if not self._ready:
            return

        logger.info("Indexing database schema...")
        table_descriptions = table_descriptions or {}

        # Clear existing schema embeddings
        try:
            from sqlalchemy import text
            with self._engine.connect() as conn:
                conn.execute(text("DELETE FROM embeddings WHERE table_name = '__schema_metadata__'"))
                conn.commit()
        except Exception as e:
            logger.error(f"Error clearing schema index: {e}")

        for table_name, columns in schema_info.items():
            if table_name in ["embeddings", "__EFMigrationsHistory"]:
                continue

            col_str = ", ".join(columns)
            desc = table_descriptions.get(table_name, "")

            content = f"Table: {table_name}\nColumns: {col_str}\nDescription: {desc}"
            content += f"\nKeywords: {table_name.replace('_', ' ')} {table_name}"

            self.index_row(
                table_name="__schema_metadata__",
                row_id=table_name,
                content=content,
                metadata={"table": table_name, "columns": columns}
            )

        logger.info(f"Indexed schema for {len(schema_info)} tables")

    # ── Table Discovery ───────────────────────────────────────────────

    def find_tables(self, query: str, top_k: int = 5) -> List[str]:
        """Find most relevant tables for a query using vector search"""
        results = self.semantic_search(query, top_k=top_k, table_filter="__schema_metadata__")

        tables = []
        seen = set()

        for res in results:
            meta = res.get("metadata", {})
            table = meta.get("table")
            if table and table not in seen:
                tables.append(table)
                seen.add(table)

        return tables

    # ── Statistics ────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get vector index statistics"""
        if not self._ready:
            return {"ready": False}

        try:
            from sqlalchemy import text
            with self._engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT table_name, COUNT(*) as count FROM embeddings GROUP BY table_name"
                ))
                table_counts = {row.table_name: row.count for row in result}
                total = sum(table_counts.values())
                return {
                    "ready": True,
                    "model": self.embedding_model,
                    "dimensions": self.dimensions,
                    "index_type": "HNSW",
                    "total_embeddings": total,
                    "tables": table_counts
                }
        except Exception as e:
            logger.error(f"Error getting vector stats: {e}")
            return {"ready": False, "error": str(e)}

    # ── Clear Table Embeddings ────────────────────────────────────────

    def clear_table(self, table_name: str) -> int:
        """Clear all embeddings for a specific table. Returns count deleted."""
        if not self._ready or not self._engine:
            return 0
        try:
            from sqlalchemy import text
            with self._engine.connect() as conn:
                result = conn.execute(text(
                    "DELETE FROM embeddings WHERE table_name = :tn"
                ), {"tn": table_name})
                conn.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"Error clearing table {table_name}: {e}")
            return 0


def get_vector_service() -> VectorService:
    """Get the singleton VectorService"""
    return VectorService.get_instance()
