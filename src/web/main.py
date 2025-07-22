# src/web/main.py
#  $ uvicorn src.web.main:app --reload --host 0.0.0.0 --port 8080
from __future__ import annotations
from pathlib import Path
import uuid, time
from typing import Literal

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.testclient import TestClient

from .routers import health, verifier, answerer
from .deps import get_settings
from .init_model import load_ckip_model

import firebase_admin
from firebase_admin import credentials, firestore

# ── 確保本地目錄存在，避免檔案操作錯誤 ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent                     # …/FactGraph/src/web
# 應該往上兩層才是專案根目錄 …/home/karca5103/dev/FactGraph
PROJECT_ROOT = BASE_DIR.parent.parent
for mode in ("verifier", "answerer"):
    (PROJECT_ROOT / "data" / "interim" / mode / "user-input").mkdir(parents=True, exist_ok=True)

# ── Firebase Key 路徑 & CORS 設定 ─────────────────────────────────────────────────
KEY_PATH = BASE_DIR / "key" / "factgraph-38be7-firebase-adminsdk-fbsvc-20b7fbb9a4.json"
origins = [
    "https://factgraph-38be7.web.app",
    "http://localhost:8080",
    "http://localhost:5173",
]

# ── FastAPI App 初始化 ─────────────────────────────────────────────────────────
app = FastAPI(title="FactGraph API", version="0.1.0", docs_url="/")
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router,   prefix="/api")
app.include_router(verifier.router, prefix="/api")
app.include_router(answerer.router, prefix="/api")

# ── Firebase Admin SDK 初始化 (Admin SDK 不受安全規則限制) ─────────────────────────────
cred = credentials.Certificate(str(KEY_PATH))
firebase_admin.initialize_app(cred)
db = firestore.client()

# 用於內部同步呼叫
sync_client = TestClient(app)

# ── Pydantic 定義 ────────────────────────────────────────────────────────────
class JobCreate(BaseModel):
    url: str
    mode: Literal["writing", "question"]
    date: str  # YYYY/MM/DD

class JobOut(BaseModel):
    id: str
    status: str

# ── 背景任務：呼叫同步 endpoint，並將答案與知識寫入 Firestore ─────────────────────────
def process_task(job_id: str, url: str, mode: str, date: str):
    doc_ref = db.collection("url-results").document(job_id)
    doc_ref.update({"status": "RUNNING"})
    try:
        # 診斷日志
        print(f"[process_task] job_id={job_id}, mode={mode}, date={date}")
        files = {"file": ("user.txt", url, "text/plain")}
        data = {"date": date}
        if mode == "writing":
            resp = sync_client.post("/api/verifier/query", files=files, data=data)
            print(f"[verifier] status={resp.status_code}, body={resp.json()}")
            body = resp.json()
            wa, wk = body.get("judge_result", ""), body.get("news_kg", "")
            update_fields = {"writingAnswer": wa, "writingKnowledge": wk}
        else:
            resp = sync_client.post("/api/answerer/query", files=files, data=data)
            print(f"[answerer] status={resp.status_code}, body={resp.json()}")
            body = resp.json()
            qa = body.get("user_judge_result") or body.get("result") or ""
            qk = body.get("user_news_kg")    or body.get("news_kg")   or ""
            update_fields = {"questionAnswer": qa, "questionKnowledge": qk}
        # 清空另一模式欄位
        if mode == "writing":
            update_fields.update(questionAnswer=None, questionKnowledge=None)
        else:
            update_fields.update(writingAnswer=None, writingKnowledge=None)
        # 他日誌輸出
        print(f"[Firestore] updating fields for {job_id}: {update_fields}")
        doc_ref.update(update_fields)
        doc_ref.update({"status": "DONE"})
        print(f"[process_task] DONE job_id={job_id}")
    except Exception as e:
        print(f"[process_task] EXCEPTION job_id={job_id}: {e}")
        doc_ref.update({"status": "FAILED"})

# ── 建立任務 Endpoint：POST /api/tasks ───────────────────────────────────────────
@app.post("/api/tasks", response_model=JobOut)
def create_task(payload: JobCreate, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    db.collection("url-results").document(job_id).set({
        "status":        "PENDING",
        "url":           payload.url,
        "mode":          payload.mode,
        "date":          payload.date,
        "writingAnswer":    None,
        "writingKnowledge": None,
        "questionAnswer":    None,
        "questionKnowledge": None,
        "created_at":     firestore.SERVER_TIMESTAMP,
    })
    background_tasks.add_task(process_task, job_id, payload.url, payload.mode, payload.date)
    return JobOut(id=job_id, status="PENDING")

# ── 查詢任務狀態 Endpoint：GET /api/tasks/{job_id} ───────────────────────────────────
@app.get("/api/tasks/{job_id}", response_model=JobOut)
def get_task(job_id: str):
    doc = db.collection("url-results").document(job_id).get()
    if not doc.exists:
        raise HTTPException(404, "Job not found")
    data = doc.to_dict()
    return JobOut(id=job_id, status=data.get("status"))

# ── 啟動時 Pre-load CKIP 模型 ───────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    print("📦 預載 CKIP 模型…")
    ckip_model = load_ckip_model()
    app.state.ckip_model = ckip_model
    app.state.model_loaded = True
    print("📦 模型載入完成。")
