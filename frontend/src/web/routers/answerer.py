from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess

router = APIRouter(prefix="/answerer", tags=["answerer"])

@router.post("/query")
async def query_verifier(file: UploadFile = File(...), date: str = Form(...)):
    # 驗證日期格式 (yyyy/mm/dd)
    try:
        news_date = datetime.strptime(date, "%Y/%m/%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式錯誤，請使用 yyyy/mm/dd")

    # 讀取上傳的文案內容
    content_bytes = await file.read()
    try:
        text_content = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text_content = content_bytes.decode("utf-8", errors="ignore")

    # 合併日期與文案
    merged = f"事件詢問日期：{date}。{text_content}"

    # 設定專案根目錄與暫存路徑
    project_root = Path(__file__).resolve().parents[3]
    interim_dir = project_root / "data" / "interim" / "answerer" / "user-input"
    interim_dir.mkdir(parents=True, exist_ok=True)

    # 取得當前處理日期與時間 (亞洲/台北)
    now = datetime.now(ZoneInfo("Asia/Taipei"))
    current_date_str = now.strftime("%Y-%m-%d")
    current_time_str = now.strftime("%H%M")

    # 檔名由新聞日期、處理日期與處理時間組成 (格式: yyyy-mm-dd_yyyy-mm-dd_HHMM)
    filename_base = f"{news_date.strftime('%Y-%m-%d')}_{current_date_str}_{current_time_str}"
    input_path = interim_dir / f"{filename_base}.txt"
    input_path.write_text(merged, encoding="utf-8")

    # 呼叫處理 pipeline
    try:
        subprocess.run(
            ["python", "-m", "src.qa.answerer.pipeline", input_path.name],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Pipeline 執行錯誤：{e.stderr}")

    # 讀取處理後的結果檔案
    processed_dir = project_root / "data" / "processed" / "answerer"
    judge_matches = list(processed_dir.glob(f"user_qa_judge_{filename_base}.txt"))
    kg_matches = list(processed_dir.glob(f"user_kg_{filename_base}.txt"))
    if not judge_matches or not kg_matches:
        raise HTTPException(status_code=500, detail="找不到處理結果檔案")

    judge_path = judge_matches[0]
    kg_path = kg_matches[0]

    judge_result = judge_path.read_text(encoding="utf-8")
    user_news_kg = kg_path.read_text(encoding="utf-8")

    # 刪除暫存輸入檔
    input_path.unlink(missing_ok=True)

    # 回傳判斷結果與知識內容
    return {"user_judge_result": judge_result, "user_news_kg": user_news_kg}
