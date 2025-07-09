"""
answerer ─ 問答主流程（Orchestrator）

職責只做「流程協調」，不處理繁雜業務邏輯：
0. python -m src.qa.answerer.pipeline
1. 讀取使用者問題（檔案或 stdin）並取得 slug
2. 呼叫 GPT 抽取三元組
3. 以向量搜尋 KG 相關敘述
4. 去重（相似僅保留最長條目）
5. 呼叫 GPT 評估最終結果
6. 依輸入檔名動態輸出 user_kg_*.txt 與 user_qa_judge_*.txt
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Dict

# ──────────────────────── 本專案自製模組 ────────────────────────
from .core.paths import (
    CKIP_ROOT,
    KG_EMB_PATH,
    KG_CSV_PATH,
    OUT_DIR,
    USER_INPUT_DIR,
    EXTRACT_PROMPT_PATH,
    JUDGE_PROMPT_PATH,
)
from .core.embedding import load_embedder, embed_triple, embed_text, dedupe
from .core.utils import read_question, safe_json_loads, clean_json_block
from .kg.loader import load_kg_vectors, load_kg_df
from .kg.search import search_by_triples
from .llm.gpt import GPTClient
from .llm.prompt_loader import load_prompt

# 需用到 qa.tools 生成敘述區塊
from ..tools import kg_nl as knl
from ..tools import data_utils as du

# ───────────────────────────── 參數設定 ─────────────────────────
SIM_TH: float = 0.80          # KG 相似度門檻
TOP_K: int = 100              # 每個三元組取前 TOP_K 條

# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def main() -> None:
    """整個問答管線的入口函式。"""

    # ========== 1. 資源初始化 ==========
    # 1-1 句向量模型
    emb = load_embedder(CKIP_ROOT)

    # 1-2 KG 向量與 DataFrame
    kg_vecs, kg_vecs_norm = load_kg_vectors(KG_EMB_PATH)
    kg_df, hp_col, rp_col, tp_col = load_kg_df(KG_CSV_PATH)

    # 1-3 Prompt 與 GPT client
    extract_prompt: str = load_prompt(EXTRACT_PROMPT_PATH)
    judge_prompt: str = load_prompt(JUDGE_PROMPT_PATH)

    gpt = GPTClient(
        api_key=os.getenv("GPT_API"),
        model_id=os.getenv("GPT_MODEL", "gpt-4o"),
        temperature=0.4,
        top_p=0.9,
        max_tokens=2048,
    )

    # ========== 2. 讀取使用者問題 ==========
    question, slug = read_question(USER_INPUT_DIR)
    print(f"🔸 Question: {question}")

    # ========== 3. 呼叫 GPT 抽取三元組 ==========
    raw_resp: str = gpt.chat(extract_prompt, question)
    print("🪵 GPT raw response:\n", raw_resp)

    # 清理 fence → JSON 解析
    cleaned = clean_json_block(raw_resp)
    data = safe_json_loads(cleaned)

    # 兼容兩種 schema
    if isinstance(data, dict) and "triples" in data:
        triples: List[Dict[str, str]] = [
            {
                "head": t.get("subject"),
                "relation": t.get("relation"),
                "tail": t.get("object"),
            }
            for t in data["triples"]
            if t.get("subject") and t.get("relation")
        ]
    else:
        triples = du.json_to_triples(data) or []

    print(f"🪲 Parsed triples count: {len(triples)}")
    if not triples:
        sys.exit("❌ GPT 未抽取到三元組")

    # ========== 4. KG 向量檢索 ==========
    raw_lines = search_by_triples(
        triples,
        embed_fn=lambda tp: embed_triple(emb, tp),
        kg_vecs_norm=kg_vecs_norm,
        top_k=TOP_K,
        sim_th=SIM_TH,
        kg_df=kg_df,
        hp_col=hp_col,
        rp_col=rp_col,
        tp_col=tp_col,
        build_block_fn=knl.build_block,
    )
    if not raw_lines:
        sys.exit("⚠️  KG 無任何匹配")

    # ========== 5. 語意去重（相似保留最長）==========
    final_lines = dedupe(
        raw_lines,
        embed_fn=lambda ln: embed_text(emb, ln),
        threshold=0.80,
    )

    # ========== 6. 依 slug 動態輸出 ==========
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    kg_out: Path = OUT_DIR / f"user_kg_{slug}.txt"
    judge_out: Path = OUT_DIR / f"user_qa_judge_{slug}.txt"

    kg_out.write_text(
        "```\n[使用者提問]\n"
        f"{question}\n```\n"
        "```\n[知識查詢結果]\n"
        + "\n".join(final_lines)
        + "\n```",
        encoding="utf-8",
    )

    # ========== 7. GPT 最終判斷 ==========
    judge_result = gpt.chat(judge_prompt, kg_out.read_text(encoding="utf-8"))
    judge_out.write_text(judge_result, encoding="utf-8")

    print("✅ finished; outputs saved under", OUT_DIR)
    print("   KG    →", kg_out.name)
    print("   JUDGE →", judge_out.name)


# ---------------------------------------------------------------------------
# CLI 執行
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
