// Polar calls this after a payment (order.paid) or refund (order.refunded).
// Verifies the Standard Webhooks signature, then adds/removes the pack's wallpapers.
import crypto from "node:crypto";
import { db, giveCredits, json, userKey } from "./_lib.js";

function verify(raw, h, secret) {
  const id = h.get("webhook-id"), ts = h.get("webhook-timestamp"), sigs = h.get("webhook-signature") || "";
  if (!id || !ts) return false;
  if (Math.abs(Date.now() / 1000 - Number(ts)) > 600) return false;
  // Polar's SDK signs with the secret's raw bytes; plain Standard Webhooks uses base64 after "whsec_". Accept either.
  const keys = [Buffer.from(secret, "utf8")];
  if (secret.startsWith("whsec_")) keys.push(Buffer.from(secret.slice(6), "base64"));
  const given = sigs.split(" ").map((part) => Buffer.from(part.split(",")[1] || "", "base64"));
  return keys.some((key) => {
    const expected = crypto.createHmac("sha256", key).update(`${id}.${ts}.${raw}`).digest();
    return given.some((sig) => sig.length === expected.length && crypto.timingSafeEqual(sig, expected));
  });
}

function packOf(order) {
  const fromMeta = Number(order?.metadata?.pack || 0);
  if (fromMeta) return fromMeta;
  for (const n of [10, 30, 100]) if (process.env[`POLAR_PRODUCT_${n}`] === order?.product_id) return n;
  return Number(String(order?.product?.name || "").match(/\d+/)?.[0] || 0);
}

export async function POST(request) {
  const secret = process.env.POLAR_WEBHOOK_SECRET;
  if (!secret) return json({ error: "not configured" }, 500);
  const raw = await request.text();
  if (!verify(raw, request.headers, secret)) return json({ error: "bad signature" }, 401);

  const { type, data } = JSON.parse(raw);
  if (type !== "order.paid" && type !== "order.refunded") return json({ ok: true, ignored: type });
  const userId = data?.metadata?.user_id;
  if (!userId) return json({ ok: true, ignored: "no user" });
  const amount = packOf(data);
  if (!amount) { console.error("Unknown Polar pack", data?.product_id); return json({ error: "unknown pack" }, 400); }

  const refund = type === "order.refunded";
  const first = await db().set(`polar:${refund ? "refund" : "order"}:${data.id}`, userId, { nx: true });
  if (!first) return json({ ok: true, duplicate: true });

  let balance = await giveCredits(userId, (refund ? -1 : 1) * amount);
  if (!refund) await db().hset(userKey(userId), { paid: "1" });
  if (balance < 0) balance = await giveCredits(userId, -balance);
  console.log(`Polar ${type} ${data.id}: ${refund ? -amount : amount} for ${userId} (now ${balance})`);
  return json({ ok: true });
}
