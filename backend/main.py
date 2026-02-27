"""
Main FastAPI Application
AI Export Insights - Multi-Domain AI Agent Platform
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import sys
import codecs

# FORCE UTF-8 ENCODING FOR WINDOWS CONSOLE
if sys.platform == "win32":
    try:
        # Try reconfigure first (Python 3.7+)
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback for wrapped streams or older Python
        try:
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
        except Exception:
            pass

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import LOGGING_CONFIG

# Force reload for config update

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    handlers=[
        logging.FileHandler(LOGGING_CONFIG['file'], encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Export Insights API",
    description="Multi-Domain AI Agent Platform with LangGraph Orchestration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from backend.routers import (
    auth_router,
    ai_router,
    dashboard_router,
    settings_router,
    domain_agents_router,
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(ai_router, prefix="/ai", tags=["AI Agent"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(settings_router, prefix="/settings", tags=["Settings"])
app.include_router(domain_agents_router, prefix="/ai/agents", tags=["Domain Agents"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("=" * 60)
    logger.info("Starting AI Export Insights Backend...")
    logger.info("=" * 60)
    
    try:
        # Initialize data adapter
        from backend.ai_agent.data_adapter import get_adapter
        adapter = get_adapter()
        schema = adapter.get_schema()
        # logger.info(f"Data adapter initialized with {len(schema)} tables") - already logged by data_adapter
        
        # Initialize AI services (singleton — preload for fast first query)
        from backend.ai_agent.ai_service import get_ai_service
        ai_service = get_ai_service()
        logger.info("AI Service initialized")
        
        # Preload VectorService (loads embedding model once at startup)
        try:
            from backend.ai_agent.vector_service import get_vector_service
            vs = get_vector_service()
            logger.info(f"VectorService preloaded (ready={vs._ready})")
        except Exception as e:
            logger.warning(f"VectorService preload skipped: {e}")
        
        # Preload LLMService (singleton)
        try:
            from backend.ai_agent.llm_service import get_llm_service
            get_llm_service()
            logger.info("LLMService preloaded")
        except Exception as e:
            logger.warning(f"LLMService preload skipped: {e}")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("=" * 60)
    logger.info("Backend ready!")
    logger.info("=" * 60)


@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "AI Export Insights API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/status")
def get_status():
    """Get system status"""
    from backend.ai_agent.data_adapter import get_adapter
    
    try:
        adapter = get_adapter()
        schema = adapter.get_schema()
        data_status = "connected"
        tables = list(schema.keys())
        record_counts = {table: len(adapter.get_all(table)) for table in tables}
    except Exception as e:
        data_status = f"error: {str(e)}"
        tables = []
        record_counts = {}
    
    return {
        "api": "running",
        "data_source": data_status,
        "tables": tables,
        "record_counts": record_counts
    }


# ── RAG Search Test Endpoints ─────────────────────────────────────────

@app.get("/api/rag/search", tags=["RAG Search (Test)"])
def rag_search_test(query: str, top_k: int = 10, table_filter: str = None):
    """
    Test endpoint: Compare old (pure vector) vs new (hybrid RAG) search results.
    Use this for side-by-side quality comparison before switching to the new engine.
    """
    try:
        from backend.ai_agent.vector_service import get_vector_service
        from backend.ai_agent.rag_search_service import get_rag_search_service

        vector_svc = get_vector_service()
        rag_svc = get_rag_search_service()

        # Old: pure vector search
        old_results = vector_svc.semantic_search(query, top_k=top_k, table_filter=table_filter)
        old_formatted = []
        for r in old_results:
            tn = r.get("table_name", "")
            if tn == "__schema_metadata__":
                continue
            old_formatted.append({
                "table": tn,
                "row_id": r.get("row_id", ""),
                "similarity": round(float(r.get("similarity", 0)), 4),
                "content": r.get("content_text", "")[:200],
            })

        # New: hybrid RAG search
        new_results = rag_svc.search(query, top_k=top_k, table_filter=table_filter)
        new_formatted = [r.to_dict() for r in new_results]
        # Truncate content for response
        for r in new_formatted:
            r["content"] = r["content"][:200]

        return {
            "query": query,
            "old_search": {
                "method": "pure_vector",
                "result_count": len(old_formatted),
                "results": old_formatted,
            },
            "new_search": {
                "method": "hybrid_rag",
                "weights": {"vector": rag_svc.w_vector, "keyword": rag_svc.w_keyword, "table": rag_svc.w_table},
                "result_count": len(new_formatted),
                "results": new_formatted,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rag/stats", tags=["RAG Search (Test)"])
def rag_stats():
    """Get vector database statistics."""
    try:
        from backend.ai_agent.vector_service import get_vector_service
        return get_vector_service().get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
