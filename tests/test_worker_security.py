"""Worker CORS 上傳限制純 Node 測試。

不依賴 Flet / Python 端，跑 `node --test` 即可。
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER_JS = ROOT / "worker" / "index.js"


WORKER_PROBE_TEMPLATE = r"""// Minimal test harness: extract and exercise the corsHeaders /
// readMaxUploadBytes functions from the worker module without
// requiring wrangler/miniflare.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const source = readFileSync("__WORKER_INDEX__", "utf8");

// Strip ESM export block (we only want to inspect pure functions).
// Use a greedy match to consume the entire `export default { ... };` block.
const wrapped = source.replace(/export default \{[\s\S]*\}\s*;/, "");

const mod = new Function(wrapped + "\nreturn { corsHeaders, readMaxUploadBytes, isPagesDomainAllowed, s2t };")();

test("corsHeaders returns configured origin when matched", () => {
  const env = { ALLOWED_ORIGIN: "https://example.com" };
  const req = new Request("https://worker/x", { headers: { Origin: "https://example.com" } });
  assert.equal(mod.corsHeaders(req, env), "https://example.com");
});

test("corsHeaders returns null when origin does not match and pages domains disabled", () => {
  const env = { ALLOWED_ORIGIN: "https://example.com" };
  const req = new Request("https://worker/x", { headers: { Origin: "https://other.com" } });
  assert.equal(mod.corsHeaders(req, env), "null");
});

test("corsHeaders blocks pages.dev subdomains by default", () => {
  const env = { ALLOWED_ORIGIN: "https://example.com" };
  const req = new Request("https://worker/x", {
    headers: { Origin: "https://any-sub.pages.dev" },
  });
  assert.equal(mod.corsHeaders(req, env), "null");
});

test("corsHeaders allows pages.dev when ALLOW_PAGES_DOMAINS=true", () => {
  const env = {
    ALLOWED_ORIGIN: "https://example.com",
    ALLOW_PAGES_DOMAINS: "true",
  };
  const req = new Request("https://worker/x", {
    headers: { Origin: "https://art-village.pages.dev" },
  });
  assert.equal(mod.corsHeaders(req, env), "https://art-village.pages.dev");
});

test("corsHeaders allows github.io when ALLOW_PAGES_DOMAINS=true", () => {
  const env = {
    ALLOWED_ORIGIN: "https://example.com",
    ALLOW_PAGES_DOMAINS: "true",
  };
  const req = new Request("https://worker/x", {
    headers: { Origin: "https://jeff2428.github.io" },
  });
  assert.equal(mod.corsHeaders(req, env), "https://jeff2428.github.io");
});

test("corsHeaders rejects invalid URL origins", () => {
  const env = { ALLOW_PAGES_DOMAINS: "true" };
  const req = new Request("https://worker/x", { headers: { Origin: "not-a-url" } });
  assert.equal(mod.corsHeaders(req, env), "null");
});

test("isPagesDomainAllowed defaults to false", () => {
  assert.equal(mod.isPagesDomainAllowed({}), false);
  assert.equal(mod.isPagesDomainAllowed({ ALLOW_PAGES_DOMAINS: "false" }), false);
  assert.equal(mod.isPagesDomainAllowed({ ALLOW_PAGES_DOMAINS: "TRUE" }), true);
});

test("readMaxUploadBytes honors env override", () => {
  assert.equal(mod.readMaxUploadBytes({ MAX_UPLOAD_BYTES: "2048" }), 2048);
  assert.equal(mod.readMaxUploadBytes({}), 10 * 1024 * 1024);
  assert.equal(mod.readMaxUploadBytes({ MAX_UPLOAD_BYTES: "garbage" }), 10 * 1024 * 1024);
});

test("s2t converts common PlantNet simplified names without frontend OpenCC", () => {
  assert.equal(mod.s2t("榕树"), "榕樹");
  assert.equal(mod.s2t("垂叶榕"), "垂葉榕");
});
"""


def _build_probe() -> str:
    escaped = str(WORKER_JS).replace("\\", "\\\\")
    return WORKER_PROBE_TEMPLATE.replace("__WORKER_INDEX__", escaped)


class WorkerSecurityTests(unittest.TestCase):
    def test_cors_and_upload_rules(self):
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".mjs",
                delete=False,
                encoding="utf-8",
            ) as tmp:
                tmp.write(_build_probe())
                tmp_path = Path(tmp.name)
        except OSError:
            self.skipTest("cannot create temp file")
            return

        try:
            result = subprocess.run(
                ["node", "--test", str(tmp_path)],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except FileNotFoundError:
            self.skipTest("node not available on PATH")
            return
        finally:
            try:
                tmp_path.unlink()
            except OSError:
                pass

        if result.returncode != 0:
            self.fail(
                "Worker security tests failed:\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )


if __name__ == "__main__":
    unittest.main()
