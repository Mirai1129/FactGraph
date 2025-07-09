from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/ping", summary="存活探針")
async def ping() -> dict[str, str]:
    return {"status": "ok"}
