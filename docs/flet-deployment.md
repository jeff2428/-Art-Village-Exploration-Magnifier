# Flet Web Deployment on Cloudflare Pages

## Cloudflare Worker

Deploy the proxy Worker from `worker/` and set the PlantNet key as an encrypted secret:

```bash
cd worker
npx wrangler deploy
npx wrangler secret put PLANTNET_API_KEY
```

Requests from Cloudflare Pages `https://*.pages.dev` origins are allowed by CORS. If you use a custom domain, set an `ALLOWED_ORIGIN` Worker variable such as `https://example.com`.

## Cloudflare Pages

Use Cloudflare Pages Git integration with these settings:

- Framework preset: `None`
- Root directory: `/`
- Build command: `bash build.sh`
- Build output directory: `flet_app/build/web`
- Production branch: `main`

Add this Pages environment variable before the first production build:

```text
WORKER_URL=https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev
```

`build.sh` installs the Flet dependencies, writes the Worker URL into `flet_app/build_config.py`, builds the static web app, then patches the custom loading animation.

Do not use this old build command:

```text
pip install flet requests opencc-python-reimplemented && flet build web
```

It does not pass `--yes`, so Cloudflare's non-interactive build environment can fail with `EOFError: EOF when reading a line` when Flet asks to install the required Flutter SDK. Use `bash build.sh` instead.

## Local Build

```bash
set WORKER_URL=https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev
bash build.sh
```

The generated web app will be in `flet_app/build/web`.
