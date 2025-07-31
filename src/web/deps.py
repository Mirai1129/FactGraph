"""
共用依賴：
- get_settings() 供路由透過 Depends 取得設定
- get_verifier() 取得 verifier service（懶載入）
"""
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    allowed_origins: list[str] = [
        "http://localhost:5173",  # Vite dev server
        "https://your-frontend.vercel.app",  # 正式前端
    ]
    tmp_dir: Path = Path("/tmp")


@lru_cache
def get_settings() -> Settings:  # FastAPI 會 cache Depends
    return Settings()


# ‒‒ example service (lazy import) ‒‒
def get_verifier():
    from qa.verifier.pipeline import _process_single  # 延後載入，避免啟動變慢
    return _process_single
