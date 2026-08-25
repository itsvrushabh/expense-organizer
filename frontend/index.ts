import indexHTML from "./index.html"

const API_URL = process.env.API_URL || "http://localhost:8000"

async function proxyToBackend(req: Request): Promise<Response> {
  const incoming = new URL(req.url)
  const target = `${API_URL}${incoming.pathname.replace(/^\/api/, "")}${incoming.search}`

  const headers = new Headers(req.headers)
  headers.delete("host")

  const body =
    req.method === "GET" || req.method === "HEAD" ? undefined : await req.arrayBuffer()

  try {
    return await fetch(target, {
      method: req.method,
      headers,
      body,
    })
  } catch (err) {
    console.error(`Proxy error ${req.method} ${target}:`, err)
    return new Response(JSON.stringify({ detail: "Backend unreachable" }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    })
  }
}

Bun.serve({
  port: 3000,
  routes: {
    "/": indexHTML,
    "/api/*": proxyToBackend,
  },
  development: {
    hmr: true,
  },
})

console.log("Frontend running on http://localhost:3000")
console.log(`API proxy -> ${API_URL}`)
