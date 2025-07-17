#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KG 檢索模組

功能：
  給定三元組列表，對預先載入並正規化的知識圖譜向量進行相似度檢索，
  回傳符合門檻的敘述區塊列表。

主要函式：
  - search_by_triples
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import (
    List, Dict, Any,
    Callable, Optional
)

import numpy as np
import pandas as pd


def search_by_triples(
    triples: List[Dict[str, str]],
    embed_fn: Callable[[Dict[str, str]], np.ndarray],
    kg_vecs_norm: np.ndarray,
    kg_df: pd.DataFrame,
    build_block_fn: Callable[..., str],
    top_k: int = 100,
    sim_th: float = 0.8,
    hp_col: Optional[str] = None,
    rp_col: Optional[str] = None,
    tp_col: Optional[str] = None
) -> List[str]:
    """
    依據輸入的三元組列表進行向量相似度檢索，
    回傳組合後的敘述區塊清單（逐行文字）。

    Args:
        triples: GPT 抽取出的三元組 dict 列表，格式包含 'head','relation','tail'.
        embed_fn: 對單一三元組執行嵌入並回傳向量的函式。
        kg_vecs_norm: 已正規化的 KG 向量矩陣，每列對應 kg_df 同一索引。
        kg_df: 包含至少 'head','relation','tail' 欄位，以及可選屬性 json 欄位。
        build_block_fn: 將三元組與屬性字典轉換為人類可讀文字區塊的函式。
        top_k: 每個三元組檢索的前 top_k 條結果。
        sim_th: 餘弦相似度門檻，低於此值將被捨棄。
        hp_col: head 屬性 json 欄位名稱，若無則設 None。
        rp_col: relation 屬性 json 欄位名稱，若無則設 None.
        tp_col: tail 屬性 json 欄位名稱，若無則設 None.

    Returns:
        符合條件的敘述區塊列表，每個元素為一行文字，保留原始編號。
    """
    results: List[str] = []

    for tp in triples:
        vec = embed_fn(tp)
        sims = kg_vecs_norm @ vec
        # 取出符合 sim_th 且排名前 top_k 的索引
        top_indices = np.argsort(sims)[-top_k:][::-1]

        for idx in top_indices:
            score = sims[idx]
            if score < sim_th:
                break
            row = kg_df.iloc[idx]
            # 基本三元組
            tri = {
                'head': row['head'],
                'relation': row['relation'],
                'tail': row['tail']
            }
            # 屬性詳情
            det: Dict[str, Dict[str, Any]] = {
                'head': json.loads(row[hp_col]) if hp_col and row.get(hp_col) else {},
                'rel':  json.loads(row[rp_col]) if rp_col and row.get(rp_col) else {},
                'tail': json.loads(row[tp_col]) if tp_col and row.get(tp_col) else {}
            }
            # 使用外部函式組合文字區塊
            block = build_block_fn([tri], {tuple(tri.values()): det})
            # 拆分為多行並加入結果
            for line in block.splitlines():
                results.append(line)

    return results
