# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: /home/karca5103/dev/FactGraph/src/qa/verifier/core/config.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-07-01 03:00:52 UTC (1751338852)

"""
集中管理超參數與正則表達式
"""
import re

SIM_TH: float = 0.8
TOP_K: int = 100
LLM_ROUNDS: int = 3
DUP_TH: float = 0.8
ENTITY_RE = re.compile('^\\d+\\.\\s*(.+?)\\s*透過關係')
