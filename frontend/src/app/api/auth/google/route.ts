import { NextRequest, NextResponse } from "next/server";

/**
 * Same-origin proxy for Google sign-in.
 *
 * The browser posts the Google ID token here; we forward it to the backend,
 * which verifies it with Google and issues the app's own JWT. Keeping this
 * server-to-server avoids CORS issues during the OAuth redirect flow.
 */

const BACKEND_URL = (
  process.env.API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "https://bizinsight-backend.onrender.com"
).replace(/\/+$/, "");

export async function POST(req: NextRequest) {
  let idToken: unknown;
  try {
    idToken = (await req.json())?.id_token;
  } catch {
    idToken = undefined;
  }

  if (typeof idToken !== "string" || !idToken) {
    return NextResponse.json({ detail: "Missing Google ID token." }, { status: 400 });
  }

  try {
    const backendRes = await fetch(`${BACKEND_URL}/api/auth/google`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id_token: idToken }),
      cache: "no-store",
      signal: AbortSignal.timeout(60_000),
    });
    const data = await backendRes.json().catch(() => ({ detail: "Unexpected response from the server." }));
    return NextResponse.json(data, { status: backendRes.status });
  } catch {
    return NextResponse.json(
      { detail: "The sign-in service is unavailable. It may be starting up — please try again shortly." },
      { status: 503 }
    );
  }
}
