# syntax=docker/dockerfile:1.6

###############################################################################
# Stage 0 ─ py-base：Python 3.12 + heavy deps (torch, transformers, …)
###############################################################################
FROM python:3.12.3-slim AS py-base
WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements_base.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements_base.txt

###############################################################################
# Stage 1 ─ deps：較常改動的輕量依賴
###############################################################################
FROM py-base AS deps
WORKDIR /opt/app

COPY requirements_app.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements_app.txt

###############################################################################
# Stage 2 ─ runtime：CUDA + 已裝好 Python 環境 + 你的程式碼
###############################################################################
FROM nvidia/cuda:12.6.2-cudnn-runtime-ubuntu22.04 AS runtime
WORKDIR /app

# 把整個 /usr/local (含 python3.12、site-packages、pip wheel 等) 搬進來
COPY --from=deps /usr/local /usr/local

# 如果你只想複製 site-packages / bin 也可以，但複製整個 /usr/local 最穩
# COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
# COPY --from=deps /usr/local/bin /usr/local/bin

# CUDA 環境變數
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH} \
    PATH=/usr/local/cuda/bin:${PATH} \
    PYTHONPATH=/app \
    PROJECT_ROOT=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 複製模型 / 資料（模型若常改，可搬到最後與 src 同層）
COPY models/ /app/models
COPY data/   /app/data
COPY src/    /app/src

# ── 把 Firebase 服務帳戶金鑰複製進容器 ──
COPY src/web/key /app/src/web/key

# 告訴 Firebase Admin SDK 去哪裡讀金鑰
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/src/web/key/factgraph-38be7-firebase-adminsdk-fbsvc-20b7fbb9a4.json

EXPOSE 8080
CMD ["uvicorn", "src.web.main:app", "--host", "0.0.0.0", "--port", "8080"]
