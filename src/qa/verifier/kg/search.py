# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: /home/karca5103/dev/FactGraph/src/qa/verifier/kg/search.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-07-04 08:02:18 UTC (1751616138)

"""
cosine_search 與 row → detail 
"""
import json
import numpy as np
from typing import List, Dict, Tuple
from .loader import KG_DF, KG_VECS_NORM, HP_COL, RP_COL, TP_COL
from ..core.config import SIM_TH, TOP_K

def cosine_search(tp: dict, q_vec: np.ndarray) -> List[int]:
    sims = KG_VECS_NORM @ q_vec
    idx = sims.argsort()[-TOP_K:][::-1]
    idx = idx[sims[idx] >= SIM_TH]
    return [i for i in idx if KG_DF.at[i, 'head'] == tp['head'] or KG_DF.at[i, 'tail'] == tp['tail']]

def kg_row_to_detail(idx: int) -> Tuple[dict, Dict[str, dict]]:
    row = KG_DF.iloc[idx]
    tri = {'head': row['head'], 'relation': row['relation'], 'tail': row['tail']}
    det = {'head': json.loads(row[HP_COL]) if HP_COL else {}, 'rel': json.loads(row[RP_COL]) if RP_COL else {}, 'tail': json.loads(row[TP_COL]) if TP_COL else {}}
    return (tri, det)