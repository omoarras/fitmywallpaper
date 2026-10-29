// Shared helpers (files starting with "_" are not public endpoints on Vercel).
import crypto from "node:crypto";
import { Redis } from "@upstash/redis";

export const FREE_WALLPAPERS = 2;
// Google sign-in Client ID (public). Can be overridden with GOOGLE_CLIENT_ID env var.
export const googleClientId = () =>
  process.env.GOOGLE_CLIENT_ID || "520588086441-dm9obqt9m24hopbrlouaiqfivcouedds.apps.googleusercontent.com";
export const COST = { standard: 1, ultra: 3 };
// Lemon Squeezy checkout links (public). Can be overridden with LS_CHECKOUT_10/30/100 env vars.
const LS = "https://fit-my-wallpaper.lemonsqueezy.com/checkout/buy/";
const DEFAULT_LINKS = {
  10: LS + "946c4624-dbe1-4c02-ac58-d9bbb3021c06",
  30: LS + "b46fb86e-ec28-42bf-bd24-6967a7bbf68a",
  100: LS + "bb07b64f-bf87-487d-94cc-541f0dc024a4",
};
export const PACKS = { 10: "LS_CHECKOUT_10", 30: "LS_CHECKOUT_30", 100: "LS_CHECKOUT_100" };
export const checkoutLink = (n) => (PACKS[n] && (process.env[PACKS[n]] || DEFAULT_LINKS[n])) || null;

export const json = (data, status = 200, headers = {}) => {
  const h = new Headers(headers);
  h.set("Content-Type", "application/json");
  h.set("Cache-Control", "no-store");
  return new Response(JSON.stringify(data), { status, headers: h });
};

// ---------- Database (Upstash Redis, added from Vercel Storage) ----------
let _redis = globalThis.__TEST_REDIS__ || null;
export function db() {
  if (_redis) return _redis;
  const url = process.env.UPSTASH_REDIS_REST_URL || process.env.KV_REST_API_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN || process.env.KV_REST_API_TOKEN;
  if (!url || !token) throw new Error("Database is not connected yet.");
  _redis = new Redis({ url, token });
  return _redis;
}

export const userKey = (sub) => `user:${sub}`;

export async function getCredits(sub) {
  const v = await db().hget(userKey(sub), "credits");
  return Number(v || 0);
}

// Atomically take credits; returns new balance, or null if not enough.
export async function takeCredits(sub, n) {
  const left = await db().hincrby(userKey(sub), "credits", -n);
  if (left < 0) {
    await db().hincrby(userKey(sub), "credits", n);
    return null;
  }
  return left;
}

export const giveCredits = (sub, n) => db().hincrby(userKey(sub), "credits", n);

// Owner accounts: always topped up, Ultra 4K unlocked, no mark. Add more with OWNER_EMAILS (comma-separated).
const OWNERS = () => (process.env.OWNER_EMAILS || "omarmohfuture@gmail.com").toLowerCase().split(",").map((e) => e.trim()).filter(Boolean);
export async function ownerTopUp(sub, email) {
  if (!email || !OWNERS().includes(String(email).toLowerCase())) return;
  const key = userKey(sub);
  await db().hset(key, { paid: "1" });
  const c = Number((await db().hget(key, "credits")) || 0);
  if (c < 20) await db().hincrby(key, "credits", 100 - c);
}

// "Paid" = has bought at least one pack; unlocks Ultra 4K.
export async function isPaid(sub) {
  return String((await db().hget(userKey(sub), "paid")) || "") === "1";
}

// ---------- Sessions (signed cookie, 30 days) ----------
const COOKIE = "fmw_session";
const MAX_AGE = 60 * 60 * 24 * 30;

function secret() {
  const s = process.env.SESSION_SECRET || process.env.OPENAI_API_KEY || process.env.OPEN_API_KEY;
  if (!s) throw new Error("Server is missing its secret.");
  return crypto.createHash("sha256").update("fmw-session:" + s).digest();
}
const b64u = (buf) => Buffer.from(buf).toString("base64url");
const sign = (data) => crypto.createHmac("sha256", secret()).update(data).digest("base64url");

export function sessionCookie(user) {
  const payload = b64u(JSON.stringify({ ...user, exp: Math.floor(Date.now() / 1000) + MAX_AGE }));
  const value = `${payload}.${sign(payload)}`;
  return `${COOKIE}=${value}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${MAX_AGE}`;
}
export const clearCookie = () => `${COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`;

export function getSession(request) {
  const raw = request.headers.get("cookie") || "";
  const m = raw.match(new RegExp(`(?:^|;\\s*)${COOKIE}=([^;]+)`));
  if (!m) return null;
  const [payload, sig] = m[1].split(".");
  if (!payload || !sig) return null;
  const good = Buffer.from(sign(payload));
  const given = Buffer.from(sig);
  if (good.length !== given.length || !crypto.timingSafeEqual(good, given)) return null;
  try {
    const s = JSON.parse(Buffer.from(payload, "base64url").toString());
    if (!s.sub || s.exp < Date.now() / 1000) return null;
    return s;
  } catch {
    return null;
  }
}
