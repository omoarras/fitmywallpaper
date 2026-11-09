// Creem calls this after a payment (checkout.completed) or refund (refund.created).
// Verifies the creem-signature header (HMAC-SHA256 hex of the raw body), then adds/removes the pack's wallpapers.
import crypto from "node:crypto";
import { db, giveCredits, json, userKey } from "./_lib.js";

function verify(raw, sig, secret) {
  if (!sig) return false;
  const expected = crypto.createHmac("sha256", secret).update(raw).digest("hex");
  const a = Buffer.from(expected), b = Buffer.from(String(sig).trim());
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

function packOf(meta, productId) {
  const fromMeta = Number(meta?.pack || 0);
  if (fromMeta) return fromMeta;
  for (const n of [10, 30, 100]) if (process.env[`CREEM_PRODUCT_${n}`] === productId) return n;
  return 0;
}

export async function POST(request) {
  const secret = process.env.CREEM_WEBHOOK_SECRET;
  if (!secret) return json({ error: "not configured" }, 500);
  const raw = await request.text();
  if (!verify(raw, request.headers.get("creem-signature"), secret)) return json({ error: "bad signature" }, 401);

  const { eventType, object: o } = JSON.parse(raw);
  if (eventType !== "checkout.completed" && eventType !== "refund.created") return json({ ok: true, ignored: eventType });
  const refund = eventType === "refund.created";
  const meta = refund ? o?.checkout?.metadata : o?.metadata;
  const productId = refund ? (o?.checkout?.product || o?.order?.product) : (o?.product?.id || o?.order?.product);
  const orderId = o?.order?.id || o?.id;
  const userId = meta?.user_id;
  if (!userId) return json({ ok: true, ignored: "no user" });
  const amount = packOf(meta, typeof productId === "object" ? productId?.id : productId);
  if (!amount) { console.error("Unknown Creem pack", productId); return json({ error: "unknown pack" }, 400); }

  const first = await db().set(`creem:${refund ? "refund" : "order"}:${orderId}`, userId, { nx: true });
  if (!first) return json({ ok: true, duplicate: true });

  let balance = await giveCredits(userId, (refund ? -1 : 1) * amount);
  if (!refund) await db().hset(userKey(userId), { paid: "1" });
  if (balance < 0) balance = await giveCredits(userId, -balance);
  console.log(`Creem ${eventType} ${orderId}: ${refund ? -amount : amount} for ${userId} (now ${balance})`);
  return json({ ok: true });
}
