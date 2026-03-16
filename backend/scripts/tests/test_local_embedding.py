"""
Script to verify local embedding generation using SentenceTransformer.
"""
import os
import sys
import logging
import time

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_embedding():
    logger.info("Testing local embedding generation...")
    
    try:
        from backend.config import VECTOR_CONFIG
        logger.info(f"Configuration: {VECTOR_CONFIG}")
        
        # Verify dependencies
        try:
            import sentence_transformers
            import torch
            logger.info(f"sentence-transformers: {sentence_transformers.__version__}")
            logger.info(f"torch: {torch.__version__}")
        except ImportError as e:
            logger.error(f"Dependency missing: {e}")
            logger.error("Please run: pip install -r backend/requirements.txt")
            return

        from backend.ai_agent.vector_service import get_vector_service
        
        start_time = time.time()
        vector_service = get_vector_service()
        
        if not vector_service._model_instance:
            logger.error("Model instance not loaded in VectorService!")
            return

        logger.info(f"Model loaded in {time.time() - start_time:.2f}s")
        
        test_text = "This is a test sentence to generate an embedding."
        embedding = vector_service._generate_embedding(test_text)
        
        if embedding:
            logger.info(f"✅ Embedding generated successfully! Length: {len(embedding)}")
            if len(embedding) == VECTOR_CONFIG["embedding_dimensions"]:
                 logger.info("✅ Dimensions match configuration.")
            else:
                 logger.warning(f"⚠️ Dimension mismatch: Got {len(embedding)}, Expected {VECTOR_CONFIG['embedding_dimensions']}")
        else:
            logger.error("❌ Failed to generate embedding.")

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_embedding()
