import indexHTML from "./index.html";

const PORT = process.env.PORT ? Number.parseInt(process.env.PORT) : 3000;
const API_URL = process.env.API_URL || "http://localhost:8000";

async function proxyToBackend(req: Request): Promise<Response> {
  const incoming = new URL(req.url);
  const subpath = incoming.pathname.replace(/^\/api/, "") || "/";
  const target = `${API_URL}${subpath}${incoming.search}`;

  const headers = new Headers(req.headers);
  headers.delete("host");

  const body = req.method === "GET" || req.method === "HEAD" ? undefined : await req.arrayBuffer();

  try {
    return await fetch(target, {
      method: req.method,
      headers,
      body,
    });
  } catch (err) {
    console.error(`Proxy error ${req.method} ${target}:`, err);
    return new Response(JSON.stringify({ detail: "Backend unreachable" }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    });
  }
}

Bun.serve({
  port: PORT,
  routes: {
    "/": indexHTML,
    "/api": proxyToBackend,
    "/api/*": proxyToBackend,
  },
  development: {
    hmr: true,
  },
});

console.log(`Frontend running on http://localhost:${PORT}`);
console.log(`API proxy -> ${API_URL}`);
