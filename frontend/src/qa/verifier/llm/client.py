# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: /home/karca5103/dev/FactGraph/src/qa/verifier/llm/client.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-07-04 08:02:25 UTC (1751616145)

"""
OpenAI 初始化與共用 kwargs
"""
from openai import OpenAI
from ..core.paths import OPENAI_API_KEY, MODEL_ID
from typing import Dict, Any
if not OPENAI_API_KEY:
    raise RuntimeError('環境變數 GPT_API 尚未設定')
client = OpenAI(api_key=OPENAI_API_KEY)
GPT_KWARGS: Dict[str, Any] = {'model': MODEL_ID, 'temperature': 0.4, 'top_p': 0.9, 'max_tokens': 4096, 'timeout': 30}