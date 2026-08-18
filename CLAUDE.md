# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HaikuBot is a Telegram bot (Ukrainian language) that collects chat messages in Supabase and generates haikus (5-7-5 syllable poems) after every N messages. It also responds to haiku comments, supports `/ask` chat analysis, and has a plugin system (currently: document translation).

## Commands

- Install dependencies: `python install_requirements.py` (installs root + plugin deps)
- Run: `python haikubot.py`
- Format: `black .`
- Lint: `flake8 haikubot.py`
- Type check: `mypy haikubot.py`
- Sync prod data to dev: `python sync_data.py --days 30 [--clear]`
- DB migrations: `supabase db push` (after `supabase link --project-ref [id]`)

## Architecture

```
haikubot.py                  Entry point: sets up Telegram handlers + loads plugins
├── handlers/
│   ├── message_handler.py   Stores every incoming message to Supabase
│   ├── haiku_handler.py     Generates haiku when message_count reaches config limit
│   ├── response_handler.py  Probabilistically replies to haiku comments using source messages
│   └── query_handler.py     /ask command: time-period chat analysis via OpenAI
├── utils/
│   ├── config.py            Loads config.json + .env into module-level constants
│   ├── openai_client.py     Single invoke_model() wrapper for OpenAI API
│   └── prompts.py           All LLM prompt templates
├── plugins/
│   ├── base.py              BasePlugin ABC with register(application) method
│   └── translator/          Document translation plugin (.docx, .xlsx)
└── db_service.py            All Supabase queries (users, messages, CRUD)
```

**Key data flow:** Messages arrive → `store_message()` increments per-chat counter → at `message_limit` (config.json), `process_haiku_answer()` fetches recent messages, calls OpenAI with `PROMPT_HAIKU`, sends haiku to chat, stores it with `haiku_source_ids` linking back to source messages → counter resets.

**Plugin system:** `plugin_loader.py` reads `config.json["plugins"]`, imports `plugins/{name}/plugin.py`, instantiates `{Name}Plugin(BasePlugin)`, and calls `register(app)` to attach Telegram handlers.

**State:** In-memory dicts `message_counts` and `last_bot_haikus` track per-chat counters and last haiku message IDs. No persistent state beyond Supabase.

## Configuration

- `config.json`: fallback values for `message_limit`, `answer_model`, `haiku_model`, `history_analysis_model`, `translation_model`, `bot`, and `plugins`.
- `.env`: `TELEGRAM_TOKEN`, `OPENAI_API_KEY`, `ANSWER_MODEL`, `OPENAI_HAIKU_MODEL`, `OPENAI_HISTORY_ANALYSIS_MODEL`, `OPENAI_TRANSLATION_MODEL`, `SUPABASE_URL`, `SUPABASE_KEY`, `DEBUG`, `RESPONSE_TRIGGER_PROBABILITY`, optional `TEST_CHAT_ID`/`TEST_CURRENT_TIME`. Environment model variables take priority over `config.json`.

## Code Style

- **Formatting**: Black with default settings
- **Imports**: stdlib → third-party → local, blank line between groups
- **Types**: Type hints on all function parameters and return values
- **Naming**: snake_case (vars/functions), UPPER_SNAKE_CASE (constants), PascalCase (classes)
- **Error handling**: try/except with specific exceptions
- **Docstrings**: Triple-quote docstrings on functions and classes
- **Logging**: `print()` with `IS_DEBUG` flag for dev; `logging` module for info/warning/error

## Database

Supabase PostgreSQL with two tables:
- `users`: user_id, username, first_name, last_name, isBot, created_at, last_activity
- `messages`: id (BIGSERIAL), chat_id, user_id (FK→users), text, tg_id, haiku_source_ids (JSON), created_at

Migrations live in `supabase/migrations/`.

## Deployment

Railway via `nixpacks.toml` + `Procfile` (`worker: python haikubot.py`).
