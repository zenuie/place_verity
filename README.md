# Veritas - 地點資料自動核實系統

**Veritas** 是一個高效能、非同步的地點資料自動核實系統。它採用 FastAPI 框架，透過整合 Google Search API 和大型語言模型 (LLM)，自動化地驗證、更新地理位置資訊，旨在將地圖維護人員從繁瑣的手動資料搜尋中解放出來。

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://pytest.org)

---

## 核心功能

- **自動化檢索**: 透過 Google Search API，自動抓取與地點相關的最新公開資訊。
- **智慧分析**: 利用 OpenAI GPT 模型，從非結構化的搜尋結果中提取關鍵資訊 (如營業狀態、聯絡電話)，並與現有資料進行比對。
- **差異報告生成**: 為每筆地點資料生成結構化的 JSON 差異報告，包含新舊值、證據來源與可信度分數。
- **可配置的自動化流程**: 高可信度的變更可設定為自動核准，低可信度或有衝突的資訊則進入人工審核隊列。
- **並行安全**: 內建執行鎖 (Execution Locks)，防止同一地點或全域批次任務被重複觸發，確保資料一致性。
- **現代化技術棧**: 基於 `FastAPI`、`HTTPX` 和 `asyncio`，提供高效能的非同步處理能力。

## 技術架構

本專案遵循業界最佳實踐，採用清晰的分層架構：

- **API 層 (`api`)**: 使用 FastAPI `APIRouter` 定義所有 HTTP 端點，處理請求驗證與回應序列化。
- **服務層 (`services`)**: 包含核心業務邏輯，如呼叫外部 API、資料處理與報告生成。此層與 Web 框架解耦，便於測試。
- **核心層 (`core`)**: 管理應用程式的設定 (Pydantic Settings) 和外部資源的生命週期 (如 `HTTPX` 和 `OpenAI` 的客戶端)。
- **資料層 (`storage`)`**: 抽象化資料存取。目前為記憶體模擬，可輕易替換為 PostgreSQL 或其他資料庫。
- **模型層 (`models`)**: 使用 Pydantic `BaseModel` 定義所有資料結構，確保 API 的型別安全。

## 環境設定

### 前置要求

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/#installation) (用於相依性管理)

### 安裝步驟

1.  **Clone 專案**:
    ```bash
    git clone https://your-repository-url/veritas.git
    cd veritas
    ```

2.  **安裝相依套件**:
    Poetry 會自動建立一個虛擬環境並安裝所有必要的套件。
    ```bash
    poetry install
    ```

3.  **設定環境變數**:
    複製範例設定檔，並填入您自己的 API 金鑰。
    ```bash
    cp .env.example .env
    ```
    接著，編輯 `.env` 檔案：
    ```ini
    # .env
    OPENAI_API_KEY="sk-..."
    GOOGLE_API_KEY="AIzaSy..."
    GOOGLE_CX="xxxxxxxxxxxxxxxxxxxxxxxxx" # 您的 Google 可程式化搜尋引擎 ID
    AUTO_APPROVE_THRESHOLD=0.9
    ```

## 啟動與使用

### 啟動開發伺服器

此命令將啟動一個 Uvicorn 伺服器，並在程式碼變更時自動重載。

```bash
poetry run uvicorn veritas_app.main:app --reload
```

伺服器將在 `http://127.0.0.1:8000` 上運行。

### API 互動式文件

應用程式啟動後，可透過瀏覽器訪問 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** 查看由 Swagger UI 自動生成的互動式 API 文件。您可以在此頁面上直接測試所有 API 端點。

### 主要 API 端點

- `GET /verify/status/{place_id}`: 查詢特定地點的執行狀態。
- `POST /verify/manual/fetch`: 手動觸發對單一地點的資料核實流程。
- `POST /verify/manual/review-approve`: 核准並更新地點資料。
- `POST /verify/auto/trigger`: 在背景觸發一次全域的自動化核實任務。

## 測試

本專案使用 `pytest` 進行單元測試，並透過 `respx` 套件來模擬 (mock) 對外部 API (Google, OpenAI) 的 HTTP 請求，使得測試無需真實的網路連線，且執行速度快。

要執行所有測試，請運行：

```bash
poetry run pytest
```

## 後續擴充方向

- **資料庫整合**: 將 `storage` 層的記憶體模擬替換為使用 `SQLAlchemy` 或 `Tortoise ORM` 的真實資料庫 (如 PostgreSQL)。
- **審核佇列與 UI**: 建立一個審核佇列的資料表和一個簡單的前端 UI，讓地圖維護人員可以更方便地批次審核差異報告。
- **訊息佇列**: 對於全域自動化任務，引入如 `Celery` 或 `ARQ` 的訊息佇列系統，使其更健壯，並支援分散式執行。
- **快取機制**: 引入 `Redis` 快取，減少對 Google Search API 的重複請求，降低成本並提升效能。
- **優化抽取規則**: 持續優化 LLM 的提示詞 (Prompt)，或加入更多基於規則的抽取器 (如 `libpostal` 進行地址正規化) 來提升資料處理的準確性。