"""FactGraph ‒ FastAPI 介面層."""
from importlib.metadata import version

__all__ = ["__version__"]
__version__ = version("fastapi")  # 方便前端顯示後端版本
