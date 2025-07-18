#  $ uvicorn src.web.main:app --reload
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import health, verifier, answerer
from .deps import get_settings

from .init_model import load_ckip_model
print("📦 準備載入 CKIP 模型（不進行推論）...")
ckip_model = load_ckip_model()  # ✅ 僅載入模型
print("📦 模型準備完畢。")

app = FastAPI(
    title="FactGraph API",
    version="0.1.0",
    docs_url="/",             # Swagger UI root
)

# ‒‒ CORS origins ‒‒
# 這裡設定允許的 CORS origins，通常是前端應用程的 URL。
# 如果使用 Vue CLI 或 Vite 開發前端，這些預設的 URL 會是 localhost:8080 或 localhost:5173。
# 可以根據實際情況修改這些 URL。
# 如果有多個前端應用，請將它們的 URL 加入這個列表。
# 注意：在生產環境中，請確保只允許可信的來源，以避免安全問題。
origins = [
    "http://localhost:8080",  # Vue CLI 預設
    "http://localhost:5173",  # Vite 預設
]


# ‒‒ CORS ‒‒
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ‒‒ Mount routers ‒‒
app.include_router(health.router,   prefix="/api")
app.include_router(verifier.router, prefix="/api")
app.include_router(answerer.router, prefix="/api")
