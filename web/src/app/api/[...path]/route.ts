import { NextRequest, NextResponse } from "next/server";

function getTargetBase(): string {
  const raw = process.env.API_ORIGIN || "https://onroad-uu9c.onrender.com";
  return /^https?:\/\//.test(raw) ? raw.replace(/\/$/, "") : `http://${raw.replace(/\/$/, "")}`;
}

async function proxy(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  const targetBase = getTargetBase();
  const targetUrl = new URL(`/api/${(path || []).join("/")}`, targetBase);

  // Preserve incoming query search params
  const incomingUrl = new URL(request.url);
  targetUrl.search = incomingUrl.search;

  // Forward incoming headers (except host, connection, content-length, accept-encoding)
  const headers = new Headers();
  request.headers.forEach((value, key) => {
    const k = key.toLowerCase();
    if (!["host", "content-length", "connection", "accept-encoding"].includes(k)) {
      headers.set(key, value);
    }
  });
  // Request uncompressed response from upstream so we can accurately measure Content-Length
  headers.set("accept-encoding", "identity");

  const method = request.method;
  const hasBody = ["POST", "PUT", "PATCH", "DELETE"].includes(method);
  let body: ArrayBuffer | undefined = undefined;
  if (hasBody) {
    try {
      body = await request.arrayBuffer();
    } catch {
      // no body
    }
  }

  try {
    const upstreamRes = await fetch(targetUrl.toString(), {
      method,
      headers,
      body,
      redirect: "manual",
      cache: "no-store",
    });

    const resData = await upstreamRes.arrayBuffer();
    const responseHeaders = new Headers();
    upstreamRes.headers.forEach((value, key) => {
      const k = key.toLowerCase();
      if (!["transfer-encoding", "content-encoding", "content-length"].includes(k)) {
        responseHeaders.set(key, value);
      }
    });

    // Explicitly set Content-Length from the full buffer size so Cloudflare / browser never prematurely terminates the body
    responseHeaders.set("Content-Length", resData.byteLength.toString());

    return new NextResponse(resData, {
      status: upstreamRes.status,
      statusText: upstreamRes.statusText,
      headers: responseHeaders,
    });
  } catch (err: unknown) {
    console.error(`[API Proxy Error] failed to proxy to ${targetUrl}:`, err);
    return NextResponse.json(
      { error: "Backend proxy unreachable", detail: err instanceof Error ? err.message : String(err) },
      { status: 502 }
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const HEAD = proxy;
export const OPTIONS = proxy;
