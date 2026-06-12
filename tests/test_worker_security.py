"""Worker CORS 上傳限制純 Node 測試。

不依賴 Flet / Python 端，跑 `node --test` 即可。
"""
# ruff: noqa: E501

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

const mod = new Function(wrapped + "\nreturn { corsHeadersMap, corsHeaders, readMaxUploadBytes, isPagesDomainAllowed, normalizeAnimalsPayload, s2t, checkRateLimit, timingSafeEqual };")();  // noqa: E501

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

test("corsHeadersMap allows animal admin PUT password header", () => {
  const env = { ALLOWED_ORIGIN: "https://example.com" };
  const req = new Request("https://worker/animals", {
    headers: { Origin: "https://example.com" },
  });
  const headers = mod.corsHeadersMap(req, env);
  assert.match(headers["Access-Control-Allow-Methods"], /PUT/);
  assert.match(headers["Access-Control-Allow-Headers"], /X-Admin-Password/);
});

test("normalizeAnimalsPayload accepts valid animal data", () => {
  const result = mod.normalizeAnimalsPayload({
    animals: [
      { name: "  貝貝  ", type: "animal", emoji: "🐶", role: "導覽員", desc: "介紹", portrait: "x", photos: ["a"] },
    ],
  });
  assert.equal(result.ok, true);
  assert.equal(result.payload.animals[0].name, "貝貝");
  assert.equal(result.payload.animals[0].type, "animal");
});

test("normalizeAnimalsPayload rejects duplicate animal names", () => {
  const result = mod.normalizeAnimalsPayload({
    animals: [
      { name: "貝貝" },
      { name: " 貝貝 " },
    ],
  });
  assert.equal(result.ok, false);
  assert.match(result.error, /duplicate/i);
});

test("normalizeAnimalsPayload rejects entries without name", () => {
  const result = mod.normalizeAnimalsPayload({
    animals: [
      { name: "", type: "animal" },
      { type: "animal" },
    ],
  });
  assert.equal(result.ok, false);
  assert.match(result.error, /name/i);
});

test("s2t handles empty string", () => {
  assert.equal(mod.s2t(""), "");
});

test("s2t returns non-string input as-is", () => {
  assert.equal(mod.s2t(42), 42);
  assert.equal(mod.s2t(null), null);
});

test("s2t converts multiple characters in one string", () => {
  assert.equal(mod.s2t("榕树和柳树"), "榕樹和柳樹");
});

test("checkRateLimit allows requests within limit", () => {
  const req = new Request("https://worker/x", {
    headers: { "CF-Connecting-IP": "1.2.3.4" },
  });
  const result = mod.checkRateLimit(req);
  assert.equal(result.allowed, true);
});

test("checkRateLimit returns retryAfter when exceeded", () => {
  const req = new Request("https://worker/x", {
    headers: { "CF-Connecting-IP": "5.6.7.8" },
  });
  // Exhaust the rate limit
  for (let i = 0; i < 30; i++) {
    mod.checkRateLimit(req);
  }
  const result = mod.checkRateLimit(req);
  assert.equal(result.allowed, false);
  assert.ok(typeof result.retryAfter === "number");
  assert.ok(result.retryAfter > 0);
});

test("timingSafeEqual returns true for identical strings", () => {
  assert.equal(mod.timingSafeEqual("hello", "hello"), true);
});

test("timingSafeEqual returns false for different strings", () => {
  assert.equal(mod.timingSafeEqual("hello", "world"), false);
});

test("timingSafeEqual returns false for different lengths", () => {
  assert.equal(mod.timingSafeEqual("hello", "hello!"), false);
  assert.equal(mod.timingSafeEqual("", "a"), false);
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
