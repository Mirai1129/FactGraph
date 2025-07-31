#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import random
import re
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# ---------- 0. 參數 ----------
# TOPIC_URL  = "https://www.cna.com.tw/news/asoc/202504080379.aspx?topic=4623"
TOPIC_URL = "https://www.cna.com.tw/news/aloc/202507310106.aspx"
TARGET_NUM = 300
OUT_PATH = Path("data/raw/news/cna") / "cna_sample.json"

# ---------- 1. Selenium 基本設定 ----------
opt = webdriver.ChromeOptions()
opt.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
opt.add_experimental_option("excludeSwitches", ["enable-automation"])
opt.add_experimental_option("useAutomationExtension", False)

# ── 改用官方 .deb 版 Chrome 的 headless 啟動 ──
opt.add_argument("--headless=new")
opt.add_argument("--no-sandbox")
opt.add_argument("--disable-dev-shm-usage")
opt.add_argument("--disable-gpu")
# binary 位置改成官方安裝路徑
opt.binary_location = "/usr/bin/google-chrome-stable"

# ---------- 1-1. chromedriver 來源 ----------
# webdriver-manager 會自動下載對應版本的 driver
service = Service(ChromeDriverManager().install())

driver = webdriver.Chrome(service=service, options=opt)
driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"},
)
wait = WebDriverWait(driver, 20)

# ---------- 2. 開啟主題頁並等待初始載入 ----------
driver.get(TOPIC_URL)
time.sleep(1 + random.uniform(0.5, 1.0))
body = driver.find_element(By.TAG_NAME, "body")

# ---------- 3. 收集動態變化的網址 ----------
urls, seen = [], set()
current_url = driver.execute_script("return window.location.href")
urls.append(current_url)
seen.add(current_url)
last_update_time = time.time()

while len(urls) < TARGET_NUM:
    body.send_keys(Keys.PAGE_DOWN)
    time.sleep(random.uniform(0.3, 0.5))

    new_url = driver.execute_script("return window.location.href")
    if new_url != current_url and new_url not in seen:
        urls.append(new_url)
        seen.add(new_url)
        current_url = new_url
        last_update_time = time.time()
        print("⇢ 新網址", new_url)

    if time.time() - last_update_time >= 10:
        print("⚠️ 10 秒內無新網址，停止滾動。")
        break

print(f"共收集 {len(urls)} 筆連結")

# ---------- 4. 逐篇進入詳細頁抓取資料 ----------
records = []
re_date = re.compile(r"/news/[^/]+/(\d{12})\.aspx")

for url in urls:
    driver.get(url)
    time.sleep(1 + random.uniform(0.5, 1.0))

    # 4-1 標題
    try:
        title = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1 span"))
        ).text.strip()
    except Exception:
        title = "標題未取得"

    # 4-2 日期（URL → YYYY-MM-DD）
    m = re_date.search(url)
    date = (
        datetime.strptime(m.group(1)[:8], "%Y%m%d").strftime("%Y-%m-%d")
        if m else "日期未取得"
    )

    # 4-3 分類（breadcrumb 第 2 個 <a>）
    cat_elems = driver.find_elements(By.CSS_SELECTOR, ".breadcrumb a")
    category = cat_elems[1].text.strip() if len(cat_elems) > 1 else ""

    # 4-4 內文；去掉版權宣告
    paras = driver.find_elements(By.CSS_SELECTOR, "#article-body p, div.paragraph p")
    content = "\n".join(
        p.text.strip()
        for p in paras
        if p.text.strip() and "本網站之文字" not in p.text
    )

    # 4-5 組裝
    records.append({
        "date": date,
        "publisher": "CNA",
        "category": category,
        "title": title,
        "content": content,
        "label": True,
    })

# ---------- 5. 輸出 JSON 檔 ----------
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with OUT_PATH.open("w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"✅ 完成 {len(records)} 篇，輸出 → {OUT_PATH.resolve()}")
driver.quit()
