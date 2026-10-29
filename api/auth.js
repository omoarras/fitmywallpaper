// POST {credential} from "Sign in with Google" → creates account (2 free wallpapers) and session.
import crypto from "node:crypto";
import { createRemoteJWKSet, jwtVerify } from "jose";
import { db, userKey, json, sessionCookie, FREE_WALLPAPERS, getCredits, isPaid, googleClientId } from "./_lib.js";

const JWKS = createRemoteJWKSet(new URL("https://www.googleapis.com/oauth2/v3/certs"));

async function verifyGoogle(token) {
  if (globalThis.__TEST_VERIFY_GOOGLE__) return globalThis.__TEST_VERIFY_GOOGLE__(token);
  const { payload } = await jwtVerify(token, JWKS, {
    issuer: ["https://accounts.google.com", "accounts.google.com"],
    audience: googleClientId(),
  });
  return payload;
}

const FREE_PER_NETWORK_PER_DAY = 2;
const clientIp = (req) => (req.headers.get("x-forwarded-for") || "").split(",")[0].trim() || "unknown";

// One free gift per device, and at most a few new free accounts per network per day.
async function grantFree(sub, deviceIds, ip) {
  const ids = [...new Set(deviceIds.filter(Boolean))];
  for (const id of ids) if (await db().get(`freedev:${id}`)) return false;
  const day = new Date().toISOString().slice(0, 10);
  const ipKey = `freeip:${ip}:${day}`;
  const n = await db().incr(ipKey);
  if (n === 1) await db().expire(ipKey, 60 * 60 * 48);
  if (n > FREE_PER_NETWORK_PER_DAY) return false;
  for (const id of ids) await db().set(`freedev:${id}`, sub);
  await db().hincrby(userKey(sub), "credits", FREE_WALLPAPERS);
  return true;
}

export async function POST(request) {
  try {
    const body = await request.json().catch(() => ({}));
    const { credential } = body;
    if (!credential) return json({ error: "Sign-in failed. Please try again." }, 400);
    const g = await verifyGoogle(credential);
    if (!g?.sub || g.email_verified === false) return json({ error: "Please use a verified Google account." }, 400);

    const key = userKey(g.sub);
    // New accounts start at 0; the free gift is added only if this device and network qualify.
    const isNew = await db().hsetnx(key, "credits", 0);
    await db().hset(key, { email: g.email || "", name: g.name || "", ...(isNew ? { created: Date.now() } : {}) });

    // Device id: kept both in a cookie and in the browser's storage (sent by the page).
    const cookieDev = (request.headers.get("cookie") || "").match(/(?:^|;\s*)fmw_dev=([A-Za-z0-9_-]{16,64})/)?.[1];
    const pageDev = typeof body.device === "string" && /^[A-Za-z0-9_-]{16,64}$/.test(body.device) ? body.device : null;
    const device = cookieDev || pageDev || crypto.randomUUID().replace(/-/g, "");
    let freeDenied = false;
    if (isNew) freeDenied = !(await grantFree(g.sub, [cookieDev, pageDev, device], clientIp(request)));

    const user = { sub: g.sub, email: g.email || "", name: g.given_name || g.name || "" };
    const headers = new Headers();
    headers.append("Set-Cookie", sessionCookie(user));
    headers.append("Set-Cookie", `fmw_dev=${device}; Path=/; Secure; SameSite=Lax; Max-Age=${60 * 60 * 24 * 730}`);
    return json({ ...user, device, credits: await getCredits(g.sub), paid: await isPaid(g.sub), isNew: !!isNew, freeDenied }, 200, headers);
  } catch (e) {
    console.error("auth error", e);
    return json({ error: "Sign-in failed. Please try again." }, 401);
  }
}
