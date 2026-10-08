const NONCE_KEY = "bizinsight_google_nonce";

export const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

function randomNonce(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

/** Redirect to Google's OAuth consent screen (implicit ID-token flow). */
export function startGoogleSignIn(): void {
  const nonce = randomNonce();
  sessionStorage.setItem(NONCE_KEY, nonce);
  const params = new URLSearchParams({
    client_id: GOOGLE_CLIENT_ID,
    redirect_uri: window.location.origin,
    response_type: "id_token",
    scope: "openid email profile",
    prompt: "select_account",
    nonce,
  });
  window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const part = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(part.padEnd(part.length + ((4 - (part.length % 4)) % 4), "=")));
  } catch {
    return null;
  }
}

export type GoogleRedirectResult = { idToken: string } | { error: string } | null;

/**
 * Read (and clear) a Google OAuth response from the URL fragment.
 * Returns null when the page wasn't reached via a Google redirect.
 */
export function consumeGoogleRedirect(): GoogleRedirectResult {
  const hash = window.location.hash;
  if (!hash.includes("id_token=") && !hash.includes("error=")) return null;

  const params = new URLSearchParams(hash.slice(1));
  window.history.replaceState(null, "", window.location.pathname + window.location.search);

  const expectedNonce = sessionStorage.getItem(NONCE_KEY);
  sessionStorage.removeItem(NONCE_KEY);

  if (params.get("error")) {
    return { error: params.get("error") === "access_denied" ? "Google sign-in was cancelled." : "Google sign-in failed." };
  }

  const idToken = params.get("id_token");
  if (!idToken) return { error: "Google sign-in failed." };

  const payload = decodeJwtPayload(idToken);
  if (!expectedNonce || payload?.nonce !== expectedNonce) {
    return { error: "Google sign-in could not be verified. Please try again." };
  }
  return { idToken };
}
