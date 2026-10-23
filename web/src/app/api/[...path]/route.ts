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

  // Forward incoming headers (except host)
  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!["host", "content-length", "connection"].includes(key.toLowerCase())) {
      headers.set(key, value);
    }
  });

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

    const responseHeaders = new Headers();
    upstreamRes.headers.forEach((value, key) => {
      // Don't forward transfer-encoding or content-encoding so Next can handle streaming
      if (!["transfer-encoding", "content-encoding"].includes(key.toLowerCase())) {
        responseHeaders.set(key, value);
      }
    });

    const resData = await upstreamRes.arrayBuffer();
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
