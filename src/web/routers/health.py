# src/web/routers/health.py
from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/ping", summary="存活探針")
async def ping() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/test")
async def test() -> dict[str, str]:
    """
    測試端點，返回一個簡單的消息。
    """
    answer = "This is a test endpoint."
    return {"message": answer}


@router.get("/ready", summary="就緒探針")
async def ready(request: Request) -> dict[str, bool]:
    """
    檢查模型是否已經預載完成。
    """
    loaded = getattr(request.app.state, "model_loaded", False)
    return {"model_loaded": loaded}
