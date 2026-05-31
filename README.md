<div align="center">

<img src="frontend/public/logo.svg" alt="CoTask Logo" width="200" />

### AI 赋能的大学生课程小组协作平台

用自然语言把想法变成可执行的项目计划。  
任务拆解、分工、进度跟踪、文件共享、组内讨论 — 一个空间就够了。

[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](docker-compose.yml)
[![Vue 3](https://img.shields.io/badge/Vue-3.x-4FC08D?logo=vuedotjs&logoColor=white)](frontend/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)](backend/)
[![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?logo=typescript&logoColor=white)](frontend/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](backend/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## 目录

- [为什么选择 CoTask？](#-为什么选择-cotask)
- [核心功能](#-核心功能)
- [快速开始](#-快速开始)
- [部署指南](#-部署指南)
- [AI 配置](#-ai-配置)
- [项目结构](#-项目结构)
- [许可证](#-许可证)

---

## 🤔 为什么选择 CoTask？

大学课程小组作业常常面临这些痛点：**任务归属不清晰**、沟通散落在微信 / QQ / 邮件各处、**排期靠 Excel 手动维护**，一旦 DDL 变动就得逐个通知。CoTask 提供一个**结构化且灵活**的协作空间来解决这些问题：

- **🗣️ 自然语言 → 项目计划**：用日常语言描述课程大作业（例如"我们做一个电商系统，包括前端、后端、数据库和测试"），AI 自动生成多级 WBS 任务树，并推荐匹配技能的负责人。
- **🔗 单一事实来源**：任务、文件、讨论、截止日期集中管理 — 不用再从聊天记录里翻找文档或 DDL。
- **📊 实时全局视野**：甘特图、成员负载热力图、72 小时 DDL 预警，无需反复追问就能掌握项目状态。
- **🔄 模板复用**：把成功的项目结构分享到灵感广场，其他小组一键导入即可复用。

CoTask 是一套**功能完整、可直接部署的全栈应用**，不是原型 Demo。提供 Docker Compose 一键启动、完整的 OpenAPI 文档，以及现代化的 Vue 3 前端界面。

---

## ✨ 核心功能

### 🤖 AI 助手
> *"用对话的方式搭建项目树，不用一个一个手动创建。"*

- **对话式 WBS 生成** — 用自然语言描述项目，AI 自动输出多级任务树，包含预估时间、技能标签和负责人推荐。
- **持续迭代优化** — 通过多轮对话调整项目树（"把测试阶段提前"、"在后端下面加一个代码审查任务"）。
- **多模型自动降级** — 支持 Anthropic Claude、OpenAI、DeepSeek、阿里通义千问（Dashscope），主模型不可用时自动切换备选。
- **每日 AI 建议** — 根据成员的工作负载和技能，推送个性化的任务建议到每个人的工作台。
- **异步处理** — AI 任务通过 Celery Worker 异步执行，实时进度通过 WebSocket 推送，不阻塞、不超时。

### 🏠 工作台
> *"你的个人指挥中心。"*

- **今日聚焦** — 按优先级排列的待办任务，包含截止时间和状态标识，支持快捷操作。
- **截止汇总** — 跨小组展示即将到期和已逾期的任务，可通过日历跳转到指定日期。
- **AI 智能建议** — 基于你的工作负载、技能和近期 DDL 生成上下文感知的任务建议。

### 🌳 项目树（WBS）
> *"把整个项目的层次结构可视化，一目了然。"*

- **多级任务拆解** — 支持任意深度的嵌套，拖拽调整排序。
- **节点状态** — 每个节点跟踪 `待办` / `进行中` / `待审核` / `已完成` 四种状态。
- **精细化权限** — 组长管理整棵树；子树管理员可独立管理指定分支。
- **任务分配** — 支持多人协同负责一个节点，匹配技能标签推荐人选。
- **依赖关系** — 支持任务间的前置 / 后继关系。

### 📅 时间轴（甘特图）
> *"纵览全局，把握节奏。"*

- **甘特图视图** — 支持周 / 月两级缩放，拖拽调整任务时间范围。
- **成员负载热力图** — 按人展示任务在时间轴上的分布，一眼看出谁任务过重。
- **DDL 预警** — 逾期任务红色高亮，72 小时内到期的任务橙色提醒。
- **今日线** — 垂直标记线，快速定位当前进度。

### 📁 文件库
> *"结构化存储，不是文件堆。"*

- **双视图模式** — 按文件夹层级浏览，或按关联任务查看。
- **预签名直传** — 文件从浏览器直接上传至 MinIO（S3 兼容），不经过服务器中转。
- **秒传去重** — 相同文件通过哈希检测，无需重复上传即可秒级"复制"。
- **上下文关联** — 文件关联到任务和讨论，信息不脱节。

### 💬 讨论区
> *"在做事的地方讨论事。"*

- **任务专属频道** — 每个任务节点自动创建专属讨论频道，讨论紧贴任务上下文。
- **主题频道** — 支持创建自由主题的讨论频道，用于跨任务的统筹交流。
- **@提醒** — 支持 @ 指定成员，通过 WebSocket 实时推送通知。
- **同屏协作** — 讨论区与项目树、时间轴并排显示，无需切换应用。

### ⭐ 灵感广场
> *"别再从零开始了。"*

- **模板分享** — 将本组的项目结构发布为可复用的模板。
- **一键导入** — 预览任意分享模板的内容，一键导入到本组的项目树。
- **社区互动** — 支持点赞、收藏、评论分享的模板。

### 🔔 通知中心
> *"实时感知，无需轮询。"*

- **WebSocket 实时推送** — 基于 Redis 发布订阅的扇出机制，即时送达。
- **事件全覆盖** — 任务分配、状态变更、@提醒、DDL 预警、AI 任务完成，均有通知。
- **未读角标** — 导航栏持久显示未读数量。

### 👥 小组管理
> *"有序协作的基础。"*

- **邀请码入组** — 成员通过可分享的邀请码加入小组（组长可重新生成）。
- **角色体系** — 组长（完全控制）和组员两种角色，权限边界清晰。
- **技能档案** — 每位成员维护个人技能标签，AI 据此进行任务分配推荐。
- **贡献统计** — 按成员统计任务完成情况。

---

## 🚀 快速开始

5 分钟内在本地跑起来。

### 前置要求

- **Docker** 20.10+ & **Docker Compose** v2
- **Git**
- 至少一个 **LLM API Key**（免费的 DeepSeek / OpenAI 额度即可测试）

### 步骤

```bash
# 1. 克隆仓库
git clone https://github.com/<your-org>/cotask.git
cd cotask

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env — 至少配置一个 AI 提供商的 Key（如 DEEPSEEK_API_KEY=sk-...）

# 3. 开发模式启动（Vite HMR + 源码挂载）
make dev

# 4. 执行数据库迁移
make migrate

# 5.（可选）导入演示数据
make seed
```

### 访问入口

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端**（推荐） | http://localhost:5173 | Vite 开发服务器，HMR 热更新 |
| **前端**（Nginx） | http://localhost | 模拟生产环境路由 |
| **API** | http://localhost:5173/api | Vite 代理至 API 容器 |
| **OpenAPI 文档** | http://localhost/docs | 交互式 Swagger UI |
| **MinIO 控制台** | http://localhost:9001 | 对象存储管理 |

### 演示账号

执行 `make seed` 后可用：

| 角色 | 手机号 | 密码 |
|------|--------|------|
| 组长 | `13800000001` | `password123` |
| 组员 | `13800000002` | `password123` |

### 常用命令

```bash
make help        # 查看所有可用命令
make logs        # 跟随查看容器日志
make test        # 运行后端测试
make down        # 停止所有服务
make clean       # 停止并删除所有数据卷 ⚠️
```

---

## 🚢 部署指南

### 生产环境启动

```bash
# 1. 克隆并配置
git clone https://github.com/<your-org>/cotask.git
cd cotask
cp .env.example .env

# 2. 编辑 .env，填写生产环境配置（见下表）
# 3. 启动
make up           # docker compose up -d --build
make migrate      # 应用数据库迁移
make seed         # 可选：导入演示数据
```

### 必填环境变量

| 变量 | 说明 |
|------|------|
| `FLASK_SECRET_KEY` | Flask 会话加密密钥 — **务必使用强随机值** |
| `JWT_SECRET_KEY` | JWT Token 签名密钥 — **务必使用强随机值** |
| `MYSQL_ROOT_PASSWORD` | MySQL root 密码 |
| `MYSQL_PASSWORD` | 应用数据库密码 |
| `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` | MinIO 管理员凭证 |
| `AI_PROVIDER` | 主 AI 提供商（`anthropic`、`openai`、`deepseek`、`dashscope`） |
| 至少一个 `*_API_KEY` | 对应提供商的 API Key |

> ⚠️ **部署前请替换所有 `change-me` 占位符及示例密码。**

### 生产环境入口

| 服务 | 地址 |
|------|------|
| 前端 | http://your-domain |
| API | http://your-domain/api |
| OpenAPI 文档 | http://your-domain/docs |
| MinIO 控制台 | http://your-domain:9001 |

### 运维命令

```bash
make ps            # 查看容器状态
make logs          # 跟踪日志
make restart       # 重启 api、worker、beat
make shell-api     # 进入 API 容器终端
make shell-db      # 进入 MySQL 命令行
```

---

## 🤖 AI 配置

CoTask 支持多种大模型提供商，配置自动降级。在 `.env` 中设置：

```env
# 主提供商
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-key-here

# 降级链路（主模型失败时按顺序尝试）
AI_PROVIDER_FALLBACK=openai,anthropic,dashscope

# 可选：自定义 Base URL（自部署或代理场景）
# OPENAI_BASE_URL=https://api.openai.com/v1
# DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
# ANTHROPIC_BASE_URL=https://api.anthropic.com
# DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

---

## 📂 项目结构

```
cotask/
├── docker-compose.yml          # 生产环境编排（8 个服务）
├── docker-compose.dev.yml      # 开发环境覆盖（Vite HMR + 源码挂载）
├── Makefile                    # 任务运行器（make help 查看全部）
├── .env.example                # 环境变量模板
├── nginx/                      # Nginx 配置（生产 / 开发）
│
├── backend/                    # Flask 后端应用
│   ├── Dockerfile
│   ├── app/
│   │   ├── modules/            # 业务模块（共 12 个）
│   │   │   ├── ai/             #   AI 助手（客户端、执行器、路由）
│   │   │   ├── auth/           #   认证模块（短信、JWT）
│   │   │   ├── dashboard/      #   个人工作台 & AI 建议
│   │   │   ├── discussion/     #   小组讨论频道
│   │   │   ├── files/          #   文件上传 & 文件夹管理
│   │   │   ├── groups/         #   小组增删改查
│   │   │   ├── inspiration/    #   灵感广场（模板分享）
│   │   │   ├── notifications/  #   通知中心
│   │   │   ├── tasks/          #   任务操作 & 分配
│   │   │   ├── timeline/       #   甘特图数据
│   │   │   ├── tree/           #   项目树（WBS）
│   │   │   └── users/          #   用户档案 & 技能
│   │   ├── common/             # 公共工具模块
│   │   ├── models/             # SQLAlchemy 数据模型（20+ 表）
│   │   └── tasks/              # Celery 任务（AI、DDL 扫描）
│   ├── migrations/             # Alembic 数据库迁移
│   └── tests/
│
├── frontend/                   # Vue 3 前端应用
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   └── src/
│       ├── views/              # 页面组件（14 个页面）
│       ├── components/         # 可复用组件
│       │   ├── ai/             #   AI 对话面板
│       │   ├── common/         #   通用 UI（Logo、主题切换等）
│       │   ├── inspiration/    #   模板导入/预览
│       │   ├── layout/         #   应用外壳、侧边栏
│       │   ├── onboarding/     #   新用户引导向导
│       │   ├── showcase/       #   登录页展示
│       │   ├── timeline/       #   甘特图组件
│       │   └── tree/           #   项目树画布、分支、任务抽屉
│       ├── stores/             # Pinia 状态管理（auth、groups、tree、notifications、UI）
│       ├── api/                # 类型化 API 客户端层
│       └── router/             # Vue Router 路由配置
│
└── docs/                       # 文档 & 截图

```

---


## 📄 许可证

本项目基于 MIT 许可证开源 — 详见 [LICENSE](LICENSE) 文件。

---

<div align="center">

**如果 CoTask 对你的团队有帮助，请给个 ⭐ Star！**

为更顺畅的小组协作而生 ❤️

</div>
