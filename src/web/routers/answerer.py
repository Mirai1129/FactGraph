"""
示範：呼叫 qa.answerer 管線（您可依實際需返回的結構調整）
"""
from __future__ import annotations
from uuid import uuid4
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["answerer"])

class QIn(BaseModel):
    question: str = Field(..., min_length=3, description="使用者提問")

class QOut(BaseModel):
    answer: str

@router.post("/answer", response_model=QOut, summary="問答 API")
async def answer_api(q: QIn) -> QOut:
    # ⬇︎ 只示範對接，請依自己 answerer pipeline 補上真實邏輯
    from qa.answerer.pipeline import main as answerer_main  # 假設已有可呼叫函式
    # 這裡用簡易回覆占位
    return QOut(answer=f"（模擬回答）你問：{q.question}，id={uuid4().hex[:6]}")
