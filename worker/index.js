const PLANTNET_URL = "https://my-api.plantnet.org/v2/identify/all";
const ALLOWED_PAGES_DOMAINS = ["pages.dev", "github.io"];

function corsHeaders(request, env = {}) {
  const origin = request.headers.get("Origin") || "";
  const configuredOrigin = env.ALLOWED_ORIGIN || "";
  
  if (configuredOrigin && origin === configuredOrigin) {
    return origin;
  }
  
  try {
    const url = new URL(origin);
    const hostname = url.hostname;
    for (const domain of ALLOWED_PAGES_DOMAINS) {
      if (hostname === domain || hostname.endsWith(`.${domain}`)) {
        return origin;
      }
    }
  } catch {
    // Invalid URL, fall through to default
  }
  
  return "https://pages.dev";
}

function jsonResponse(body, init, request, env) {
  const allowOrigin = corsHeaders(request, env);
  return new Response(JSON.stringify(body), {
    ...init,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": allowOrigin,
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Max-Age": "86400",
      Vary: "Origin",
      ...(init?.headers || {}),
    },
  });
}

function isFileLike(value) {
  return value && typeof value.arrayBuffer === "function" && typeof value.type === "string";
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      const allowOrigin = corsHeaders(request, env);
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": allowOrigin,
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
          "Access-Control-Max-Age": "86400",
          Vary: "Origin",
        },
      });
    }

    try {
      if (request.method === "GET" || request.method === "HEAD") {
        return jsonResponse({ results: [] }, { status: 200 }, request, env);
      }

      if (request.method !== "POST") {
        return jsonResponse({ error: "Method not allowed" }, { status: 405 }, request, env);
      }

      if (!env.PLANTNET_API_KEY) {
        return jsonResponse({ error: "PlantNet API key is not configured" }, { status: 500 }, request, env);
      }

      const contentType = request.headers.get("Content-Type") || "";
      if (!contentType.toLowerCase().includes("multipart/form-data")) {
        return jsonResponse({ error: "Expected multipart/form-data" }, { status: 415 }, request, env);
      }

      const incomingForm = await request.formData();
      const image = incomingForm.get("images") || incomingForm.get("image") || incomingForm.get("file");

      if (!isFileLike(image)) {
        return jsonResponse({ error: "Missing image file" }, { status: 400 }, request, env);
      }

      const plantNetForm = new FormData();
      plantNetForm.append("images", image, image.name || "capture.jpg");

      const params = new URLSearchParams({
        "api-key": env.PLANTNET_API_KEY,
        lang: "zh",
        "no-reject": "true",
      });

      const response = await fetch(`${PLANTNET_URL}?${params.toString()}`, {
        method: "POST",
        headers: {
          "Accept": "application/json",
        },
        body: plantNetForm,
      });

      const allowOrigin = corsHeaders(request, env);
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: {
          "Content-Type": response.headers.get("Content-Type") || "application/json; charset=utf-8",
          "Access-Control-Allow-Origin": allowOrigin,
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
          "Access-Control-Max-Age": "86400",
          Vary: "Origin",
        },
      });
    } catch (error) {
      return jsonResponse(
        { error: "Worker proxy failed", detail: error instanceof Error ? error.message : String(error) },
        { status: 502 },
        request,
        env,
      );
    }
  },
};
