const PLANTNET_URL = "https://my-api.plantnet.org/v2/identify/all";
const PERENUAL_SPECIES_LIST_URL = "https://perenual.com/api/v2/species-list";
const PERENUAL_DETAILS_URL = "https://perenual.com/api/v2/species/details";
const ALLOWED_PAGES_DOMAINS = ["pages.dev", "github.io"];
const PERENUAL_CACHE_SECONDS = 7 * 24 * 60 * 60;

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
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
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

function topScientificName(plantNetPayload) {
  const result = plantNetPayload?.results?.[0] || {};
  const species = result.species || {};
  return species.scientificNameWithoutAuthor || species.scientificName || "";
}

function normalizeScientificName(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

function bestPerenualMatch(items, scientificName) {
  if (!Array.isArray(items) || items.length === 0) {
    return null;
  }
  const target = normalizeScientificName(scientificName);
  return (
    items.find((item) => {
      const names = Array.isArray(item.scientific_name) ? item.scientific_name : [item.scientific_name];
      return names.some((name) => normalizeScientificName(name) === target);
    }) || items[0]
  );
}

function normalizePerenualDetails(details, query) {
  return {
    status: "ok",
    source: "Perenual",
    query,
    id: details.id,
    common_name: details.common_name || "",
    scientific_name: Array.isArray(details.scientific_name) ? details.scientific_name[0] || "" : details.scientific_name || "",
    family: details.family || "",
    description: details.description || "",
    cycle: details.cycle || "",
    watering: details.watering || "",
    sunlight: Array.isArray(details.sunlight) ? details.sunlight : [],
    care_level: details.care_level || "",
    poisonous_to_humans: typeof details.poisonous_to_humans === "boolean" ? details.poisonous_to_humans : null,
    poisonous_to_pets: typeof details.poisonous_to_pets === "boolean" ? details.poisonous_to_pets : null,
    invasive: typeof details.invasive === "boolean" ? details.invasive : null,
  };
}

async function fetchPerenualMetadata(scientificName, env) {
  if (!scientificName) {
    return { status: "missing_scientific_name", source: "Perenual" };
  }
  if (!env.PERENUAL_API_KEY) {
    return { status: "not_configured", source: "Perenual", query: scientificName };
  }

  try {
    const searchParams = new URLSearchParams({
      key: env.PERENUAL_API_KEY,
      q: scientificName,
    });
    const listResponse = await fetch(`${PERENUAL_SPECIES_LIST_URL}?${searchParams.toString()}`, {
      headers: { Accept: "application/json" },
    });
    if (!listResponse.ok) {
      return { status: "lookup_failed", source: "Perenual", query: scientificName };
    }
    const listPayload = await listResponse.json();
    const match = bestPerenualMatch(listPayload.data, scientificName);
    if (!match?.id) {
      return { status: "not_found", source: "Perenual", query: scientificName };
    }

    const detailsParams = new URLSearchParams({ key: env.PERENUAL_API_KEY });
    const detailsResponse = await fetch(`${PERENUAL_DETAILS_URL}/${match.id}?${detailsParams.toString()}`, {
      headers: { Accept: "application/json" },
    });
    if (!detailsResponse.ok) {
      return { status: "details_failed", source: "Perenual", query: scientificName, id: match.id };
    }
    return normalizePerenualDetails(await detailsResponse.json(), scientificName);
  } catch (error) {
    return {
      status: "error",
      source: "Perenual",
      query: scientificName,
      detail: error instanceof Error ? error.message : String(error),
    };
  }
}

async function fetchPerenualMetadataCached(scientificName, env) {
  const startedAt = Date.now();
  if (!scientificName) {
    return {
      metadata: { status: "missing_scientific_name", source: "Perenual" },
      timing: { perenual_ms: Date.now() - startedAt },
    };
  }
  if (!env.PERENUAL_API_KEY) {
    return {
      metadata: { status: "not_configured", source: "Perenual", query: scientificName },
      timing: { perenual_ms: Date.now() - startedAt },
    };
  }

  const cacheUrl = new URL("https://art-village-metadata-cache.local/perenual");
  cacheUrl.searchParams.set("scientificName", normalizeScientificName(scientificName));
  const cacheKey = new Request(cacheUrl.toString(), { method: "GET" });

  try {
    const cachedResponse = await caches.default.match(cacheKey);
    if (cachedResponse) {
      const cached = await cachedResponse.json();
      return {
        metadata: { ...cached, status: "cached", source: cached.source || "Perenual" },
        timing: { perenual_ms: Date.now() - startedAt, perenual_cache: "hit" },
      };
    }
  } catch {
    // Cache is an optimization; metadata lookup should still work if it fails.
  }

  const metadata = await fetchPerenualMetadata(scientificName, env);
  if (metadata.status === "ok") {
    try {
      await caches.default.put(
        cacheKey,
        new Response(JSON.stringify(metadata), {
          headers: {
            "Content-Type": "application/json; charset=utf-8",
            "Cache-Control": `public, max-age=${PERENUAL_CACHE_SECONDS}`,
          },
        }),
      );
    } catch {
      // Ignore cache write failures and return the fresh metadata.
    }
  }

  return {
    metadata,
    timing: { perenual_ms: Date.now() - startedAt, perenual_cache: "miss" },
  };
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      const allowOrigin = corsHeaders(request, env);
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": allowOrigin,
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
          "Access-Control-Max-Age": "86400",
          Vary: "Origin",
        },
      });
    }

    try {
      const requestUrl = new URL(request.url);

      if (request.method === "GET" && requestUrl.pathname === "/metadata") {
        const totalStartedAt = Date.now();
        const scientificName = requestUrl.searchParams.get("scientificName") || "";
        const { metadata, timing } = await fetchPerenualMetadataCached(scientificName, env);
        return jsonResponse(
          {
            ...metadata,
            timing: {
              ...timing,
              total_ms: Date.now() - totalStartedAt,
            },
          },
          {
            status: scientificName ? 200 : 400,
            headers: {
              "Cache-Control": metadata.status === "cached" || metadata.status === "ok"
                ? `public, max-age=${PERENUAL_CACHE_SECONDS}`
                : "no-store",
            },
          },
          request,
          env,
        );
      }

      if (request.method === "GET" || request.method === "HEAD") {
        return jsonResponse(
          { error: "App version expired. Refresh the page before identifying plants." },
          { status: 426 },
          request,
          env,
        );
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
      const organ = String(incomingForm.get("organs") || "").toLowerCase();
      const allowedOrgans = new Set(["leaf", "flower", "fruit", "bark"]);

      if (!isFileLike(image)) {
        return jsonResponse({ error: "Missing image file" }, { status: 400 }, request, env);
      }

      const plantNetForm = new FormData();
      if (allowedOrgans.has(organ)) {
        plantNetForm.append("organs", organ);
      }
      plantNetForm.append("images", image, image.name || "capture.jpg");

      const params = new URLSearchParams({
        "api-key": env.PLANTNET_API_KEY,
        lang: "zh",
      });

      const totalStartedAt = Date.now();
      const plantNetStartedAt = Date.now();
      const response = await fetch(`${PLANTNET_URL}?${params.toString()}`, {
        method: "POST",
        headers: {
          "Accept": "application/json",
        },
        body: plantNetForm,
      });
      const plantnetMs = Date.now() - plantNetStartedAt;

      const allowOrigin = corsHeaders(request, env);
      const responseText = await response.text();
      const responseHeaders = {
        "Content-Type": response.headers.get("Content-Type") || "application/json; charset=utf-8",
        "Access-Control-Allow-Origin": allowOrigin,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400",
        "Server-Timing": `plantnet;dur=${plantnetMs}`,
        Vary: "Origin",
      };

      if (!response.ok) {
        return new Response(responseText, {
          status: response.status,
          statusText: response.statusText,
          headers: responseHeaders,
        });
      }

      const plantNetPayload = JSON.parse(responseText);
      const scientificName = topScientificName(plantNetPayload);
      plantNetPayload.perenual = env.PERENUAL_API_KEY && scientificName
        ? { status: "pending", source: "Perenual", query: scientificName }
        : { status: env.PERENUAL_API_KEY ? "missing_scientific_name" : "not_configured", source: "Perenual", query: scientificName };
      plantNetPayload.timing = {
        plantnet_ms: plantnetMs,
        perenual_ms: 0,
        total_ms: Date.now() - totalStartedAt,
      };

      return new Response(JSON.stringify(plantNetPayload), {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
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
