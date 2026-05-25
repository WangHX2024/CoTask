# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status

**Status**: Full v1.0 implementation in place — backend (Flask), frontend (Vue 3), DB schema, AI integration, Docker Compose, and Nginx. See `docs/开发方案.md` for the single source of truth on product/architecture.

## High-level architecture

7-service stack orchestrated by `docker-compose.yml`:

| Service     | Responsibility                                                  |
| ----------- | --------------------------------------------------------------- |
| `nginx`     | TLS termination, SPA static, `/api`, `/ws` routing              |
| `web`       | Vite-built Vue 3 SPA served by Nginx                            |
| `api`       | Flask + flask-smorest + gunicorn (REST + WebSocket via flask-sock) |
| `worker`    | Celery worker (AI jobs, file ops, async work)                   |
| `beat`      | Celery beat (DDL scanner, daily digest)                         |
| `mysql`     | Primary DB (utf8mb4, ngram FULLTEXT)                            |
| `redis`     | Cache + Celery broker + WS pub/sub                              |
| `minio`     | S3-compatible file storage                                      |

## Key design decisions

- **Project tree**: adjacency list (`parent_id`) + **materialized path** (`path`) + **closure table** (`task_closure`). Only leaves (`is_leaf=true`) carry `start_date`/`end_date`; non-leaf progress is aggregated from descendants via the closure table.
- **Group-scoped roles**: a user has a (leader/member) role per group via `group_members(group_id, user_id, role)`. The `@require_group_role` decorator (in `backend/app/common/permissions.py`) is the only auth gate for group-scoped endpoints.
- **AI**: provider-agnostic (`backend/app/modules/ai/client.py`) — Claude → OpenAI → DeepSeek → Dashscope fallback. All LLM calls run as Celery jobs (`backend/app/tasks/ai_tasks.py`). Output is strictly validated via Pydantic schemas (`backend/app/modules/ai/schemas.py`).
- **Inspiration plaza templates** are stored as **detached subtrees** in the same `tasks` table (`group_id=NULL`), referenced by `inspiration_posts.template_root_id`. Importing a template deep-copies into the target group.
- **WebSocket**: Redis pub/sub fanout. The gateway in `backend/app/modules/notifications/ws.py` subscribes a connection to `user:<uid>` + `group:<gid>` channels.
- **Auth**: JWT double-token. Access token (15min) in `Authorization` header. Refresh token (30d) as HttpOnly cookie at `/api/auth/refresh`.

## Frontend conventions

- TypeScript strict, all components use `<script setup lang="ts">` with **explicit imports** (no auto-import plugin).
- State: Pinia stores live in `frontend/src/stores/` (`auth`, `groups`, `tree`, `notifications`, `ui`).
- API client: `frontend/src/api/index.ts` — single typed `Api` object that every component imports.
- Theme: light/dark/auto via CSS variables in `frontend/src/styles/index.scss`. Use `var(--bg-card)` etc., never inline hex.
- WebSocket: `frontend/src/composables/useWS.ts` — singleton connection with auto-reconnect and event subscription via `.on(event, cb)`.
- Routing: `frontend/src/router/index.ts` — auth guard redirects to `/login` if no `accessToken`.

## Common dev commands

```bash
make up          # docker compose up -d --build
make migrate     # apply Alembic migrations
make seed        # demo data: 13800000001 / password123
make logs        # tail logs
make test        # backend pytest
make shell-api   # bash into api container
```

## When extending

- **New backend module**: add `backend/app/modules/<name>/{__init__.py,schemas.py,service.py,routes.py}`, then register the `blp` in `backend/app/__init__.py`.
- **New AI capability**: add prompt template `backend/app/modules/ai/prompts/<scope>.md`, Pydantic schema in `schemas.py`, runner function in `runner.py`, dispatch case in `backend/app/tasks/ai_tasks.py:run_ai_job`.
- **New page**: add `frontend/src/views/<Page>.vue` and a child route under the `/` shell route in `frontend/src/router/index.ts`. Use only explicit imports.

## Things to know

- The frontend does NOT use unplugin-auto-import — every component must explicitly `import { ref, computed, onMounted } from 'vue'`.
- Element Plus components are NOT auto-registered — explicit imports of `ElMessage`, `ElMessageBox` are required, but `<el-button>` etc. tags work via Element Plus's full registration in `main.ts`.
- Tree closure maintenance is done in `backend/app/modules/tree/service.py` — never write directly to `task_closure` from outside this module.
- All write services use the `tx()` context manager from `backend/app/common/tx.py`.

## Working language

Product copy and UI strings are Chinese. Code identifiers and comments are English.
