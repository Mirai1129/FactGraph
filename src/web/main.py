#  $ uvicorn src.web.main:app --reload
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import health, verifier, answerer
from .deps import get_settings

app = FastAPI(
    title="FactGraph API",
    version="0.1.0",
    docs_url="/",             # Swagger UI root
)

# ‒‒ CORS ‒‒
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ‒‒ Mount routers ‒‒
app.include_router(health.router,   prefix="/api")
app.include_router(verifier.router, prefix="/api")
app.include_router(answerer.router, prefix="/api")
