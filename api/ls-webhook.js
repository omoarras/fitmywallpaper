// Lemon Squeezy calls this after a payment. Adds the bought wallpapers to the buyer's balance.
// Products must be named with their amount, e.g. "10 Wallpapers", "30 Wallpapers", "100 Wallpapers".
import crypto from "node:crypto";
import { db, giveCredits, json, userKey } from "./_lib.js";

export async function POST(request) {
  const secret = process.env.LEMONSQUEEZY_WEBHOOK_SECRET;
  if (!secret) return json({ error: "not configured" }, 500);

  const raw = await request.text();
  const expected = Buffer.from(crypto.createHmac("sha256", secret).update(raw).digest("hex"));
  const given = Buffer.from(request.headers.get("x-signature") || "");
  if (expected.length !== given.length || !crypto.timingSafeEqual(expected, given))
    return json({ error: "bad signature" }, 401);

  const body = JSON.parse(raw);
  const event = body?.meta?.event_name;
  if (event !== "order_created" && event !== "order_refunded") return json({ ok: true, ignored: event });

  const a = body.data?.attributes || {};
  const userId = body.meta?.custom_data?.user_id;
  if (!userId) return json({ ok: true, ignored: "no user" });
  if (event === "order_created" && a.status !== "paid") return json({ ok: true, ignored: "not paid" });

  const item = a.first_order_item || {};
  const qty = Number(item.quantity || 1);
  const amount = Number(String(`${item.variant_name || ""} ${item.product_name || ""}`).match(/\d+/)?.[0] || 0);
  if (!amount) {
    console.error("Could not tell pack size from product name", item);
    return json({ error: "unknown pack" }, 400);
  }

  // Only count each order (and each refund) once, even if Lemon Squeezy retries.
  const refund = event === "order_refunded";
  const first = await db().set(`${refund ? "refund" : "order"}:${body.data.id}`, userId, { nx: true });
  if (!first) return json({ ok: true, duplicate: true });

  const change = (refund ? -1 : 1) * amount * qty;
  let balance = await giveCredits(userId, change);
  if (!refund) await db().hset(userKey(userId), { paid: "1" });
  if (balance < 0) balance = await giveCredits(userId, -balance); // never below zero
  console.log(`Order ${body.data.id} ${event}: ${change} wallpapers for ${userId} (now ${balance})`);
  return json({ ok: true });
}
