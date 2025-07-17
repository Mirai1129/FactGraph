# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: /home/karca5103/dev/FactGraph/src/qa/answerer/kg/loader.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-07-01 14:11:48 UTC (1751379108)

from pathlib import Path
import numpy as np
import pandas as pd
__all__ = ['load_kg_vectors', 'load_kg_df']

def load_kg_vectors(path: Path):
    vecs = np.load(path)
    return (vecs, vecs / np.linalg.norm(vecs, axis=1, keepdims=True))

def load_kg_df(path: Path):
    df = pd.read_csv(path)
    hp_col = 'head_props' if 'head_props' in df.columns else None
    rp_col = 'rel_props' if 'rel_props' in df.columns else None
    tp_col = 'tail_props' if 'tail_props' in df.columns else None
    return (df, hp_col, rp_col, tp_col)