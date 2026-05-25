# CoTask — AI 赋能的大学生课程小组协作辅助平台

> 完整可部署的全栈实现。包含 Vue 3 前端 + Flask 后端 + MySQL/Redis/MinIO + Celery + Nginx，docker compose 一键拉起。

详细产品方案见 [`docs/开发方案.md`](docs/开发方案.md)。

## 快速开始

```bash
git clone <repo> cotask
cd cotask
cp .env.example .env             # 按需修改，至少填入 ANTHROPIC_API_KEY 或其它 LLM key
make up                          # 拉起所有服务（首次会构建镜像）
make migrate                     # 应用数据库迁移
make seed                        # （可选）写入演示数据
```

访问：

| 入口          | 地址                        |
| ------------- | --------------------------- |
| 前端          | http://localhost            |
| API           | http://localhost/api        |
| OpenAPI 文档  | http://localhost/docs       |
| MinIO 控制台  | http://localhost:9001       |

演示账号（执行 `make seed` 后可用）：
- 组长：`13800000001` / `password123`
- 组员：`13800000002` / `password123`

## 目录结构

```
.
├── docker-compose.yml      # 7 个服务：nginx, web, api, worker, beat, mysql, redis, minio
├── nginx/                  # 反向代理配置
├── backend/                # Flask + Celery
│   ├── app/
│   │   ├── modules/        # 业务模块（auth/users/groups/tree/tasks/...）
│   │   ├── models/         # SQLAlchemy 模型
│   │   ├── common/         # 错误/权限/事务/分页
│   │   └── tasks/          # Celery tasks
│   ├── migrations/         # Alembic
│   └── tests/
├── frontend/               # Vue 3 + Vite + TS + Pinia + Element Plus
│   └── src/
│       ├── views/          # 页面
│       ├── components/     # 组件
│       ├── stores/         # Pinia
│       ├── api/            # 自动生成的 OpenAPI 客户端 + 手写 fetch 包装
│       └── router/
├── scripts/                # seed、ops 工具
└── docs/开发方案.md        # 单一参考文档
```

## 常用命令

见 `make help`。

## 测试

```bash
make test                  # 后端 pytest
cd frontend && npm run test  # 前端 vitest
```

## AI 配置

支持四家（`backend/app/modules/ai/client.py`）：
- Anthropic Claude（推荐）
- OpenAI / 兼容 endpoint
- DeepSeek（OpenAI 兼容 API，`AI_PROVIDER=deepseek`）
- 阿里通义千问 (Dashscope)

`.env` 里设置 `AI_PROVIDER=anthropic`（或 `deepseek` 等）并填入对应 key。失败会按 `AI_PROVIDER_FALLBACK` 顺序降级。

## 生产部署提示

- 替换 `.env` 中所有 `change-me` 项。
- Nginx 加 TLS（推荐 acme.sh / cert-manager）。
- MySQL 启用主从、binlog 备份。
- MinIO 启用版本化与桶副本。
- 监控建议：Loki（日志）+ Prometheus（指标）+ Sentry（错误）。
