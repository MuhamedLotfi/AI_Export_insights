# AGENTS.md - AI Export Insights

This file provides guidelines for agentic coding agents working in this repository.

## Project Overview

A **Multi-Domain AI Agent Platform** built with:
- **Backend**: FastAPI (Python 3.10+) with LangGraph-based multi-agent architecture
- **Frontend**: Flutter Web (Dart) with GetX state management
- **Data**: JSON files (development) / PostgreSQL (production with pgvector)

## Build/Lint/Test Commands

### Backend (Python/FastAPI)

```bash
# Activate virtual environment
cd D:\AI\AI_Export_insights
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server (with auto-reload)
cd backend
uvicorn main:app --reload --port 8000

# Run tests (integration tests in backend/scripts/tests/)
python backend/scripts/tests/test_integration.py
python backend/scripts/tests/test_rag_search.py
python backend/scripts/tests/test_sql_agent.py

# Single test execution example
python -m pytest backend/scripts/tests/test_integration.py  # if pytest installed
python backend/scripts/tests/test_dynamic_discovery.py
```

### Frontend (Flutter/Dart)

```bash
cd flutter_app

# Install dependencies
flutter pub get

# Run development (Chrome)
flutter run -d chrome

# Build for production
flutter build web

# Run Flutter analyzer (linting)
flutter analyze

# Run tests
flutter test

# Run single test file
flutter test test/widget_test.dart
```

## Code Style Guidelines

### Python (Backend)

**Imports**:
- Use absolute imports: `from backend.routers import auth_router`
- Group imports: stdlib, third-party, local
- Add parent directory to path at file top: `sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))`

**Naming**:
- `snake_case` for functions, variables, module names
- `PascalCase` for classes and exceptions
- `UPPER_SNAKE_CASE` for constants

**Formatting**:
- Max line length: 100 characters (soft)
- Use 4 spaces for indentation
- Add docstrings for public functions/classes

**Types**:
- Use type hints: `def func(x: int) -> str:`
- Use Pydantic models for request/response validation
- Use Optional for nullable types: `Optional[str]`

**Error Handling**:
- Use FastAPI HTTPException for API errors
- Log errors with proper logging: `logger.error(f"Error: {e}")`
- Include traceback for debugging: `import traceback; traceback.print_exc()`

**API Structure**:
- Use FastAPI routers with prefixes: `app.include_router(router, prefix="/api")`
- Add tags for OpenAPI docs: `tags=["Category"]`
- Follow REST conventions: GET/POST/PUT/DELETE

### Dart/Flutter (Frontend)

**Imports**:
- Use package imports: `import 'package:get/get.dart'`
- Group: dart:*, package:*, relative

**Naming**:
- `camelCase` for variables, functions
- `PascalCase` for classes, enums, extensions
- `snake_case` for file names

**Formatting**:
- Uses analysis_options.yaml linter rules
- Prefer `const` constructors where possible
- Use single quotes for strings
- Prefer final fields

**Architecture** (GetX pattern):
- `lib/app/models/` - Data models with JSON serialization
- `lib/app/controllers/` - GetX controllers (business logic)
- `lib/app/services/` - API services (HTTP calls)
- `lib/app/modules/` - Feature modules (views, bindings, controllers)
- `lib/app/routes/` - Navigation/routes

**State Management**:
- Use GetX: `Get.put()`, `Get.lazyPut()`, `Get.find()`
- Controllers extend `GetxController` with `.obs` for reactive state

**Error Handling**:
- Use try-catch with proper error messages
- Use Get.snackbar or dialogs for user feedback

## Key Files and Locations

| Path | Description |
|------|-------------|
| `backend/main.py` | FastAPI app entry point |
| `backend/config.py` | Configuration (JSON paths, domain agents) |
| `backend/ai_agent/` | AI agents (thinking, processing, visualization, coordinator) |
| `backend/routers/` | API endpoints (auth, ai, dashboard, settings) |
| `flutter_app/lib/main.dart` | Flutter app entry point |
| `flutter_app/lib/config/api_config.dart` | API base URL configuration |
| `flutter_app/lib/app/modules/` | Feature modules (auth, dashboard, ai_assistant, settings) |
| `data/*.json` | JSON data files (users, sales, inventory, etc.) |

## Default Credentials

| Username | Password | Role |
|----------|-----------|------|
| admin | password123 | admin |
| manager | password123 | manager |
| user | password123 | user |

## Configuration

### Change Backend Port
Edit `backend/main.py` line 231: `uvicorn.run(app, host="0.0.0.0", port=8000)`

### Change Flutter API URL
Edit `flutter_app/lib/config/api_config.dart`: `static const String baseUrl = 'http://localhost:8000';`

### Add New Domain Agent
1. Add to `data/agents.json`
2. Add to `backend/config.py` DOMAIN_AGENTS dict
3. Assign to users via admin panel

## Development Notes

- Backend requires PostgreSQL with pgvector extension for vector search
- Use `python-jose` for JWT authentication
- Backend uses singleton pattern for services: `get_ai_service()`, `get_adapter()`
- Flutter uses GetX routing: `Get.toNamed()`, `Get.offNamed()`
- Dark theme primary: #6366F1 (Indigo), secondary: #8B5CF6 (Purple)