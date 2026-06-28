# 藝素村探險放大鏡

以 React/Vite、Cloudflare Pages 與 Cloudflare Worker 建構的植物辨識與探險圖鑑 Web App。使用者可透過裝置相機拍攝植物，由 PlantNet 辨識物種，並以 Perenual 補充照護與毒性資料。

## 正式架構

- `flet_app/`：React 18、TypeScript、Vite 正式前端
- `worker/`：Cloudflare Worker API，保護 PlantNet/Perenual secrets、處理 CORS、限流與動物資料
- `admin/`：靜態動物管理頁面，由正式建置複製到輸出目錄
- `flet_app_old/`：歷史 Flet 實作，只供追溯，不參與正式建置
- `tests/`：Worker 與歷史相容性測試

## 本機開發

需要 Node.js 22。

```powershell
cd flet_app
npm ci
$env:VITE_API_URL = "https://YOUR-WORKER.workers.dev"
npm run dev
```

若未設定 `VITE_API_URL`，前端會使用同源 API，適合由本機 proxy 或整合環境提供。

## 品質檢查

```powershell
cd flet_app
npm run lint
npm test
npm run build
cd ..
node --check worker/index.js
python -m unittest tests.test_worker_security -v
```

## Cloudflare Worker

Worker secrets：

```powershell
cd worker
npx wrangler secret put PLANTNET_API_KEY
npx wrangler secret put PERENUAL_API_KEY
npx wrangler secret put ANIMALS_ADMIN_PASSWORD
npx wrangler deploy
```

正式環境應設定精確的 `ALLOWED_ORIGIN`。若需要接受指定 Pages/GitHub Pages 子網域，才設定 `ALLOW_PAGES_DOMAINS=true`。

## Cloudflare Pages

- Root directory：`/`
- Build command：`bash build.sh`
- Build output：`flet_app/build/web`
- Production branch：`main`
- 環境變數：`WORKER_URL=https://YOUR-WORKER.workers.dev`

`build.sh` 會將 `WORKER_URL` 映射為 Vite build-time 變數 `VITE_API_URL`，使用 `npm ci` 依照 lockfile 安裝，建置 React App，並複製管理頁與產生安全 headers。

## 安全邊界

- 第三方 API keys 只存在 Worker secrets，不進入瀏覽器 bundle。
- Worker 驗證 Origin、圖片 MIME、上傳大小與管理端 payload。
- 管理端密碼由 `X-Admin-Password` 傳至 Worker；公開部署仍應搭配 Cloudflare WAF 全域限流。
- CSP 目前是 report-only；切換 enforce 前需先檢查實際違規報告。

詳細規格見 [React 前端基礎重整規格](docs/spec-react-foundation.md) 與 [技術棧](docs/technical-stack.md)。

