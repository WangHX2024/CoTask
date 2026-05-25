.PHONY: help up down build logs ps restart migrate seed shell-api shell-db test fmt lint clean

help:
	@echo "CoTask 开发命令"
	@echo "  make up        启动全部服务"
	@echo "  make down      停止全部服务"
	@echo "  make build     重新构建镜像"
	@echo "  make migrate   执行数据库迁移"
	@echo "  make seed      写入演示数据"
	@echo "  make logs      跟随日志"
	@echo "  make shell-api 进入 api 容器"
	@echo "  make shell-db  进入 mysql 容器"
	@echo "  make test      跑后端测试"
	@echo "  make fmt       格式化代码"
	@echo "  make clean     清理容器/卷"

up:
	@[ -f .env ] || cp .env.example .env
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

restart:
	docker compose restart api worker beat

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

migrate:
	docker compose exec api flask db upgrade

seed:
	docker compose exec api python -m scripts.seed

shell-api:
	docker compose exec api bash

shell-db:
	docker compose exec mysql mysql -u$$MYSQL_USER -p$$MYSQL_PASSWORD $$MYSQL_DATABASE

test:
	docker compose exec api pytest -v

fmt:
	docker compose exec api ruff format .
	cd frontend && npm run format

lint:
	docker compose exec api ruff check .
	cd frontend && npm run lint

clean:
	docker compose down -v
	rm -rf backend/__pycache__ frontend/node_modules frontend/dist
