# Flet Web Deployment on Cloudflare Pages

## Cloudflare Worker

Deploy the proxy Worker from `worker/` and set the PlantNet key as an encrypted secret:

```bash
cd worker
npx wrangler deploy
npx wrangler secret put PLANTNET_API_KEY
npx wrangler secret put PERENUAL_API_KEY
```

Requests from Cloudflare Pages `https://*.pages.dev` origins are allowed by CORS. If you use a custom domain, set an `ALLOWED_ORIGIN` Worker variable such as `https://example.com`.

If the Worker is connected to Git, use these Worker build settings:

- Build command: `echo "No Worker build step"`
- Deploy command: `npx wrangler deploy -c worker/wrangler.toml`
- Version command: `npx wrangler versions upload -c worker/wrangler.toml`
- Root directory: `/`
- Production branch: `main`

Add `PLANTNET_API_KEY` and `PERENUAL_API_KEY` in Worker Variables and secrets. PlantNet performs image identification; Perenual is used afterward for the identified plant's toxicity and care details. If `PERENUAL_API_KEY` is missing, plant identification still works, but the app falls back to conservative local metadata.

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

It does not pass `--yes`, so Cloudflare's non-interactive build environment can fail with `EOFError: EOF when reading a line` when Flet asks to install the required Flutter SDK. Recent Flet versions also accept only `auto`, `canvaskit`, or `skwasm` for `--web-renderer`. Use `bash build.sh` instead.

## Local Development Workflow

Use Cloudflare Pages as the production display machine, not as the draft workspace.

Install dependencies once:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-dev.ps1
```

Start local Flet development:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
```

This runs `flet run -d -w main.py` from `flet_app/`. In Flet 0.85, `-d` watches the script directory for hot reload, and `-w` opens the web app in your browser.

Iterate locally until the UI, buttons, responsive layout, and API calls are acceptable. Push to GitHub only when the change is ready for Cloudflare to compile and publish.

## Local Build

```bash
set WORKER_URL=https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev
bash build.sh
```

The generated web app will be in `flet_app/build/web`.
