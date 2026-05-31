# CoTask — AI 赋能的大学生课程小组协作辅助平台

> 完整可部署的全栈实现。包含 Vue 3 前端 + Flask 后端 + MySQL/Redis/MinIO + Celery + Nginx，docker compose 一键拉起。

## 快速开始

### 生产模式

前端静态构建后由 Nginx 托管，适合体验完整功能或部署上线。

```bash
git clone <repo> cotask
cd cotask
cp .env.example .env             # 按需修改，至少填入 ANTHROPIC_API_KEY 或其它 LLM key
make up                          # 拉起所有服务（首次会构建镜像）
make migrate                     # 应用数据库迁移
make seed                        # （可选）写入演示数据
```

| 入口         | 地址                   |
| ------------ | ---------------------- |
| 前端         | http://localhost       |
| API          | http://localhost/api   |
| OpenAPI 文档 | http://localhost/docs  |
| MinIO 控制台 | http://localhost:9001  |

### 开发模式

前端以 Vite dev server 运行，修改 `.vue` / `.ts` 文件后浏览器**自动热更新**，无需重新构建镜像。

```bash
make dev                         # 拉起所有服务（首次会构建 dev 镜像）
make migrate                     # 首次需要执行一次迁移
make seed                        # （可选）写入演示数据
```

| 入口                | 地址                            | 说明                          |
| ------------------- | ------------------------------- | ----------------------------- |
| 前端（推荐）        | http://localhost:5173           | 直连 Vite dev server，HMR 最快 |
| 前端（Nginx 代理）  | http://localhost                | 经 Nginx 转发，HMR 同样有效   |
| API                 | http://localhost:5173/api       | 由 Vite 代理至 api 容器       |
| MinIO 控制台        | http://localhost:9001           |                               |

演示账号（执行 `make seed` 后可用）：
- 组长：`13800000001` / `password123`
- 组员：`13800000002` / `password123`

## 目录结构

```
.
├── docker-compose.yml      # 生产：7 个服务（nginx, web, api, worker, beat, mysql, redis, minio）
├── docker-compose.dev.yml  # 开发覆盖：web 改为 Vite dev server + source volume mount
├── nginx/
│   ├── nginx.conf          # 生产 Nginx 配置
│   └── nginx.dev.conf      # 开发 Nginx 配置（代理至 Vite，含 HMR WebSocket 支持）
├── backend/                # Flask + Celery
│   ├── app/
│   │   ├── modules/        # 业务模块（auth/users/groups/tree/tasks/...）
│   │   ├── models/         # SQLAlchemy 模型
│   │   ├── common/         # 错误/权限/事务/分页
│   │   └── tasks/          # Celery tasks
│   ├── migrations/         # Alembic
│   └── tests/
├── frontend/               # Vue 3 + Vite + TS + Pinia + Element Plus
│   ├── Dockerfile          # 生产镜像（多阶段：build → nginx:alpine）
│   ├── Dockerfile.dev      # 开发镜像（node:20-alpine，运行 npm run dev）
│   └── src/
│       ├── views/          # 页面
│       ├── components/     # 组件
│       ├── stores/         # Pinia
│       ├── api/            # 类型化 API 客户端
│       └── router/
├── scripts/                # seed、ops 工具
└── docs/

```

## 常用命令

```bash
make help       # 查看所有命令
make up         # 生产模式启动
make dev        # 开发模式启动（前端 HMR）
make down       # 停止所有服务
make migrate    # 应用数据库迁移
make seed       # 写入演示数据
make logs       # 跟随日志输出
make shell-api  # 进入 api 容器
make test       # 后端 pytest
```

## 测试

```bash
make test                    # 后端 pytest
cd frontend && npm run test  # 前端 vitest
```

## AI 配置

支持四家（`backend/app/modules/ai/client.py`）：
- Anthropic Claude
- OpenAI
- DeepSeek
- 阿里通义千问 (Dashscope)

`.env` 里设置 `AI_PROVIDER=anthropic`（或 `deepseek` 等）并填入对应 key。失败会按 `AI_PROVIDER_FALLBACK` 顺序降级。

## 生产部署提示

- 替换 `.env` 中所有 `change-me` 项。
- Nginx 加 TLS（推荐 acme.sh / cert-manager）。
- MySQL 启用主从、binlog 备份。
- MinIO 启用版本化与桶副本。
- 监控建议：Loki（日志）+ Prometheus（指标）+ Sentry（错误）。
