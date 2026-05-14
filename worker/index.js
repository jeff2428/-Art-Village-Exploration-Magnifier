const PLANTNET_URL = "https://my-api.plantnet.org/v2/identify/all";
const ALLOWED_ORIGIN_RE = /^https:\/\/[a-z0-9-]+\.github\.io$/i;

function corsHeaders(request) {
  const origin = request.headers.get("Origin") || "";
  const allowOrigin = ALLOWED_ORIGIN_RE.test(origin) ? origin : "https://github.io";

  return {
    "Access-Control-Allow-Origin": allowOrigin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}

function jsonResponse(body, init, request) {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      ...corsHeaders(request),
      ...(init?.headers || {}),
    },
  });
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: corsHeaders(request),
      });
    }

    if (request.method !== "POST") {
      return jsonResponse({ error: "Method not allowed" }, { status: 405 }, request);
    }

    if (!env.PLANTNET_API_KEY) {
      return jsonResponse({ error: "PlantNet API key is not configured" }, { status: 500 }, request);
    }

    const contentType = request.headers.get("Content-Type") || "";
    if (!contentType.toLowerCase().includes("multipart/form-data")) {
      return jsonResponse({ error: "Expected multipart/form-data" }, { status: 415 }, request);
    }

    const incomingForm = await request.formData();
    const image = incomingForm.get("images") || incomingForm.get("image") || incomingForm.get("file");

    if (!(image instanceof File)) {
      return jsonResponse({ error: "Missing image file" }, { status: 400 }, request);
    }

    const plantNetForm = new FormData();
    plantNetForm.append("images", image, image.name || "capture.jpg");

    const response = await fetch(`${PLANTNET_URL}?api-key=${encodeURIComponent(env.PLANTNET_API_KEY)}&lang=zh`, {
      method: "POST",
      body: plantNetForm,
    });

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: {
        "Content-Type": response.headers.get("Content-Type") || "application/json; charset=utf-8",
        ...corsHeaders(request),
      },
    });
  },
};
