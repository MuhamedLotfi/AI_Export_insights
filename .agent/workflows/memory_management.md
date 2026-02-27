---
description: How memory management works in the AI agent system — rules for context building, token budgets, and database tables
---

# Memory Management Workflow

This workflow defines the patterns and rules for how conversation memory
is managed in the AI agent system. Follow these guidelines when adding
new agents, modifying context building, or working with conversation history.

## Core Principle

**All conversation context must flow through `MemoryManager`.**
Never access conversation tables directly for context building.
Never hard-code message limits or character truncation.

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────┐
│  MemoryManager              │
│  build_memory_context()     │
│  ┌────────────────────────┐ │
│  │ conversation_history   │ │ ← conversations table (token-budgeted)
│  │ session_summary        │ │ ← session_summaries table
│  │ cross_session_context  │ │ ← pgvector semantic search
│  │ user_preferences       │ │ ← user_preferences table
│  └────────────────────────┘ │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  LLM Service                │
│  Messages order:            │
│  1. System prompt           │
│  2. User preferences        │
│  3. Session summary         │
│  4. Cross-session context   │
│  5. Recent history          │
│  6. Current user message    │
└─────────────────────────────┘
```

## Rules for New Agents

When creating a new agent that needs conversation context:

1. **Import MemoryManager**, not vector_store:
   ```python
   from backend.ai_agent.memory_manager import get_memory_manager
   memory = get_memory_manager()
   ```

2. **Use `build_memory_context()`** for full memory package:
   ```python
   memory_ctx = memory.build_memory_context(query, session_id, user_id)
   history = memory_ctx["conversation_history"]
   summary = memory_ctx["session_summary"]
   cross_session = memory_ctx["cross_session_context"]
   prefs = memory_ctx["user_preferences"]
   ```

3. **Trigger memory updates** after storing conversation:
   ```python
   # After storing the conversation
   memory.trigger_memory_update(query, response_text, session_id, user_id)
   ```

## Rules for Token Budgets

- **Never exceed the configured token budgets** in `config.py` → `MEMORY_CONFIG`
- If you need more tokens for a specific agent, adjust the budget in config,
  don't bypass the system
- Total memory tokens should stay under 2500 to leave room for
  system prompt + response within the context window

## Rules for Context Building

- **System prompt first** — Always. This maximizes KV cache prefix reuse.
- **Stable content before dynamic** — Preferences before summary
  before history before current query.
- **Use TokenCounter for estimation** — `from backend.ai_agent.token_counter import estimate_tokens`
- **Truncate at sentence boundaries** — `from backend.ai_agent.token_counter import truncate_to_tokens`

## Configuration

All memory settings are in `config.py` under `MEMORY_CONFIG`. Key settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `history_token_budget` | 1500 | Max tokens for recent messages |
| `enable_summarization` | True | Enable rolling summarization |
| `summarize_every_n_turns` | 3 | Turns between summarizations |
| `enable_cross_session` | True | Enable cross-session retrieval |
| `enable_user_preferences` | True | Enable preference learning |
| `enable_feedback_learning` | True | Learn from user feedback |

## Database Tables

| Table | Database | Purpose |
|-------|----------|---------|
| `conversations` | ERP_AI | Existing — stores all messages |
| `feedback` | ERP_AI | Existing — stores user feedback |
| `session_summaries` | ERP_AI | Rolling conversation summaries |
| `user_preferences` | ERP_AI | Learned user preferences |

### Run Migration
// turbo
```bash
cd d:\AI\AI_Export_insights
python -m backend.migrations.002_create_memory_tables
```

## Debugging

All memory operations log with the `[MEMORY]` prefix:
```
[MEMORY] Session abc123...: 4 messages, 890/1500 tokens used
[MEMORY] Session abc123... needs summarization (3 new turns)
[MEMORY] Summarized session abc123...
[MEMORY] Found 2 cross-session matches (340 tokens)
[MEMORY] Loaded 3 preferences for user 42
```

Run with `LOG_LEVEL=DEBUG` for full memory diagnostics.
