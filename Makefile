.PHONY: install install-backend install-frontend lint format test test-backend test-frontend typecheck build build-frontend build-docker clean

# 后端通过 uv 管理，前端通过 npm 管理
install: install-backend install-frontend

install-backend:
	uv sync

install-frontend:
	cd frontend && npm install

# 静态检查：后端 ruff + basedpyright + 前端 tsc
lint: lint-backend lint-frontend

lint-backend:
	uv run ruff check .
	uv run ruff format --check .
	uv run basedpyright

lint-frontend: typecheck

format:
	uv run ruff format .

# 测试：后端 pytest + 前端类型检查
test: test-backend test-frontend

test-backend:
	uv run pytest -q

test-frontend: typecheck

typecheck:
	cd frontend && npm run typecheck

# 构建：前端静态资源 + Docker 镜像
build: build-frontend build-docker

build-frontend:
	cd frontend && npm run build

build-docker:
	docker build -t add-work .

clean:
	rm -rf frontend/build .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
