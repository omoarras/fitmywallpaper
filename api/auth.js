// POST {credential} from "Sign in with Google" → creates account (2 free wallpapers) and session.
import { createRemoteJWKSet, jwtVerify } from "jose";
import { db, userKey, json, sessionCookie, FREE_WALLPAPERS, getCredits } from "./_lib.js";

const JWKS = createRemoteJWKSet(new URL("https://www.googleapis.com/oauth2/v3/certs"));

async function verifyGoogle(token) {
  if (globalThis.__TEST_VERIFY_GOOGLE__) return globalThis.__TEST_VERIFY_GOOGLE__(token);
  const { payload } = await jwtVerify(token, JWKS, {
    issuer: ["https://accounts.google.com", "accounts.google.com"],
    audience: process.env.GOOGLE_CLIENT_ID,
  });
  return payload;
}

export async function POST(request) {
  try {
    const { credential } = await request.json().catch(() => ({}));
    if (!credential) return json({ error: "Sign-in failed. Please try again." }, 400);
    const g = await verifyGoogle(credential);
    if (!g?.sub || g.email_verified === false) return json({ error: "Please use a verified Google account." }, 400);

    const key = userKey(g.sub);
    // New people get their free wallpapers once; returning people keep their balance.
    const isNew = await db().hsetnx(key, "credits", FREE_WALLPAPERS);
    await db().hset(key, { email: g.email || "", name: g.name || "", ...(isNew ? { created: Date.now() } : {}) });

    const user = { sub: g.sub, email: g.email || "", name: g.given_name || g.name || "" };
    return json({ ...user, credits: await getCredits(g.sub), isNew: !!isNew }, 200, {
      "Set-Cookie": sessionCookie(user),
    });
  } catch (e) {
    console.error("auth error", e);
    return json({ error: "Sign-in failed. Please try again." }, 401);
  }
}
