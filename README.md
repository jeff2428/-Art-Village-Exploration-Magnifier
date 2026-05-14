# 藝素村探險放大鏡

Flet Web + Cloudflare Worker + Cloudflare Pages 版本。

## 架構

- `flet_app/`：Flet Web 前端，負責相機、擬物化放大鏡 UI、模式切換與探險圖鑑。
- `worker/`：Cloudflare Worker API 中繼站，負責隱藏 `PLANTNET_API_KEY` 並處理 CORS。
- `build.sh` / `wrangler.toml`：Cloudflare Pages 建置設定，push 到 `main` 後由 Cloudflare 自動建置與發布。

## Cloudflare Worker

這個 Worker 是 PlantNet API 中繼站，不是網頁前端。

```bash
cd worker
npx wrangler secret put PLANTNET_API_KEY
npx wrangler deploy
```

部署後，把 Worker URL 填到 Cloudflare Pages 的 `WORKER_URL` 環境變數。

如果你要讓 Worker 也連 Git 自動部署，Cloudflare Worker 的 Build 設定請使用：

- Build command：`echo "No Worker build step"`
- Deploy command：`npx wrangler deploy -c worker/wrangler.toml`
- Version command：`npx wrangler versions upload -c worker/wrangler.toml`
- Root directory：`/`
- Production branch：`main`

Worker 的 Variables and secrets 要新增：

```text
PLANTNET_API_KEY=你的 PlantNet API Key
```

## 本機開發

```bash
cd flet_app
uv run flet run -d chrome
```

## Cloudflare Pages 設定

這裡才是網頁前端，也就是 Flet 靜態網頁。

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

不要使用舊指令：

```text
pip install flet requests opencc-python-reimplemented && flet build web
```

這個舊指令沒有 `--yes`，Cloudflare 無互動建置環境會在 Flet 詢問是否安裝 Flutter SDK 時失敗。

## 本機建置

```bash
set WORKER_URL=https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev
bash build.sh
```

輸出目錄為 `flet_app/build/web`。
