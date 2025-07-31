# syntax=docker/dockerfile:1.6

###############################################################################
# Stage 0 ─ base：建 venv + 安裝所有依賴
###############################################################################
FROM python:3.12.3-slim AS base
WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 建 venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# 系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl \
 && rm -rf /var/lib/apt/lists/*

# Heavy deps
COPY requirements_base.txt .
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install -r requirements_base.txt

# Light deps
COPY requirements_app.txt .
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install -r requirements_app.txt

###############################################################################
# Stage 1 ─ runtime：最終執行環境
###############################################################################
FROM python:3.12.3-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    PORT=8080 \
    PROJECT_ROOT=/app \
    PYTHONPATH=/app

# 複製 venv
COPY --from=base /opt/venv /opt/venv

# rarely changed (模型、靜態資源)
COPY models/ /app/models
COPY data/   /app/data

# frequently changed (程式碼)
COPY src/    /app/src

# 切換使用者（COPY 完再切）
RUN useradd -m app && chown -R app:app /app
USER app

EXPOSE 8080

# bash 以展開 $PORT；Cloud Run 改 port 時不用重建 image
CMD ["bash", "-c", "uvicorn src.web.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
