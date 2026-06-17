const PLANTNET_URL = "https://my-api.plantnet.org/v2/identify/all";
const PERENUAL_SPECIES_LIST_URL = "https://perenual.com/api/v2/species-list";
const PERENUAL_DETAILS_URL = "https://perenual.com/api/v2/species/details";
const PERENUAL_CACHE_SECONDS = 7 * 24 * 60 * 60;
const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX_REQUESTS = 30;
const RATE_LIMIT_CLEANUP_INTERVAL_MS = RATE_LIMIT_WINDOW_MS * 2; // 120 seconds
const rateLimitStore = new Map();
const inFlightPerenualRequests = new Map();

// Periodic cleanup of stale rate limit entries every 2 minutes
if (typeof fetch !== 'undefined' && typeof setInterval !== 'undefined') {
  setInterval(() => {
    const now = Date.now();
    for (const [ip, entry] of rateLimitStore) {
      if (now - entry.windowStart > RATE_LIMIT_WINDOW_MS * 3) {
        rateLimitStore.delete(ip);
      }
    }
  }, RATE_LIMIT_CLEANUP_INTERVAL_MS).unref?.();
}

// Clean up stale in-flight Perenual requests every 60 seconds
if (typeof fetch !== 'undefined' && typeof setInterval !== 'undefined') {
  setInterval(() => {
    if (inFlightPerenualRequests.size > 100) {
      const keys = [...inFlightPerenualRequests.keys()];
      for (let i = 0; i < keys.length - 50; i++) {
        inFlightPerenualRequests.delete(keys[i]);
      }
    }
  }, 60_000).unref?.();
}
const DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
const ALLOWED_IMAGE_MIME = new Set(["image/jpeg", "image/png", "image/webp"]);
const ANIMALS_KV_KEY = "animals:v1";
const MAX_ANIMALS_BYTES = 2 * 1024 * 1024;

function readMaxUploadBytes(env) {
  const raw = env && env.MAX_UPLOAD_BYTES;
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_MAX_UPLOAD_BYTES;
}

const ANIMALS_DATA = [
  {"name":"貝貝","type":"animal","emoji":"🐶","role":"溫柔導覽員","desc":"東北角的米克斯母狗，也是藝素村最溫柔的導嚮員。","portrait":"","photos":[]},
  {"name":"牧耳","type":"animal","emoji":"🐕","role":"草地巡邏員","desc":"充滿活力的夥伴，最喜歡在東北角的草地上奔跑。","portrait":"","photos":[]},
  {"name":"小飛俠","type":"animal","emoji":"🐈","role":"屋頂觀察員","desc":"身手矯健，總是在屋頂上觀察探險家們。","portrait":"","photos":[]},
  {"name":"嘿皮","type":"animal","emoji":"🐈‍⬛","role":"親人接待員","desc":"個性大方的黑貓，討摸是牠的日常。","portrait":"","photos":[]},
  {"name":"冬瓜","type":"animal","emoji":"🐱","role":"慵懶守護者","desc":"圓滾滾的橘貓，是村裡的慵懶大王。","portrait":"","photos":[]},
];

const s2tMapping = {
  "叶": "葉", "兰": "蘭", "菊": "菊", "莲": "蓮", "苹": "蘋", "萝": "蘿", "松": "松", "柏": "柏", "枫": "楓", "樱": "櫻", 
  "梅": "梅", "桂": "桂", "竹": "竹", "柳": "柳", "桐": "桐", "杉": "杉", "榆": "榆", "藤": "藤", "蓉": "蓉", "葛": "葛", 
  "苏": "蘇", "芦": "蘆", "麦": "麥", "豆": "豆", "米": "米", "茶": "茶", "药": "藥", "阳": "陽", "阴": "陰", "风": "風", 
  "云": "雲", "电": "電", "雨": "雨", "雪": "雪", "霜": "霜", "露": "露", "雾": "霧", "冰": "冰", "水": "水", "火": "火", 
  "土": "土", "金": "金", "木": "木", "华": "華", "发": "發", "长": "長", "大": "大", "小": "小", "多": "多", "少": "少", 
  "高": "高", "低": "低", "红": "紅", "黄": "黃", "蓝": "藍", "绿": "綠", "黑": "黑", "白": "白", "紫": "紫", "青": "青", 
  "灰": "灰", "粉": "粉", "褐": "褐", "无": "無", "铁": "鐵", "龙": "龍", "马": "馬", "鸟": "鳥", "鱼": "魚", "虫": "蟲", 
  "贝": "貝", "龟": "龜", "蛇": "蛇", "蛙": "蛙", "鼠": "鼠", "牛": "牛", "虎": "虎", "兔": "兔", "羊": "羊", "猴": "猴", 
  "鸡": "雞", "狗": "狗", "猪": "豬", "猫": "貓", "鸭": "鴨", "鹅": "鵝", "象": "象", "熊": "熊", "狮": "獅", "豹": "豹", 
  "狼": "狼", "狐": "狐", "鹿": "鹿", "门": "門", "观": "觀", "园": "園", "区": "區", "广": "廣", "厂": "廠", "类": "類", 
  "属": "屬", "种": "種", "网": "網", "线": "線", "条": "條", "块": "塊", "点": "點", "面": "面", "体": "體", "形": "形", 
  "状": "狀", "态": "態", "貌": "貌", "色": "色", "香": "香", "味": "味", "臭": "臭", "苦": "苦", "甜": "甜", "酸": "酸", 
  "辣": "辣", "咸": "鹹", "淡": "淡", "浓": "濃", "薄": "薄", "厚": "厚", "轻": "輕", "重": "重", "软": "軟", "硬": "硬", 
  "干": "乾", "湿": "濕", "冷": "冷", "热": "熱", "温": "溫", "凉": "涼", "寒": "寒", "暖": "暖", "明": "明", "暗": "暗", 
  "赤": "赤", "橙": "橙", "银": "銀", "铜": "銅", "锡": "錫", "铅": "鉛", "玉": "玉", "石": "石", "宝": "寶", "珠": "珠", 
  "亚": "亞", "产": "產", "双": "雙", "单": "單", "丽": "麗", "锦": "錦", "绣": "繡", "绒": "絨", "丝": "絲", "棉": "棉", 
  "麻": "麻", "毛": "毛", "皮": "皮", "骨": "骨", "肉": "肉", "血": "血", "汗": "汗", "泪": "淚", "液": "液", "汁": "汁", 
  "浆": "漿", "膏": "膏", "脂": "脂", "油": "油", "气": "氣", "雷": "雷", "光": "光", "声": "聲", "音": "音", "乐": "樂", 
  "曲": "曲", "歌": "歌", "舞": "舞", "图": "圖", "画": "畫", "书": "書", "文": "文", "字": "字", "词": "詞", "语": "語", 
  "言": "言", "论": "論", "记": "記", "传": "傳", "史": "史", "志": "志", "录": "錄", "典": "典", "籍": "籍", "册": "冊", 
  "卷": "卷", "篇": "篇", "章": "章", "节": "節", "款": "款", "项": "項", "目": "目", "科": "科", "纲": "綱", "界": "界", 
  "系": "系", "统": "統", "群": "群", "族": "族", "盘": "盤", "罗": "羅", "齿": "齒", "齐": "齊", "车": "車", "转": "轉", 
  "轮": "輪", "轴": "軸", "轨": "軌", "载": "載", "辉": "輝", "边": "邊", "过": "過", "进": "進", "远": "遠", "违": "違", 
  "连": "連", "迟": "遲", "适": "適", "选": "選", "逊": "遜", "透": "透", "递": "遞", "途": "途", "逗": "逗", "通": "通", 
  "造": "造", "速": "速", "逢": "逢", "树": "樹", "样": "樣", "根": "根", "茎": "莖", "果": "果", "桃": "桃",
  "莓": "莓", "凤": "鳳", "梨": "梨", "芒": "芒", "百": "百", "合": "合", "牵": "牽", "带": "帶",
  "蕨": "蕨", "藓": "蘚", "藻": "藻", "菌": "菌", "菇": "菇", "蕈": "蕈", "乔": "喬"
};

const _S2T_REGEX = new RegExp(
  Object.keys(s2tMapping).map(c => c.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'),
  'g'
);

function s2t(str) {
  if (typeof str !== 'string') return str;
  return str.replace(_S2T_REGEX, match => s2tMapping[match] || match);
}

// Note: The rateLimitStore Map only limits requests within a single Cloudflare Worker node (Isolate).
// For strict global rate limiting, configure WAF Rate Limiting rules in the Cloudflare Dashboard.
let lastRateLimitCleanup = 0;
function checkRateLimit(request) {
  const now = Date.now();
  if (now - lastRateLimitCleanup > RATE_LIMIT_CLEANUP_INTERVAL_MS) {
    for (const [ip, entry] of rateLimitStore) {
      if (now - entry.windowStart > RATE_LIMIT_WINDOW_MS * 3) { // Remove stale entries older than 3 windows
        rateLimitStore.delete(ip);
      }
    }
    lastRateLimitCleanup = now;
  }
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const entry = rateLimitStore.get(ip);
  if (!entry || now - entry.windowStart > RATE_LIMIT_WINDOW_MS) {
    rateLimitStore.set(ip, { windowStart: now, count: 1 });
    return { allowed: true };
  }
  entry.count++;
  if (entry.count > RATE_LIMIT_MAX_REQUESTS) {
    return { allowed: false, retryAfter: Math.ceil((RATE_LIMIT_WINDOW_MS - (now - entry.windowStart)) / 1000) };
  }
  return { allowed: true };
}

function isPagesDomainAllowed(env = {}) {
  return String(env.ALLOW_PAGES_DOMAINS || "").toLowerCase() === "true";
}

function isAllowedPagesOrigin(origin) {
  try {
    const hostname = new URL(origin).hostname;
    return hostname === "pages.dev"
      || hostname.endsWith(".pages.dev")
      || hostname === "github.io"
      || hostname.endsWith(".github.io");
  } catch {
    return false;
  }
}

function corsHeaders(request, env = {}) {
  const origin = request.headers.get("Origin") || "";
  const configuredOrigin = env.ALLOWED_ORIGIN || "";

  if (configuredOrigin && origin === configuredOrigin) {
    return origin;
  }

  const allowedOriginsStr = env.ALLOWED_ORIGINS || "";
  if (allowedOriginsStr && origin) {
    const allowedOrigins = allowedOriginsStr.split(",").map((s) => s.trim()).filter(Boolean);
    if (allowedOrigins.includes(origin)) {
      return origin;
    }
  }

  if (origin && isPagesDomainAllowed(env) && isAllowedPagesOrigin(origin)) {
    return origin;
  }

  return "null";
}

function corsHeadersMap(request, env) {
  return {
    "Access-Control-Allow-Origin": corsHeaders(request, env),
    "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, X-Admin-Password",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}

function jsonResponse(body, init, request, env) {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      ...corsHeadersMap(request, env),
      ...(init?.headers || {}),
    },
  });
}

function isFileLike(value) {
  return value && typeof value.arrayBuffer === "function" && typeof value.type === "string";
}

function normalizeAnimalsPayload(payload) {
  if (!payload || !Array.isArray(payload.animals)) {
    return { ok: false, error: "animals array is required" };
  }
  if (payload.animals.length > 100) {
    return { ok: false, error: "too many animals" };
  }

  const seenNames = new Set();
  const animals = [];
  for (const entry of payload.animals) {
    const name = String(entry?.name || "").trim();
    if (!name) {
      return { ok: false, error: "animal name is required" };
    }
    if (seenNames.has(name)) {
      return { ok: false, error: `duplicate animal name: ${name}` };
    }
    seenNames.add(name);
    animals.push({
      name,
      type: "animal",
      emoji: String(entry?.emoji || "🐾"),
      role: String(entry?.role || ""),
      desc: String(entry?.desc || ""),
      portrait: String(entry?.portrait || ""),
      photos: Array.isArray(entry?.photos) ? entry.photos.map((photo) => String(photo || "")).filter(Boolean) : [],
    });
  }

  const normalized = { animals };
  const serialized = JSON.stringify(normalized);
  if (new TextEncoder().encode(serialized).length > MAX_ANIMALS_BYTES) {
    return { ok: false, error: "animals payload is too large" };
  }
  return { ok: true, payload: normalized, serialized };
}

async function readAnimalsPayload(env) {
  if (env?.ANIMALS_KV) {
    try {
      const stored = await env.ANIMALS_KV.get(ANIMALS_KV_KEY, "json");
      const normalized = normalizeAnimalsPayload(stored);
      if (normalized.ok) {
        return { ...normalized.payload, source: "kv" };
      }
    } catch {
      // Fall back to bundled data if KV is unavailable or contains invalid data.
    }
  }
  return { animals: ANIMALS_DATA, source: "bundled" };
}

async function writeAnimalsPayload(env, payload) {
  if (!env?.ANIMALS_KV) {
    return { ok: false, status: 503, error: "ANIMALS_KV binding is not configured" };
  }
  const normalized = normalizeAnimalsPayload(payload);
  if (!normalized.ok) {
    return { ok: false, status: 400, error: normalized.error };
  }
  await env.ANIMALS_KV.put(ANIMALS_KV_KEY, normalized.serialized);
  return { ok: true, payload: normalized.payload };
}

function timingSafeEqual(a, b) {
  const bufA = new TextEncoder().encode(a);
  const bufB = new TextEncoder().encode(b);
  if (bufA.length !== bufB.length) {
    let result = bufA.length ^ bufB.length;
    for (let i = 0; i < bufA.length; i++) {
      result |= bufA[i] ^ (bufB[i % bufB.length] || 0);
    }
    return result === 0;
  }
  let result = 0;
  for (let i = 0; i < bufA.length; i++) {
    result |= bufA[i] ^ bufB[i];
  }
  return result === 0;
}

function isAnimalAdminAuthorized(request, env) {
  const expected = String(env?.ANIMALS_ADMIN_PASSWORD || "");
  if (!expected) {
    return { ok: false, status: 503, error: "ANIMALS_ADMIN_PASSWORD is not configured" };
  }
  const actual = request.headers.get("X-Admin-Password") || "";
  if (!timingSafeEqual(actual, expected)) {
    return { ok: false, status: 401, error: "Invalid animal admin password" };
  }
  return { ok: true };
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

  const normalizedName = normalizeScientificName(scientificName);
  const cacheKeyStr = `cache://perenual/${normalizedName}`;
  const cacheKey = new Request(cacheKeyStr, { method: "GET" });

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

  // Request deduplication: if there's already an in-flight request for this scientific name, wait for it
  if (inFlightPerenualRequests.has(normalizedName)) {
    try {
      const metadata = await inFlightPerenualRequests.get(normalizedName);
      return {
        metadata,
        timing: { perenual_ms: Date.now() - startedAt, perenual_cache: "deduped" },
      };
    } catch {
      // If the deduplicated request fails, fall through to make a new request
    }
  }

  // Create a promise for the in-flight request
  const fetchTimeout = setTimeout(() => {
    if (inFlightPerenualRequests.get(normalizedName) === fetchPromise) {
      inFlightPerenualRequests.delete(normalizedName);
    }
  }, 30_000);

  const fetchPromise = fetchPerenualMetadata(scientificName, env).finally(() => {
    clearTimeout(fetchTimeout);
    inFlightPerenualRequests.delete(normalizedName);
  });

  inFlightPerenualRequests.set(normalizedName, fetchPromise);

  try {
    const metadata = await fetchPromise;
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
  } finally {
    // inFlightPerenualRequests.delete(normalizedName) handled by fetchPromise.finally()
  }
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: corsHeadersMap(request, env),
      });
    }

    try {
      const rateCheck = checkRateLimit(request);
      if (!rateCheck.allowed) {
        return jsonResponse(
          { error: "Rate limit exceeded. Try again later." },
          { status: 429, headers: { "Retry-After": String(rateCheck.retryAfter) } },
          request, env,
        );
      }

      const requestUrl = new URL(request.url);

      if (requestUrl.pathname === "/animals/auth" && request.method === "POST") {
        const auth = isAnimalAdminAuthorized(request, env);
        return jsonResponse(
          { ok: auth.ok },
          { status: auth.ok ? 200 : auth.status },
          request, env,
        );
      }

      if (requestUrl.pathname === "/animals") {
        if (request.method === "GET") {
          const animalsPayload = await readAnimalsPayload(env);
          return jsonResponse(animalsPayload, { status: 200, headers: { "Cache-Control": "no-store" } }, request, env);
        }
        if (request.method === "PUT") {
          const auth = isAnimalAdminAuthorized(request, env);
          if (!auth.ok) {
            return jsonResponse({ error: auth.error }, { status: auth.status }, request, env);
          }
          const contentLengthHeader = request.headers.get("Content-Length");
          if (contentLengthHeader) {
            const contentLength = Number.parseInt(contentLengthHeader, 10);
            if (contentLength > MAX_ANIMALS_BYTES) {
              return jsonResponse({ error: "Payload too large" }, { status: 413 }, request, env);
            }
          }
          let payload;
          try {
            payload = await request.json();
          } catch {
            return jsonResponse({ error: "Invalid JSON" }, { status: 400 }, request, env);
          }
          const writeResult = await writeAnimalsPayload(env, payload);
          if (!writeResult.ok) {
            return jsonResponse({ error: writeResult.error }, { status: writeResult.status }, request, env);
          }
          return jsonResponse({ ...writeResult.payload, source: "kv" }, { status: 200 }, request, env);
        }
      }

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

      const maxUploadBytes = readMaxUploadBytes(env);
      const contentLengthHeader = request.headers.get("Content-Length");
      if (contentLengthHeader) {
        const contentLength = Number.parseInt(contentLengthHeader, 10);
        if (contentLength > maxUploadBytes) {
          return jsonResponse(
            { error: "Upload too large", max_bytes: maxUploadBytes },
            { status: 413, headers: { "Retry-After": "0" } },
            request, env,
          );
        }
      }

      const incomingForm = await request.formData();
      const image = incomingForm.get("images") || incomingForm.get("image") || incomingForm.get("file");
      const organ = String(incomingForm.get("organs") || "").toLowerCase();
      const allowedOrgans = new Set(["leaf", "flower", "fruit", "bark"]);

      if (!isFileLike(image)) {
        return jsonResponse({ error: "Missing image file" }, { status: 400 }, request, env);
      }

      if (!ALLOWED_IMAGE_MIME.has(image.type)) {
        return jsonResponse(
          { error: `Unsupported image type: ${image.type || "unknown"}`, allowed: [...ALLOWED_IMAGE_MIME] },
          { status: 415 },
          request, env,
        );
      }

      if (typeof image.size === "number" && image.size > maxUploadBytes) {
        return jsonResponse(
          { error: "Upload too large", max_bytes: maxUploadBytes },
          { status: 413, headers: { "Retry-After": "0" } },
          request, env,
        );
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

      const responseText = await response.text();
      const responseHeaders = {
        "Content-Type": response.headers.get("Content-Type") || "application/json; charset=utf-8",
        ...corsHeadersMap(request, env),
        "Server-Timing": `plantnet;dur=${plantnetMs}`,
      };

      if (!response.ok) {
        return new Response(responseText, {
          status: response.status,
          statusText: response.statusText,
          headers: responseHeaders,
        });
      }

      const plantNetPayload = JSON.parse(responseText);
      
      // Apply S2T mapping to commonNames
      if (Array.isArray(plantNetPayload.results)) {
        plantNetPayload.results.forEach(result => {
          if (result && result.species && Array.isArray(result.species.commonNames)) {
            result.species.commonNames = result.species.commonNames.map(s2t);
          }
        });
      }

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
      console.error("Worker proxy failed:", error);
      return jsonResponse(
        { error: "Worker proxy failed" },
        { status: 502 },
        request,
        env,
      );
    }
  },
};
