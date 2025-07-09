#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新聞事實驗證主流程 Pipeline

執行方式：
  - 全量：python -m src.qa.verifier.pipeline
  - 單篇：python -m src.qa.verifier.pipeline <news_id>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import gc
from pathlib import Path
from typing import List

import numpy as np
from tqdm import tqdm

from ..tools import data_utils as du
from ..tools import kg_nl as knl
from .core.paths import USER_INPUT_DIR, VEC_DIR, RES_DIR
from .core.config import LLM_ROUNDS
from .core.embeddings import embed_text, embed_triple
from .kg.search import cosine_search, kg_row_to_detail
from .llm.extract import extract_entities_relations
from .llm.judge import judge_news_kb
from .core.dedup import deduplicate


def _pull_triples(text: str) -> List[du.Triple]:
    """
    多輪 LLM 抽取三元組並去重合併。
    回傳合併後的三元組列表。
    """
    all_rounds: List[List[du.Triple]] = []
    last_error: Exception | None = None

    for i in range(LLM_ROUNDS):
        print(f'🔸 GPT 抽取 round {i+1}')
        start = time.time()
        raw = extract_entities_relations(text)
        elapsed = time.time() - start
        print(f'  ↳ 完成，用時 {elapsed:.1f}s')

        if not raw:
            print(f'[WARN] 抽取回傳為空，跳過 round {i+1}')
            continue

        try:
            triples = du.json_to_triples(json.loads(raw))
            all_rounds.append(triples)
        except Exception as e:
            last_error = e
            print(f'[WARN] JSON 解析失敗於 round {i+1}: {e}')

    if not all_rounds:
        if last_error:
            print(f'[ERROR] 所有輪次皆失敗: {last_error}', file=sys.stderr)
        return []

    return du.merge_triples(*all_rounds)


def _process_single(news_id: str, text: str) -> None:
    """
    處理單篇新聞：
      1. 嵌入全文
      2. LLM 抽取三元組
      3. 向量檢索 KG
      4. 去重與編號
      5. 輸出結果與事實判斷
    """
    RES_DIR.mkdir(parents=True, exist_ok=True)
    VEC_DIR.mkdir(parents=True, exist_ok=True)

    # 全文嵌入
    vec_path = VEC_DIR / f'{news_id}.npy'
    np.save(vec_path, embed_text(text))

    # 三元組抽取
    triples = _pull_triples(text)
    if not triples:
        sys.exit('❌ LLM 未抽取到任何三元組，流程終止')

    # KG 比對
    raw_lines: List[str] = []
    for tp in tqdm(triples, desc='🔍 KG 比對'):
        q_vec = embed_triple(tp)
        for idx in cosine_search(tp, q_vec):
            tri, det = kg_row_to_detail(idx)
            block = knl.build_block([tri], {tuple(tri.values()): det})
            raw_lines.extend(block.splitlines())

    if not raw_lines:
        sys.exit('⚠️ 無 KG 命中')

    # 去重與重編號
    kept = deduplicate(raw_lines)
    final = [re.sub(r'^\d+\.', f'[{i}]', ln, count=1) for i, ln in enumerate(kept, 1)]

    # 組合輸出
    news_block = f"```\n[原始新聞]\n{text}\n```"
    kb_block = '```\n[比對知識]\n' + '\n'.join(final) + '\n```'

    # 寫入檔案
    kg_file = RES_DIR / f'news_kg_{news_id}.txt'
    judge_file = RES_DIR / f'judge_result_{news_id}.txt'
    kg_file.write_text(f'{news_block}\n{kb_block}', encoding='utf-8')

    # 事實判斷
    judged = judge_news_kb(f'{news_block}\n{kb_block}')
    judge_file.write_text(judged, encoding='utf-8')

    print(f'✅ 輸出：{kg_file.name}, {judge_file.name}')


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser('FactGraph Verifier Pipeline')
    p.add_argument(
        'news_id',
        nargs='?',
        help='新聞檔名（不含 .txt），留空則批次所有'
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    if args.news_id:
        input_path = USER_INPUT_DIR / f'{args.news_id}.txt'
        if not input_path.is_file():
            sys.exit(f'❌ 找不到檔案：{input_path}')
        text = input_path.read_text(encoding='utf-8-sig').strip()
        _process_single(args.news_id, text)
    else:
        processed = {
            p.stem.removeprefix('news_kg_')
            for p in RES_DIR.glob('news_kg_*.txt')
        }
        for path in sorted(USER_INPUT_DIR.glob('*.txt')):
            nid = path.stem
            if nid in processed:
                continue
            text = path.read_text(encoding='utf-8-sig').strip()
            _process_single(nid, text)

    gc.collect()


if __name__ == '__main__':
    print(f'⚙️ USER_INPUT_DIR: {USER_INPUT_DIR.resolve()} (exists: {USER_INPUT_DIR.is_dir()})')
    print(f'⚙️ RES_DIR:        {RES_DIR.resolve()} (exists: {RES_DIR.is_dir()})')
    files = list(USER_INPUT_DIR.glob("*.txt"))
    print(f'🔍 找到 {len(files)} 個輸入檔案：{[p.name for p in files]}')

    main()
