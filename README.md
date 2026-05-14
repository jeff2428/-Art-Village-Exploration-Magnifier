# 藝素村探險放大鏡

Flet Web + Cloudflare Worker + Cloudflare Pages 版本。

## 架構

- `flet_app/`：Flet Web 前端，負責相機、擬物化放大鏡 UI、模式切換與探險圖鑑。
- `worker/`：Cloudflare Worker API 中繼站，負責隱藏 `PLANTNET_API_KEY` 並處理 CORS。
- `build.sh` / `wrangler.toml`：Cloudflare Pages 建置設定，push 到 `main` 後由 Cloudflare 自動建置與發布。

## Cloudflare Worker

```bash
cd worker
npx wrangler secret put PLANTNET_API_KEY
npx wrangler deploy
```

部署後，把 Worker URL 填到 Cloudflare Pages 的 `WORKER_URL` 環境變數。

## 本機開發

```bash
cd flet_app
uv run flet run -d chrome
```

## Cloudflare Pages 設定

在 Cloudflare Pages 專案使用這些設定：

- Framework preset：`None`
- Root directory：`/`
- Build command：`bash build.sh`
- Build output directory：`flet_app/build/web`
- Production branch：`main`

Pages 環境變數：

```text
WORKER_URL=https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev
```

## 本機建置

```bash
set WORKER_URL=https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev
bash build.sh
```

輸出目錄為 `flet_app/build/web`。
