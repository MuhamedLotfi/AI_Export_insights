"""
Configuration for AI Export Insights Backend
"""
import os
from typing import Dict, Any

# API Settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# JWT Settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ai-export-insights-secret-key-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Data Source Configuration
# Options: "json", "database"
DATA_SOURCE = os.getenv("DATA_SOURCE", "json")

# JSON Data Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
JSON_FILES = {
    "users": os.path.join(DATA_DIR, "users.json"),
    # "sales": os.path.join(DATA_DIR, "sales.json"),
    # "inventory": os.path.join(DATA_DIR, "inventory.json"),
    # "items": os.path.join(DATA_DIR, "items.json"),
    "agents": os.path.join(DATA_DIR, "agents.json"),
    "user_agents": os.path.join(DATA_DIR, "user_agents.json"),
    "conversations": os.path.join(DATA_DIR, "conversations.json"),
    "settings": os.path.join(DATA_DIR, "settings.json"),
    # "pojectDataset.json": os.path.join(DATA_DIR, "pojectDataset.json"),
    "project_59": os.path.join(DATA_DIR, "project_59.json"),
}

# Database Configuration (for future use)
PG_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", "5432")),
    "database": os.getenv("PG_DATABASE", "ai_export_insights"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", "postgres"),
}

# AI Configuration
AI_CONFIG = {
    "model_provider": os.getenv("MODEL_PROVIDER", "ollama"),  # "ollama" or "openai"
    "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    "ollama_model": os.getenv("OLLAMA_MODEL", "gemma3:latest"),
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "openai_model": os.getenv("OPENAI_MODEL", "gpt-4"),
    "ollama_options": {
        "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "4096")),  # Reduced for speed
        "num_predict": int(os.getenv("OLLAMA_NUM_PREDICT", "512")),  # Limit output length
        "temperature": 0.7,
        "seed": 42,
    },
    # Translation settings (TranslateGemma for Arabic support)
    "translation_model": os.getenv("TRANSLATION_MODEL", "translategemma:4b"),
    "translation_enabled": os.getenv("TRANSLATION_ENABLED", "true").lower() == "true",
}

# LangGraph Configuration
LANGGRAPH_CONFIG = {
    "use_langgraph_agents": True,
    "enable_domain_routing": True,
    "enable_thinking_trace": True,
    "max_agent_iterations": 5,
    "enable_parallel_agents": False,
}

# Domain Agents Configuration
DOMAIN_AGENTS = {
    "sales": {
        "name": "Sales Analytics Agent",
        "description": "Analyzes sales data, revenue trends, and customer behavior",
        "icon": "trending_up",
        "tables": ["sales", "items", "project_59"],
        "keywords": ["sales", "revenue", "sold", "customer", "top items", "project", "contract", "opportunity"],
    },
    "inventory": {
        "name": "Inventory Management Agent",
        "description": "Monitors stock levels, reorder points, and warehouse operations",
        "icon": "inventory_2",
        "tables": ["inventory", "items"],
        "keywords": ["inventory", "stock", "warehouse", "reorder", "quantity"],
    },
    "purchasing": {
        "name": "Purchasing Agent",
        "description": "Manages vendor analysis, purchase orders, and procurement",
        "icon": "shopping_cart",
        "tables": ["purchasing", "vendors", "project_59"],
        "keywords": ["purchase", "vendor", "supplier", "lead time", "order"],
    },
    "accounting": {
        "name": "Accounting Agent",
        "description": "Handles financial analysis, costs, margins, and profitability",
        "icon": "account_balance",
        "tables": ["items", "costs", "project_59"],
        "keywords": ["cost", "margin", "profit", "pricing", "financial"],
    },
    "projects": {
        "name": "Project Analytics Agent",
        "description": "Tracks project performance, status, and profitability",
        "icon": "assignment",
        "tables": ["project_59", "sales", "purchasing"],
        "keywords": ["project", "status", "profitability", "completion", "contract"],
    },
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "app.log",
}
