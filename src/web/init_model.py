# src/web/init_model.py
import os
import time
from sentence_transformers import SentenceTransformer

def load_ckip_model():
    model_name = 'ckiplab/bert-base-chinese'
    model_cache_path = 'models/CKIP'

    print(f"🚀 正在初始化 CKIP 模型：{model_name}")
    t0 = time.time()

    try:
        model = SentenceTransformer(
            model_name,
            trust_remote_code=True,
            cache_folder=model_cache_path
        )
    except Exception as e:
        print("❌ 模型載入失敗：", e)
        raise

    elapsed = time.time() - t0
    print(f"✅ 模型載入成功，耗時 {elapsed:.2f} 秒。")
    return model
