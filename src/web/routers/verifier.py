from __future__ import annotations
import asyncio
import uuid
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from ..schemas.news import NewsIn, NewsOut
from ..deps import get_settings, get_verifier

router = APIRouter(tags=["verifier"])

# —— 極簡 in-memory 任務表 —— #
_TASKS: dict[str, str] = {}      # task_id -> status

@router.post("/verify", response_model=NewsOut, summary="提交新聞驗證")
async def verify(
    payload: NewsIn,
    bg: BackgroundTasks,
    settings = Depends(get_settings),
    verifier = Depends(get_verifier),
) -> NewsOut:
    task_id = uuid.uuid4().hex[:8]
    _TASKS[task_id] = "processing"

    # 背景執行長流程
    async def _run():
        try:
            await asyncio.to_thread(verifier, task_id, payload.text)
            _TASKS[task_id] = "done"
        except Exception as e:          # 真實場景請記 log
            _TASKS[task_id] = "error"
            print("Verifier error →", e)

    bg.add_task(_run)
    return NewsOut(task_id=task_id, status="processing")


@router.get("/verify/{task_id}", response_model=NewsOut, summary="查詢任務狀態")
async def verify_status(task_id: str) -> NewsOut:
    if task_id not in _TASKS:
        raise HTTPException(404, detail="task_id not found")
    return NewsOut(task_id=task_id, status=_TASKS[task_id])
