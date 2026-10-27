import { NextRequest, NextResponse } from "next/server";

function getTargetBase(): string {
  const raw = process.env.API_ORIGIN || "https://onroad-uu9c.onrender.com";
  return /^https?:\/\//.test(raw) ? raw.replace(/\/$/, "") : `http://${raw.replace(/\/$/, "")}`;
}

async function doFetchWithRetry(
  url: string,
  init: RequestInit,
  isIdempotent: boolean
): Promise<Response> {
  const maxAttempts = isIdempotent ? 2 : 1;
  let lastError: unknown;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const res = await fetch(url, {
        ...init,
        signal: AbortSignal.timeout(60000), // 60s timeout to tolerate Render free-tier cold starts
      });

      // If Render router returns 502/503/504 while waking the container, retry once for safe methods
      if (isIdempotent && [502, 503, 504].includes(res.status) && attempt < maxAttempts) {
        await new Promise((r) => setTimeout(r, 2000));
        continue;
      }

      return res;
    } catch (err) {
      lastError = err;
      if (attempt < maxAttempts) {
        await new Promise((r) => setTimeout(r, 2000));
        continue;
      }
      throw err;
    }
  }

  throw lastError;
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

  const isIdempotent = ["GET", "HEAD"].includes(method);

  try {
    const upstreamRes = await doFetchWithRetry(
      targetUrl.toString(),
      {
        method,
        headers,
        body,
        redirect: "manual",
        cache: "no-store",
      },
      isIdempotent
    );

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
      {
        error: "Backend proxy unreachable",
        detail:
          err instanceof Error
            ? err.message
            : "The backend server is either waking up from sleep or temporarily unreachable. Please retry shortly.",
      },
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
