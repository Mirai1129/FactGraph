# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: /home/karca5103/dev/FactGraph/src/qa/answerer/llm/gpt.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-07-01 14:12:47 UTC (1751379167)

from __future__ import annotations
import time
from openai import OpenAI, OpenAIError, APITimeoutError
__all__ = ['GPTClient']

class GPTClient:

    def __init__(self, api_key: str, model_id: str, **kwargs):
        self._client = OpenAI(api_key=api_key)
        self._base_kwargs = {'model': model_id, **kwargs}

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        backoff = 5
        while True:
            try:
                resp = self._client.chat.completions.create(messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}], **self._base_kwargs)
                return resp.choices[0].message.content.strip()
            except (OpenAIError, APITimeoutError) as err:
                print(f'[WARN] GPT retry in {backoff}s → {err}')
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)