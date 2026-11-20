const VERSION = "0.1.1";
const json = (data, status = 200) => new Response(JSON.stringify(data), {status, headers: {"content-type":"application/json; charset=utf-8","cache-control":"no-store"}});
const unauthorized = () => json({error:"unauthorized"}, 401);
function authorized(request, env) {
  const expected = env.ADMIN_TOKEN;
  return Boolean(expected && request.headers.get("authorization") === "Bearer " + expected);
}
async function snapshot(env) {
  const raw = await env.NODES.get("snapshot");
  if (!raw) return {schema_version:1, generated_at:null, count:0, nodes:[]};
  try { return JSON.parse(raw); } catch { return {schema_version:1, generated_at:null, count:0, nodes:[]}; }
}
export default {
  async fetch(request, env) {
    const url = new URL(request.url), path = url.pathname;
    if (request.method === "GET" && path === "/api/status")
      return json({ok:true, service:"AimiliVPN-NV", version:VERSION, storage:Boolean(env.NODES)});
    if (!authorized(request, env)) return unauthorized();
    if (!env.NODES) return json({error:"KV binding NODES is missing"}, 500);
    if (request.method === "GET" && path === "/api/nodes") {
      const data = await snapshot(env), protocol = url.searchParams.get("protocol");
      const nodes = protocol ? data.nodes.filter(n => n.protocol === protocol) : data.nodes;
      return json({...data, nodes, count:nodes.length});
    }
    if (request.method === "GET" && path.startsWith("/api/nodes/")) {
      const id = decodeURIComponent(path.slice("/api/nodes/".length));
      const data = await snapshot(env), node = data.nodes.find(n => n.id === id);
      return node ? json(node) : json({error:"not_found"}, 404);
    }
    if (request.method === "GET" && path === "/api/stats") {
      const data = await snapshot(env), byProtocol = {}, byStatus = {};
      for (const n of data.nodes) {
        byProtocol[n.protocol] = (byProtocol[n.protocol] || 0) + 1;
        byStatus[n.status] = (byStatus[n.status] || 0) + 1;
      }
      return json({count:data.nodes.length, generated_at:data.generated_at, by_protocol:byProtocol, by_status:byStatus});
    }
    if (request.method === "GET" && path === "/api/config")
      return json({protocols:["openvpn","sstp","softether","l2tp_ipsec"], implemented_sources:["vpngate_openvpn"], tunnel_gateway:false});
    if (request.method === "GET" && path === "/api/subscription") return json(await snapshot(env));
    if (request.method === "POST" && path === "/api/refresh") {
      await env.NODES.put("refresh_requested_at", new Date().toISOString());
      return json({accepted:true, note:"GitHub Actions performs collection; this Worker is not a VPN gateway."}, 202);
    }
    if (request.method === "POST" && path === "/api/nodes/import") {
      let body;
      try { body = await request.json(); } catch { return json({error:"invalid_json"}, 400); }
      if (!body || !Array.isArray(body.nodes) || body.nodes.length > 5000) return json({error:"invalid_snapshot"}, 400);
      const allowed = new Set(["openvpn","sstp","softether","l2tp_ipsec"]);
      for (const n of body.nodes) {
        if (!n || typeof n.id !== "string" || !allowed.has(n.protocol) || !n.endpoint ||
            typeof n.endpoint.host !== "string" || !Number.isInteger(n.endpoint.port) ||
            n.endpoint.port < 1 || n.endpoint.port > 65535)
          return json({error:"invalid_node", node_id:n && n.id}, 400);
      }
      const data = {schema_version:1, source:body.source || "github-actions",
        generated_at:body.generated_at || new Date().toISOString(), count:body.nodes.length, nodes:body.nodes};
      await env.NODES.put("snapshot", JSON.stringify(data));
      await env.NODES.put("last_import_at", data.generated_at);
      return json({ok:true, count:data.count, generated_at:data.generated_at});
    }
    return json({error:"not_found"}, 404);
  }
};
