# Flet Web Deployment

## Cloudflare Worker

Deploy the proxy Worker from `worker/` and set the PlantNet key as an encrypted secret:

```bash
cd worker
npx wrangler deploy
npx wrangler secret put PLANTNET_API_KEY
```

Only requests from `https://*.github.io` origins are allowed by CORS.

## Flet Build

Set `WORKER_URL` in `flet_app/main.py` to your deployed Worker URL, then build:

```bash
cd flet_app
uv run flet build web --yes --verbose --base-url -Art-Village-Exploration-Magnifier --route-url-strategy hash --web-renderer html
cd ..
python scripts/patch_flet_loader.py
```

The generated web app will be in `flet_app/build/web`.

## GitHub Pages

The workflow at `.github/workflows/deploy.yml` builds on every push to `main` and publishes the generated files to the `gh-pages` branch. In repository settings, set Pages source to deploy from the `gh-pages` branch.
