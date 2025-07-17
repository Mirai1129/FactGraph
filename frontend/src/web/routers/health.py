from fastapi import APIRouter

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