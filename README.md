# 藝素村探險放大鏡

Flet Web + Cloudflare Worker + GitHub Pages 版本。

## 架構

- `flet_app/`：Flet Web 前端，負責相機、擬物化放大鏡 UI、模式切換與探險圖鑑。
- `worker/`：Cloudflare Worker API 中繼站，負責隱藏 `PLANTNET_API_KEY` 並處理 CORS。
- `.github/workflows/deploy.yml`：push 到 `main` 時自動建置 Flet Web，並發布到 `gh-pages` 分支。

## Cloudflare Worker

```bash
cd worker
npx wrangler secret put PLANTNET_API_KEY
npx wrangler deploy
```

部署後，把 Worker URL 填入 `flet_app/main.py` 的 `WORKER_URL`。

## 本機開發

```bash
cd flet_app
uv run flet run -d chrome
```

## 建置 GitHub Pages

```bash
cd flet_app
uv run flet build web --yes --verbose --base-url -Art-Village-Exploration-Magnifier --route-url-strategy hash --web-renderer html
cd ..
python scripts/patch_flet_loader.py
```

輸出目錄為 `flet_app/build/web`。
