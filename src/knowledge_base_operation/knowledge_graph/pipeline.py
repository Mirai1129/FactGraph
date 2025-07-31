"""
Main Script for ETL Pipeline
...
"""

import argparse
import csv
import os

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

from extraction import extract_entities_relations
from neo4j_loader import Neo4jLoader
from src.common.gadget import _init_logger as LOGGER
from src.common.gadget import run_with_timer
from transformation import transform_to_neo4j_format


def load_ids_from_csv(path, id_column_index=1):
    r"""
    從 CSV 檔讀取 _id 值列表。
    預設 id 在第二欄 (index=1)，如果有 header，請自行調整 csv.reader 呼叫方式。
    轉換能轉成 ObjectId 的字串，否則保留原字串。
    如果要需要從 csv 讀取 _id，須執行 python main.py --id-csv <xxx.csv>
    """
    ids = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            raw = row[id_column_index]
            # 嘗試轉成 ObjectId
            try:
                ids.append(ObjectId(raw))
            except Exception:
                ids.append(raw)
    return ids


def main():
    # ─────────────────────────────
    # 0. 命令列參數
    # ─────────────────────────────
    parser = argparse.ArgumentParser(description="ETL for news → MongoDB → Neo4j")
    parser.add_argument(
        "--id-csv",
        help="CSV 檔路徑，若提供則只依此檔案中的 _id 查詢 MongoDB；不提供則全量擷取。",
        type=str,
        default=None,
    )
    args = parser.parse_args()

    # ─────────────────────────────
    # 1. 連線 MongoDB
    # ─────────────────────────────
    load_dotenv()
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client["News"]
    collection = db["Real_News"]

    # ─────────────────────────────
    # 2. 決定查詢模式
    # ─────────────────────────────
    if args.id_csv:
        LOGGER.info(f"🗂 以 CSV ({args.id_csv}) 中的 _id 進行查詢")
        ids = load_ids_from_csv(args.id_csv)
        docs_cursor = collection.find({"_id": {"$in": ids}})
    else:
        LOGGER.info("📦 未提供 CSV，執行全量擷取")
        docs_cursor = collection.find({})

    # ─────────────────────────────
    # 3. 初始化 Neo4j 連線
    # ─────────────────────────────
    neo4j_loader = Neo4jLoader()

    # ─────────────────────────────
    # 4. 逐筆處理擷取的文件
    # ─────────────────────────────
    for idx, doc in enumerate(docs_cursor, start=1):
        date = doc.get("date", "")
        title = doc.get("title", "")
        content = doc.get("content", "")
        doc_id = doc.get("_id", "")

        LOGGER.info(f"🔍 [處理第 {idx} 筆] doc_id: {doc_id}，日期: {date}")

        text = f"日期: {date}\n標題: {title}\n內容: {content}"
        # 抽取
        extraction_result = None
        attempt = 0
        MAX_RETRY = 5
        while extraction_result is None:
            attempt += 1
            try:
                extraction_result = extract_entities_relations(text)
                if extraction_result is None:
                    LOGGER.warning(f"⚠️ 第 {idx} 筆抽取失敗，第 {attempt} 次重試...")
            except Exception as e:
                from requests.exceptions import ConnectionError
                LOGGER.warning(f"⚠️ 第 {idx} 筆抽取例外（第 {attempt} 次）：{e}")
                if isinstance(e, ConnectionError) and attempt >= MAX_RETRY:
                    LOGGER.critical("❌ LLM 連線失敗超過次數，程式終止")
                    raise SystemExit

        # 轉換 & 寫入
        nodes, rels = transform_to_neo4j_format(extraction_result)
        for r in rels:
            r["doc_id"] = doc_id
            r["date"] = date
        neo4j_loader.insert_data(nodes, rels)
        LOGGER.info(f"✅ 第 {idx} 筆成功寫入 Neo4j")

    neo4j_loader.close()
    LOGGER.info("🌟 全部作業完成")


if __name__ == "__main__":
    run_with_timer(main)
