# 藝素村探險放大鏡 — 2026 重構與強化計畫

> 文件版本：v1.0（2026-06-03 建立）
> 對應分支：`main`
> 對應 PR 序列：PR1 → PR2 → PR3 → PR4 → PR5 → PR6

## 1. 背景與動機

本專案「藝素村探險放大鏡」目前以 Flet Web + Cloudflare Worker + Cloudflare Pages 架構提供植物辨識與探險圖鑑服務。經 2026-06 全面健檢，發現以下三類問題需有計畫地解決：

- **安全**：CSP header（已實施 report-only）、CORS 白名單收斂（已完成）、Worker 上傳大小與 MIME 限制（已完成）。
- **結構**：`flet_app/main.py` 單檔 1400 行，`AppState` 同時持有 UI 控制項與業務資料，難以維護與測試。
- **體驗**：相機變焦採整頁 update、圖鑑加入動畫序列執行、圖片壓縮預設 `optimize=True` 在 Pyodide 中偏慢。

本計畫以「分多次、可獨立 revert 的 PR」方式逐步改善，目標是在不打斷現有功能的前提下完成現代化與強化。

## 2. 目標

1. 安全：補上 CSP、收斂 CORS、限制 Worker 上傳大小與 MIME。
2. 結構：把 `main.py` 拆為 `views/` + `services/` + 狀態機 enum。
3. 流暢：相機變焦、圖鑑動畫、圖片壓縮等體感優化。
4. 美化：以「台灣本土動植物」為主題的插畫童書風（保留米黃書本主色）。
5. 工程：CI（GitHub Actions）、Playwright smoke、型別檢查與依賴收斂。

## 3. 範圍

### In-Scope
- 前端：`flet_app/` 全部原始碼
- Worker：`worker/index.js`、`worker/wrangler.toml`
- 構建：`build.sh`、`scripts/`、`_headers` 產出
- CI：`.github/workflows/`
- 文件：`docs/`、`README.md`
- 測試：`tests/`

### Out-of-Scope
- 把前端換成純 JS / 非 Flet 方案（保留與 `prototype/index.html` 對照的策略）
- 改 Cloudflare Pages 之外的部署目標
- 改 PlantNet / Perenual 對外的 API 規格

## 4. 指令

| 動作 | 指令 |
|---|---|
| 安裝依賴 | `pwsh scripts/install-dev.ps1` |
| 開發 | `pwsh scripts/dev.ps1`（瀏覽器監看 + 熱重載） |
| 構建 | `bash build.sh` |
| 測試 | `python -m unittest discover -s tests` |
| Lint | `python -m ruff check --target-version py312 flet_app/ tests/` |
| 型別 | `python -m mypy flet_app` |
| 部署 | `git push origin main`（觸發 Cloudflare Pages 自動 build） |

## 5. 目標結構（PR4 完成後）

```
flet_app/
├── main.py                # 入口，僅負責路由與 Page 初始化
├── app_state.py           # 純資料 + 狀態機 enum，移除 UI 控制項
├── app_types.py
├── ui_theme.py
├── camera_utils.py
├── plant_api.py
├── magnifier_handle.py    # 視覺元件不變
├── pokedex_manager.py
├── build_config.py
├── services/
│   ├── camera_manager.py  # 封裝相機生命週期
│   ├── recognition.py     # PlantNet + Perenual 流程
│   ├── storage.py         # pokedex / dark mode
│   └── animals.py         # 動物資料動態載入
├── views/
│   ├── welcome.py
│   ├── plant_view.py
│   ├── animal_view.py
│   ├── gallery.py
│   └── dialogs.py         # 拆出 show_plant_card / show_animal_card
└── components/
    ├── illustrations.py   # 插畫風 SVG/emoji 組件
    └── toasts.py          # 全域 toast/snackbar
```

## 6. 程式碼風格

- 函式 ≤ 60 行，必要時拆 helper
- `from __future__ import annotations` 全部沿用
- 型別：公開 API 必填，內部輔助函式不強制
- 例外一律 `RecognitionServiceError` 或自訂，避免裸 `Exception`
- 註解僅解釋「為什麼」，不解釋「做什麼」
- 狀態以 enum 表示（`CameraState`、`RecognitionState`、`Mode`），不留舊布林旗位

## 7. 測試策略

- 單元測試：`tests/test_*.py`，每個新模組都補
- 工件測試：`tests/test_flet_artifacts.py` 持續維護
- 整合 smoke：Playwright 跑 `test_reload.py` 場景（CI 排程每日）
- Worker 安全測試：新增 `tests/test_worker_security.py`（純 Node 測 `corsHeaders()`）

## 8. PR 序列總覽

| PR | 標題 | 規模 | 主要內容 |
|---|---|---|---|
| PR1 | chore: 提交未儲存改動 + 文件盤點 | XS | 提交歡迎/Shell 切換改動、建立本 spec |
| PR2 | feat(security): CSP、CORS 收斂、Worker 上傳限制 | S | CSP report-only、CORS 白名單、Content-Length 與 MIME 限制 |
| PR3 | perf(smoothness): 局部 update、變焦優化、Staggered 動畫 | M | F1–F5、F7 |
| PR4 | refactor: 拆分 main.py 為 views + services + 狀態機 | L | O1–O5 |
| PR5 | feat(ui): 插畫童書風美化 | M-L | B1–B12、台灣本土動植物風 |
| PR6 | chore(ci): 增強 CI、Playwright 巡檢、依賴收斂 | S | O6–O9、O13、O14 |

## 9. 部署節奏

每個 PR 完成即 push 到 `main`，由 Cloudflare Pages 自動 build。  
若該 PR 線上發現問題，可單獨 revert 不影響後續 PR。

## 10. 風險與緩解

| 風險 | 影響 | 緩解 |
|---|---|---|
| `test_flet_artifacts.py` 字串斷言會被 PR4 打破 | 測試全紅 | PR4 開始前先轉成行為斷言 |
| CSP report-only 觀察期間出現逸出 | 線上功能失效 | 24h 觀察 log，調整白名單再改 enforce |
| Pyodide 內 Pillow 效能 | 拍攝回饋慢 | PR3 透過 `optimize=False` 縮短 |
| 插畫 SVG 體積過大 | 構建包變肥 | 採內聯 + gzip；> 4KB 才走外部檔 |
| GitHub Actions 額度 | 額度耗盡 | 預設只在 `main` 與 PR 觸發，smoke 每日一次 |

## 11. 補充策略摘要

### 11.1 PR2 CSP report-only 觀察期

- 在 `_headers` 設 `Content-Security-Policy-Report-Only` 與 `Report-To`
- 觀察 24h，比對 Worker / Pages log
- 之後改為去掉 `-Report-Only` 直接 enforce

### 11.2 PR2 Worker 上傳限制

- `MAX_UPLOAD_BYTES = 10 * 1024 * 1024`
- `ALLOWED_IMAGE_MIME = { image/jpeg, image/png, image/webp }`
- 預先檢查 `Content-Length` 與 `image.type`

### 11.3 PR2 CORS 收斂

- 預設僅放行 `env.ALLOWED_ORIGIN`
- `env.ALLOW_PAGES_DOMAINS === "true"` 時才放行 `pages.dev` 與 `github.io` 子域
- 不再 fallback `"https://pages.dev"` 字串

### 11.4 PR5 插畫清單（台灣本土動植物）

| 主題 | 元素 | 用途 |
|---|---|---|
| 葉脈 | 月桃葉、台灣欒樹葉、台灣山蘇 | 歡迎頁背景紋理 |
| 鳥類 | 台灣藍鵲、五色鳥 | 模式切換插畫、圖鑑空狀態 |
| 兩棲類 | 台北樹蛙、面天樹蛙 | 拍攝成功 toast、提示 |
| 花卉 | 臺灣百合、艷紅鹿子百合 | 載入動畫、過場 |
| 樹木 | 樟樹、櫸木、台灣杉 | 主畫面裝飾 |
| 紙材 | 牛皮紙、棉紙紋理 | 卡片背景層 |

### 11.5 PR5 套件策略

| 方案 | 採用 |
|---|---|
| 內聯 SVG（純手寫） | 主要 |
| OpenMoji（CC BY-SA 4.0） | 候選，僅用於動物插畫 |
| Lottie | 暫不採用（Pyodide 載入慢） |
| `flet_animations` | PR5 開始時驗證 0.85 支援度 |
| iconify / Tabler Icons | 不用（風格不搭） |

### 11.6 PR5 資產組織

```
flet_app/assets/
├── illustrations/
│   ├── welcome/
│   ├── animal-mode/
│   ├── gallery-empty/
│   └── capture-success/
├── textures/
└── README.md  # 來源、授權、CC 標註
```

## 12. 成功條件

- 全部 6 個 PR 合併至 `main`
- `python -m unittest` 29 項以上測試全綠
- `python -m ruff check` 零警告
- `node --check worker/index.js` 通過
- CSP enforce 上線 7 日後零逸出
- Playwright smoke 每週通過
- 線上 `art-village-exploration-magnifier.pages.dev` 主要流程（歡迎 → 拍攝 → 辨識 → 加入圖鑑 → 模式切換）正常

## 13. 開放問題追蹤

> 目前無懸而未決的開放問題；如有新增，會在此處追加。
