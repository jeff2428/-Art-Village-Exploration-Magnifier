# 編譯前必讀紀錄

這份檔案是給每次本機測試、Cloudflare Pages 編譯、或排錯前先看的紀錄。遇到同樣錯誤時，先照這裡檢查，可以省很多時間。

## 目前架構

- 前端：Flet Web App，主要程式在 `flet_app/main.py`
- 放大鏡手柄 UI：`flet_app/magnifier_handle.py`
- Worker API 中繼站：`worker/index.js`
- Cloudflare Pages 前端網址：`https://art-village-exploration-magnifier.pages.dev`
- Cloudflare Worker API 網址：`https://art-village-magnifier.jeff2428.workers.dev`
- 前端 Worker 設定檔：`flet_app/build_config.py`

## 每次本機測試前

1. 開 PowerShell 到專案根目錄：

```powershell
cd C:\Users\jeff2\Documents\-Art-Village-Exploration-Magnifier-main
```

2. 啟動本機 Flet：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
```

3. 瀏覽器會開 `127.0.0.1` 的網址。

4. 如果畫面怪怪的，先按重新整理。

5. 如果仍然卡住，回 PowerShell 按 `Ctrl+C` 停掉，再重新執行 `scripts/dev.ps1`。

## 每次 Cloudflare Pages 編譯前

Cloudflare Pages 的 Build command 要用：

```bash
bash build.sh
```

Build output directory 要是：

```text
flet_app/build/web
```

Framework preset 選：

```text
None
```

Root directory 保持空白或 `/`。

## 重要環境變數

Cloudflare Pages 前端需要：

```text
WORKER_URL=https://art-village-magnifier.jeff2428.workers.dev
```

Cloudflare Worker 後端需要 Secret：

```text
PLANTNET_API_KEY
```

注意：PlantNet API Key 不要寫進前端，也不要 commit 到 GitHub。只放在 Cloudflare Worker 的 Secret 裡。

## 常見錯誤紀錄

### 1. `No module named 'js'`

原因：本機 `flet run` 是一般 Python，不是瀏覽器 Pyodide。

目前修法：`main.py` 會自動偵測，網頁版用 `fetch`，本機版用 `requests`。

### 2. 卡在 `working`

可能原因：

- Worker 沒回應
- PlantNet API Key 沒設好
- 相機回傳格式不是原本預期的 data URL
- 本機同步網路請求卡住畫面

目前修法：

- `main.py` 已加入 `capture_to_bytes()`
- 本機 `requests.post()` 已改成背景執行緒
- 如果還卡住，先看畫面狀態文字或 PowerShell 錯誤訊息

### 3. `Camera is not initialized. Call initialize() first`

原因：按拍攝時相機還沒初始化完成。

目前修法：程式有 `camera_ready` 檢查，未準備好時不會直接拍照。

### 4. Flet API 相容性錯誤

之前遇過：

```text
module 'flet.controls.alignment' has no attribute 'center'
module 'flet.controls.border' has no attribute 'all'
FilledTonalButton.__init__() got an unexpected keyword argument 'text'
module 'flet.controls.border_radius' has no attribute 'only'
```

原因：Flet 0.85 API 跟舊版範例不同。

目前修法：程式改用 Flet 0.85 可用寫法。

### 5. Cloudflare 編譯卡在安裝 Flutter SDK

原因：`flet build web` 第一次會詢問是否安裝 Flutter SDK，但 Cloudflare 沒辦法互動回答。

目前修法：`build.sh` 使用：

```bash
flet build web --yes --verbose --route-url-strategy hash --web-renderer auto
```

### 6. `--web-renderer html` 錯誤

原因：Flet 0.85 不支援 `html` renderer。

目前修法：使用：

```bash
--web-renderer auto
```

## 部署前檢查

本機可以先跑：

```powershell
C:\Users\jeff2\anaconda3\python.exe -m unittest discover -s tests
C:\Users\jeff2\anaconda3\python.exe -m compileall flet_app scripts tests
node --check worker\index.js
```

如果都通過，再 push 到 GitHub：

```powershell
git status
git add .
git commit -m "Update Flet app"
git push
```

注意：`AGENTS.md` 和 `skills/` 是本機工具資料，不一定要 commit。commit 前先看 `git status`。

## 目前要特別記得

- 前端不要直接使用 PlantNet API Key。
- 前端只呼叫 Worker URL。
- Worker 才呼叫 PlantNet。
- 本機測試正常後，再交給 Cloudflare Pages 編譯。
- 如果 Cloudflare 成功但頁面空白，先看瀏覽器 Console 或 Flet 錯誤畫面。
- 如果拍照沒有反應，先看是否顯示「相機準備中」或「正在拍攝並辨識」。
