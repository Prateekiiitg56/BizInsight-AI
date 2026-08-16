import { NextRequest, NextResponse } from "next/server";

/**
 * Proxy Google auth requests through Vercel to the Render backend.
 * This eliminates ALL CORS issues because the browser only talks
 * to the same Vercel origin (same-origin = no CORS).
 * Vercel → Render is server-to-server (no CORS applies).
 *
 * Also handles Render free-tier cold starts with a retry mechanism.
 */

const BACKEND_URL = (
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"
).replace(/\/+$/, "");

async function fetchWithRetry(
  url: string,
  options: RequestInit,
  retries = 3,
  delayMs = 3000
): Promise<Response> {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url, options);
      // 503 = Render is waking up from hibernation, retry
      if (res.status === 503 && i < retries - 1) {
        await new Promise((r) => setTimeout(r, delayMs));
        continue;
      }
      return res;
    } catch (err) {
      if (i < retries - 1) {
        await new Promise((r) => setTimeout(r, delayMs));
        continue;
      }
      throw err;
    }
  }
  return fetch(url, options);
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    const backendRes = await fetchWithRetry(
      `${BACKEND_URL}/api/auth/google`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
      3,
      3000
    );

    // Read response as text first to handle non-JSON responses
    const responseText = await backendRes.text();

    let data: any;
    try {
      data = JSON.parse(responseText);
    } catch {
      // Backend returned non-JSON (e.g. HTML error page from Render)
      return NextResponse.json(
        {
          detail: `Backend returned non-JSON response (status ${backendRes.status}). The server may still be starting up — please try again in 30 seconds.`,
        },
        { status: 502 }
      );
    }

    return NextResponse.json(data, { status: backendRes.status });
  } catch (error: any) {
    return NextResponse.json(
      {
        detail: `Cannot reach backend: ${error.message || "Unknown error"}. The server may be starting up — please try again in 30 seconds.`,
      },
      { status: 502 }
    );
  }
}
