const VERSION = "0.1.0";
const CATEGORIES = new Set([
  "us-residential",
  "other-residential",
  "datacenter-low-risk",
]);
const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
    },
  });
const text = (body, status = 200, contentType = "text/plain; charset=utf-8") =>
  new Response(body, {
    status,
    headers: {
      "content-type": contentType,
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
    },
  });

function isAdmin(request, env) {
  const expected = env.ADMIN_TOKEN;
  return Boolean(
    expected &&
    request.headers.get("authorization") === `Bearer ${expected}`
  );
}

function base64url(bytes) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

async function tokenKey(token) {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(token)
  );
  return `token:${base64url(new Uint8Array(digest))}`;
}

function validYamlMap(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  for (const [category, yaml] of Object.entries(value)) {
    if (!CATEGORIES.has(category) || typeof yaml !== "string") return false;
    if (yaml.length > 2_000_000) return false;
  }
  return Object.keys(value).length > 0;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (request.method === "GET" && path === "/health") {
      return json({
        ok: true,
        service: "node-finder-publisher",
        version: VERSION,
        storage: Boolean(env.NODE_FINDER_KV),
      });
    }

    if (!env.NODE_FINDER_KV) {
      return json({ error: "missing_kv_binding" }, 500);
    }

    if (request.method === "GET" && path.startsWith("/sub/")) {
      const token = path.slice("/sub/".length);
      if (!/^[A-Za-z0-9_-]{40,60}$/.test(token)) {
        return text("Not found", 404);
      }
      const category = await env.NODE_FINDER_KV.get(await tokenKey(token));
      if (!category || !CATEGORIES.has(category)) return text("Not found", 404);
      const yaml = await env.NODE_FINDER_KV.get(`published:${category}:yaml`);
      if (!yaml) return text("Subscription not published", 404);
      return text(yaml, 200, "text/yaml; charset=utf-8");
    }

    if (!isAdmin(request, env)) return json({ error: "unauthorized" }, 401);

    if (request.method === "POST" && path === "/api/v1/publish") {
      let body;
      try {
        body = await request.json();
      } catch {
        return json({ error: "invalid_json" }, 400);
      }
      if (!validYamlMap(body?.yaml)) return json({ error: "invalid_yaml_map" }, 400);

      const publishedAt = new Date().toISOString();
      for (const [category, yaml] of Object.entries(body.yaml)) {
        await env.NODE_FINDER_KV.put(`published:${category}:yaml`, yaml);
        await env.NODE_FINDER_KV.put(
          `published:${category}:meta`,
          JSON.stringify({ category, published_at: publishedAt, bytes: new TextEncoder().encode(yaml).length })
        );
      }
      return json({ ok: true, published_at: publishedAt, categories: Object.keys(body.yaml) });
    }

    if (request.method === "POST" && path === "/api/v1/tokens") {
      let body;
      try {
        body = await request.json();
      } catch {
        return json({ error: "invalid_json" }, 400);
      }
      const category = body?.category;
      if (!CATEGORIES.has(category)) return json({ error: "invalid_category" }, 400);

      const bytes = crypto.getRandomValues(new Uint8Array(32));
      const token = base64url(bytes);
      await env.NODE_FINDER_KV.put(await tokenKey(token), category);
      return json({ ok: true, category, token, path: `/sub/${token}` }, 201);
    }

    if (request.method === "DELETE" && path.startsWith("/api/v1/tokens/")) {
      const token = path.slice("/api/v1/tokens/".length);
      if (!/^[A-Za-z0-9_-]{40,60}$/.test(token)) {
        return json({ error: "invalid_token" }, 400);
      }
      await env.NODE_FINDER_KV.delete(await tokenKey(token));
      return json({ ok: true, revoked: true });
    }

    if (request.method === "GET" && path === "/api/v1/status") {
      const categories = {};
      for (const category of CATEGORIES) {
        const raw = await env.NODE_FINDER_KV.get(`published:${category}:meta`);
        categories[category] = raw ? JSON.parse(raw) : null;
      }
      return json({ ok: true, version: VERSION, categories });
    }

    return json({ error: "not_found" }, 404);
  },
};
