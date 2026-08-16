import { NextRequest, NextResponse } from "next/server";

/**
 * FULL Google authentication handled entirely on Vercel.
 *
 * Flow:
 * 1. Browser sends Google ID token to this route (same-origin, no CORS)
 * 2. This route verifies the token with Google's tokeninfo API
 * 3. This route tries the backend's /api/auth/google endpoint
 * 4. If backend is down/broken, generates JWT directly using the same
 *    secret as the backend and creates user on next available opportunity
 *
 * This ensures Google Sign-In works even when Render is sleeping/crashing.
 */

const BACKEND_URL = (
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"
).replace(/\/+$/, "");

const JWT_SECRET =
  process.env.JWT_SECRET || "bizinsight-dev-secret-change-in-production";

// Simple JWT generation compatible with the Python backend (PyJWT HS256)
async function createJWT(payload: Record<string, any>): Promise<string> {
  const header = { alg: "HS256", typ: "JWT" };

  const base64url = (data: string) =>
    btoa(data).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

  const encodedHeader = base64url(JSON.stringify(header));
  const encodedPayload = base64url(JSON.stringify(payload));
  const signingInput = `${encodedHeader}.${encodedPayload}`;

  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(JWT_SECRET),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );

  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(signingInput)
  );

  const encodedSignature = btoa(
    Array.from(new Uint8Array(signature))
      .map((b) => String.fromCharCode(b))
      .join("")
  )
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");

  return `${signingInput}.${encodedSignature}`;
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const idToken = body.id_token;

    if (!idToken) {
      return NextResponse.json(
        { detail: "Missing id_token in request body." },
        { status: 400 }
      );
    }

    // Step 1: Verify the Google ID token using Google's public API
    const googleRes = await fetch(
      `https://oauth2.googleapis.com/tokeninfo?id_token=${idToken}`,
      { method: "GET" }
    );

    if (!googleRes.ok) {
      return NextResponse.json(
        { detail: "Google token verification failed. Please try again." },
        { status: 401 }
      );
    }

    const googleData = await googleRes.json();

    // Step 2: Validate the token data
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";
    if (clientId && googleData.aud !== clientId) {
      return NextResponse.json(
        { detail: "Token was not issued for this application." },
        { status: 401 }
      );
    }

    const email = googleData.email;
    const name = googleData.name || email?.split("@")[0] || "user";
    const emailVerified =
      googleData.email_verified === "true" ||
      googleData.email_verified === true;

    if (!email) {
      return NextResponse.json(
        { detail: "Google account has no email." },
        { status: 400 }
      );
    }

    if (!emailVerified) {
      return NextResponse.json(
        { detail: "Google email is not verified." },
        { status: 400 }
      );
    }

    // Step 3: Try the backend's Google auth endpoint first
    try {
      const backendRes = await fetch(`${BACKEND_URL}/api/auth/google`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_token: idToken }),
      });

      if (backendRes.ok) {
        const data = await backendRes.json();
        return NextResponse.json(data, { status: 200 });
      }
      // If backend fails, fall through to Step 4
    } catch {
      // Backend unreachable, fall through to Step 4
    }

    // Step 4: Backend is down or broken — generate JWT directly
    // This JWT is compatible with the backend's PyJWT HS256 verification
    const now = Math.floor(Date.now() / 1000);
    const token = await createJWT({
      user_id: 0, // Will be resolved on next backend call
      username: name,
      role: "user",
      email: email,
      exp: now + 24 * 60 * 60, // 24 hours
      iat: now,
      google_user: true, // Flag for the backend to know this is a Google user
    });

    return NextResponse.json({
      token,
      user: {
        id: 0,
        username: name,
        email: email,
        role: "user",
      },
    });
  } catch (error: any) {
    return NextResponse.json(
      {
        detail: `Authentication error: ${error.message || "Unknown error"}`,
      },
      { status: 500 }
    );
  }
}
