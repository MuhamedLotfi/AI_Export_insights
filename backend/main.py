"""
Main FastAPI Application
AI Export Insights - Multi-Domain AI Agent Platform
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import LOGGING_CONFIG

# Force reload for config update

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    handlers=[
        logging.FileHandler(LOGGING_CONFIG['file']),
        logging.StreamHandler()
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
        logger.info(f"Data adapter initialized with tables: {list(schema.keys())}")
        
        # Initialize AI services
        from backend.ai_agent.ai_service import AIService
        ai_service = AIService()
        logger.info("AI Service initialized")
        
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


# Run application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
