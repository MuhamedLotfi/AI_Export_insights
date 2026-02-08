# AI Export Insights

## 🚀 Overview

A modern **Multi-Domain AI Agent Platform** built with **Flutter Web** frontend and **FastAPI** backend. This system features a LangGraph-based multi-agent architecture that provides intelligent data insights with domain-aware access control.

![Flutter App](https://img.shields.io/badge/Frontend-Flutter-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green)
![LangGraph](https://img.shields.io/badge/AI-LangGraph-purple)

## ✨ Features

### 🔐 User Security
- JWT-based authentication
- Role-based access control (Admin, Manager, User)
- Secure token storage
- Protected routes with middleware

### 🤖 Multi-Domain AI Agents
- **Sales Analytics Agent** - Revenue trends, top products, customer insights
- **Inventory Management Agent** - Stock levels, reorder points, warehouse status
- **Purchasing Agent** - Vendor performance, lead times, procurement
- **Accounting Agent** - Profit margins, cost analysis, financial summaries

### ✨ Key Features
- 🔐 User Security - JWT authentication, role-based access, protected routes
- 📊 Dashboard - Real-time KPIs, interactive charts, quick actions
- 💬 AI Chat Tab - Natural language queries, chart generation, data tables
- 📝 Memory Tab - Conversation history, search, memory clearing
- ⚙️ Settings - Theme switching, AI config view, user profile
- 👥 User Management - Admin panel for agent assignments
- 🧠 LangGraph Agents - Thinking, Processing, Visualization, Coordinator
- 📁 JSON Data Adapter - Reads from JSON files (database adapter pattern preserved)

### 🧠 LangGraph Architecture
```
┌─────────────────────────────────────────────────────────────────────┐
│                     LangGraph Multi-Agent Pipeline                  │
├─────────────┬─────────────────┬──────────────┬────────────────────┤
│  THINKING   │   PROCESSING    │VISUALIZATION │   COORDINATOR      │
│   AGENT     │     AGENT       │    AGENT     │      AGENT         │
├─────────────┼─────────────────┼──────────────┼────────────────────┤
│ • Query     │ • SQL Execution │ • Chart Gen  │ • Answer Format    │
│   Analysis  │ • Calculator    │ • Data Viz   │ • Insights Extract │
│ • Domain ID │ • RAG Retrieval │ • Type Select│ • Recommendations  │
│ • Tool Pick │ • Data Access   │              │                    │
└─────────────┴─────────────────┴──────────────┴────────────────────┘
```

### 📊 Dashboard
- Real-time KPIs with trend indicators
- Interactive charts (Bar, Pie, Line)
- Quick action cards
- System status monitoring

### 💬 AI Chat Interface
- Natural language querying
- Thinking trace visibility
- Chart generation
- Data table previews
- Insight extraction

### 📝 Conversation Memory
- Full conversation history
- Search and filter
- Memory clearing
- Agent usage tracking

### ⚙️ Settings
- Theme switching (Light/Dark/System)
- AI configuration view
- User profile management

### 👥 User Management (Admin)
- User list with roles
- Domain agent assignment
- Real-time toggle updates

## 🏗️ Architecture

D:\AI\AI_Export_insights\
├── README.md                   # Comprehensive documentation
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
│
├── backend/                    # FastAPI Backend
│   ├── main.py                # Application entry point
│   ├── config.py              # Configuration (JSON file paths, domain agents)
│   ├── ai_agent/
│   │   ├── agents/
│   │   │   ├── thinking_agent.py      # Query analysis & tool selection
│   │   │   ├── processing_agent.py    # SQL/Calculator/RAG execution
│   │   │   ├── visualization_agent.py # Chart generation
│   │   │   └── coordinator_agent.py   # Response formatting
│   │   ├── ai_service.py             # Main AI orchestration
│   │   ├── auth_service.py           # JWT authentication
│   │   └── data_adapter.py           # JSON/Database adapter pattern
│   └── routers/
│       ├── auth.py                   # Login, Register, User management
│       ├── ai.py                     # Chat, Conversations, Memory
│       ├── dashboard.py              # KPIs, Charts, Activity
│       ├── settings.py               # User preferences
│       └── domain_agents.py          # Agent assignments
│
├── data/                       # JSON Data Files
│   ├── users.json              # User accounts (admin, manager, user)
│   ├── sales.json              # Sample sales data
│   ├── inventory.json          # Sample inventory data
│   ├── items.json              # Item catalog with pricing
│   ├── agents.json             # Domain agent registry
│   ├── user_agents.json        # User-agent assignments
│   ├── conversations.json      # Chat history (empty)
│   └── settings.json           # User settings (empty)
│
├── flutter_app/                # Flutter Web Frontend
│   ├── pubspec.yaml            # Dependencies
│   ├── lib/
│   │   ├── main.dart           # App entry point
│   │   ├── config/
│   │   │   └── api_config.dart # API endpoints
│   │   ├── core/theme/
│   │   │   └── app_theme.dart  # Modern dark/light theme
│   │   └── app/
│   │       ├── routes/         # Navigation (app_routes, app_pages)
│   │       ├── models/         # User, DomainAgent, ChatMessage
│   │       ├── services/       # AuthService
│   │       ├── controllers/    # ThemeController
│   │       ├── middlewares/    # AuthMiddleware
│   │       └── modules/
│   │           ├── auth/       # Login & Register views
│   │           ├── dashboard/  # Main dashboard with KPIs
│   │           ├── ai_assistant/ # Chat & Memory tabs
│   │           ├── settings/   # User preferences
│   │           └── user_management/ # Admin panel
│   └── web/
│       ├── index.html          # Web entry
│       └── manifest.json       # PWA manifest
│
└── docs/                       # Documentation folder

### Backend Structure
```
backend/
├── main.py                 # FastAPI application
├── config.py               # Configuration with JSON file paths
├── ai_agent/
│   ├── agents/
│   │   ├── thinking_agent.py
│   │   ├── processing_agent.py
│   │   ├── visualization_agent.py
│   │   └── coordinator_agent.py
│   ├── ai_service.py       # Main AI orchestration
│   ├── auth_service.py     # Authentication
│   └── data_adapter.py     # JSON/DB adapter
└── routers/
    ├── auth.py             # Auth endpoints
    ├── ai.py               # Chat endpoints
    ├── dashboard.py        # Dashboard endpoints
    ├── settings.py         # Settings endpoints
    └── domain_agents.py    # Agent management
```

### Flutter Structure
```
flutter_app/lib/
├── main.dart               # Entry point
├── config/
│   └── api_config.dart     # API endpoints
├── core/
│   └── theme/
│       └── app_theme.dart  # Theme configuration
├── app/
│   ├── routes/             # Navigation
│   ├── models/             # Data models
│   ├── services/           # Auth service
│   ├── controllers/        # Theme controller
│   ├── middlewares/        # Auth middleware
│   └── modules/
│       ├── auth/           # Login/Register
│       ├── dashboard/      # Main dashboard
│       ├── ai_assistant/   # Chat interface
│       ├── settings/       # User settings
│       └── user_management/# Admin panel
```

### Data Layer
```
data/
├── users.json              # User accounts
├── sales.json              # Sales data
├── inventory.json          # Inventory data
├── items.json              # Item catalog
├── agents.json             # Agent registry
├── user_agents.json        # User-agent assignments
├── conversations.json      # Chat history
└── settings.json           # User settings
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Flutter 3.10+
- Node.js (for web builds)

### Backend Setup

1. **Create Virtual Environment**
```bash
cd D:\AI\AI_Export_insights
python -m venv venv
venv\Scripts\activate
```

2. **Install Dependencies**
```bash
pip install fastapi uvicorn pydantic python-jose[cryptography] passlib[bcrypt]
```

3. **Run Backend**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Flutter Setup

1. **Install Dependencies**
```bash
cd flutter_app
flutter pub get
```

2. **Run Web (Development)**
```bash
flutter run -d chrome
```

3. **Build Web (Production)**
```bash
flutter build web
```

## 🔑 Default Credentials

| Username | Password     | Role    | Agents                         |
|----------|--------------|---------|--------------------------------|
| admin    | password123  | admin   | sales, inventory, purchasing, accounting |
| manager  | password123  | manager | sales, inventory               |
| user     | password123  | user    | sales                          |

## 📡 API Endpoints

### Authentication
| Method | Endpoint       | Description     |
|--------|----------------|-----------------|
| POST   | /auth/login    | User login      |
| POST   | /auth/register | User registration |
| GET    | /auth/me       | Current user    |
| GET    | /auth/users    | All users (admin) |

### AI Chat
| Method | Endpoint         | Description           |
|--------|------------------|-----------------------|
| POST   | /ai/chat         | Send chat query       |
| GET    | /ai/conversations| Conversation history  |
| GET    | /ai/state        | Agent state           |
| DELETE | /ai/memory       | Clear memory          |

### Dashboard
| Method | Endpoint    | Description      |
|--------|-------------|------------------|
| GET    | /dashboard  | Dashboard data   |
| GET    | /dashboard/kpis | KPIs only    |
| GET    | /dashboard/charts | Charts only |

### Domain Agents
| Method | Endpoint            | Description          |
|--------|---------------------|----------------------|
| GET    | /ai/agents          | All agents           |
| GET    | /ai/agents/my       | My agents            |
| POST   | /ai/agents/assign   | Assign agent         |
| DELETE | /ai/agents/revoke   | Revoke agent         |

### 🤖 Domain Agents
| Agent	|Description	|Tables
| sales	|Revenue trends, top products	sales, items
| inventory	|Stock levels, reorder points	inventory, items
| purchasing	|Vendor performance	purchasing, vendors
| accounting	|Profit margins, costs	items, costs

## 🎨 UI Features

### Modern Design
- Glassmorphism effects
- Gradient accents
- Smooth animations
- Responsive layout

### Dark Theme
- Primary: #6366F1 (Indigo)
- Secondary: #8B5CF6 (Purple)
- Background: #0F172A
- Surface: #1E293B
- Accent: #10B981 (Emerald)

## 🔧 Configuration

### Change API URL
Edit `flutter_app/lib/config/api_config.dart`:
```dart
static const String baseUrl = 'http://your-server:8000';
```

### Add New Domain Agent
1. Add to `data/agents.json`
2. Add to `backend/config.py` DOMAIN_AGENTS
3. Assign to users via admin panel

## 📦 Dependencies

### Backend
- FastAPI
- Uvicorn
- Pydantic
- python-jose
- passlib

### Flutter
- get (State Management)
- dio (HTTP Client)
- fl_chart (Charts)
- flutter_markdown (Markdown Rendering)
- google_fonts (Typography)
- shared_preferences (Storage)
- flutter_secure_storage (Secure Storage)

## 📄 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

---

Built with ❤️ by AI Export Insights Team
