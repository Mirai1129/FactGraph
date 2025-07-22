# FactGraph – 部署指南

新聞事實查核全端平台

* **前端** Vue 3 ＋ Vite → **Firebase Hosting**
* **後端** FastAPI（Docker 容器）→ **Cloud Run**
* **映像倉庫** `gcr.io`（或區域 Artifact Registry，如 `asia‑southeast1-docker.pkg.dev`）

> ⚠️  前後端請使用**相同區域**。若需 L4 GPU，本專案現階段使用新加坡區域 (`asia‑southeast1`)。

---

## 1　前置準備

| 工具 | 測試版本 | 用途 |
|------|---------|------|
| Docker CLI / Desktop | 24.x | 本地建置映像 |
| Google Cloud CLI (`gcloud`) | 530.0.0 | 推送映像、部署 Cloud Run |
| Firebase CLI | 14.x | 部署 Firebase Hosting |
| Node 18 ＋ Yarn 1.x | 編譯 Vue 前端 |
| Python 3.12（venv） | — | 後端開發與本地測試 |

---

## 2　專案結構（深度 = 2）

```bash
$ tree -L 2
.
├── Dockerfile
├── frontend/
│   ├── firebase.json
│   └── vite.config.js
├── models/            # CKIP 等大型模型 ~500 MB
├── src/
│   └── web/           # FastAPI 入口 main.py
└── requirements.txt   # 由 `pip freeze` 產生
````

---

## 3　後端：建置 → 推送 → 部署

###  一次性「快取初始化」（只做一次）
目的：把 所有階段 的 layer 快取（尤其是 pip 與 模型 那層）寫進 Artifact Registry，日後就能命中。

1. 在 Artifact Registry 建一個專用快取 repo（建一次即可）。

```bash
gcloud artifacts repositories create buildcache \
  --repository-format=docker \
  --location=asia-southeast1
```

2. 啟用 Docker 與 AR 的認證

```bash
gcloud auth configure-docker asia-southeast1-docker.pkg.dev
```

3. 一次完整建置 + 把快取寫進 Registry

```bash
docker buildx build \
  --cache-to=type=registry,ref=asia-southeast1-docker.pkg.dev/factgraph-38be7/buildcache/backend,mode=max \
  --tag asia-southeast1-docker.pkg.dev/factgraph-38be7/factgraph-backend/factgraph-backend:latest \
  --push .                     
```
-> 直接推，避免 --load 造成 digest 變動
* mode=max ⇒ 連中間階段（Stage 1 pip install、模型層）都保存

* 這是最後一次看到大型 layer 上傳；完成後 Registry 已擁有所有快取

## 日常開發迭代
### 3.1 本機 build & 測試（不推送）
```bash
docker buildx build \
  --cache-from=type=registry,ref=asia-southeast1-docker.pkg.dev/factgraph-38be7/buildcache/backend \
  -t factgraph-backend:dev \
  --output=type=docker .

docker run --rm -p 8080:8080 factgraph-backend:dev
# 測試 OK 後…
```
→ 只在本機執行 build，利用遠端快取跳過不變的層，把最終映像載入本地 daemon。

→ 終端應出現 CACHED [deps 4/4] RUN pip install …，代表真的跳過重灌。

### 3.2.A 給映像加上遠端路徑（如果 build 時已經用遠端 tag，這步可略）
```bash
docker tag factgraph-backend:dev \
  asia-southeast1-docker.pkg.dev/factgraph-38be7/factgraph-backend/factgraph-backend:latest
```
* 把本地測試版打上遠端的 latest 標籤，準備推送。

### 3.2.B 確定無誤後推送至 Artifact Registry（只傳增量 layer）
```bash
docker push asia-southeast1-docker.pkg.dev/factgraph-38be7/factgraph-backend/factgraph-backend:latest
```
docker push 只會上傳 Registry 未持有的 layer，因此先前已存在舊層會被跳過(大層直接 Layer already exists)，只傳當次新增或修改的部分。推送完成後，Console 的 Artifact Registry → Repositories → factgraph-backend 就能看到最新的 digest 與時間戳。

### 3.3　部署到 Cloud Run

```bash
gcloud run deploy factgraph-backend \
  --image=asia-southeast1-docker.pkg.dev/factgraph-38be7/factgraph-backend/factgraph-backend:latest \
  --region=asia-southeast1 \
  --platform=managed \
  --cpu=8 \
  --memory=16Gi \
  --concurrency=80 \
  --timeout=900 \
  --allow-unauthenticated
```
參數都可以自行調整，我會簡單部署後，再到網頁進行部署一次，設定詳細配置。

（於 Cloud Console → Cloud Run → **Deploy** 圖形介面操作）

### 3.4　確認服務狀態

```bash
gcloud run services list --platform managed --region asia-southeast1
```

### 3.5　快取機制與快速重建

Dockerfile 將龐大檔案（模型、依賴）置於第一層，未改動 `requirements.txt` 或 `models/` 時，Cloud Build 會使用快取，只重新打包程式碼層，通常 1 分鐘內完成。

### 3.6　更新既有服務

```bash
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/factgraph-backend:latest .
gcloud run deploy factgraph-backend --image gcr.io/$GOOGLE_CLOUD_PROJECT/factgraph-backend:latest ...
```

（或於 Cloud Run 介面點 **Deploy Revision**）

---

## 4　後端 CORS 設定

`src/web/main.py`：將 Firebase Hosting 網域加入 `origins`，避免瀏覽器阻擋跨域。

```python
origins = [
    "http://localhost:8080",
    "http://localhost:5173",
    "https://factgraph-38be7.web.app",  # Firebase Hosting 網址
]
```

---

## 5　前端：建置與部署 Firebase Hosting

### 5.1　設定 `frontend/firebase.json`

```jsonc
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "region": "asia-southeast1",          // 與 Cloud Run 同區
    "rewrites": [
      {
        "source": "/api/**",
        "run": {
          "serviceId": "factgraph-backend",
          "region": "asia-southeast1"
        }
      },
      { "source": "**", "destination": "/index.html" }
    ]
  }
}
```

### 5.2　建置與部署

```bash
cd ~/dev/FactGraph/frontend
yarn install          # 初次執行
yarn build            # 生成 dist/
firebase deploy --only hosting
```

---

## 6　區域搬遷檢查表

1. Artifact Registry 標籤 → `asia-southeast1-docker.pkg.dev/...`
2. Cloud Run `--region` → `asia-southeast1`
3. `firebase.json` `"region"` → `asia-southeast1`
4. CORS 網域無需修改（`*.web.app` 不變）

---

## 7　本地除錯

| 功能              | 指令                                                      |
| --------------- | ------------------------------------------------------- |
| 啟動後端熱重載         | `uvicorn src.web.main:app --reload`                     |
| 模擬 Hosting + 重寫 | `firebase serve --only hosting`                         |
| 測試 API          | `curl -X POST http://127.0.0.1:8000/api/answerer/query` |

---

## 8　疑難排解

| 現象                | 可能原因                           | 解法                          |
| ----------------- | ------------------------------ | --------------------------- |
| Swagger UI 一直轉圈   | Cloud Run 冷啟動或 CORS 未放行        | 查看日誌、確認 `origins`           |
| `docker build` 超久 | 快取失效（改了 requirements / models） | 確認多階段設計，將大檔案固定在同層           |
| `/api/...` 404    | `firebase.json` 重寫錯誤           | 檢查 `"run"` 區塊與 serviceId    |
| 模型太大無法推 Git       | 可用 Git LFS 或改放 GCS             | `.gitignore` 忽略模型；部署時掛載 GCS |

---

## 9　常用指令

```bash
# 列出映像標籤
gcloud artifacts docker images list gcr.io/$PROJECT_ID/factgraph-backend

# 列出本地 Docker 映像
docker image list

# 查看 Cloud Run 日誌
gcloud logs read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=factgraph-backend" \
  --limit 50

# 將流量切至最新修訂，刪舊版
gcloud run services update-traffic factgraph-backend --to-latest
