# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: /home/karca5103/dev/FactGraph/src/qa/answerer/llm/prompt_loader.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-07-01 14:13:00 UTC (1751379180)

from pathlib import Path
__all__ = ['load_prompt']

def load_prompt(path: Path) -> str:
    return path.read_text(encoding='utf-8-sig')