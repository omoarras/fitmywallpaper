// GET ?pack=10|30|100 → checkout link tied to the signed-in person.
// Uses Polar when POLAR_ACCESS_TOKEN + POLAR_PRODUCT_<n> are set, otherwise Lemon Squeezy.
import { getSession, json, checkoutLink } from "./_lib.js";

const POLAR_API = () => (process.env.POLAR_SERVER === "sandbox" ? "https://sandbox-api.polar.sh" : "https://api.polar.sh");

export async function GET(request) {
  const s = getSession(request);
  if (!s) return json({ error: "Please sign in first." }, 401);
  const pack = new URL(request.url).searchParams.get("pack");

  const polarProduct = process.env[`POLAR_PRODUCT_${pack}`];
  if (process.env.POLAR_ACCESS_TOKEN && polarProduct) {
    const r = await fetch(`${POLAR_API()}/v1/checkouts/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${process.env.POLAR_ACCESS_TOKEN}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        products: [polarProduct],
        customer_email: s.email || undefined,
        customer_name: s.name || undefined,
        metadata: { user_id: s.sub, pack: String(pack) },
        success_url: "https://www.pawlowallpaper.com/thanks/?checkout_id={CHECKOUT_ID}",
      }),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok || !j.url) {
      console.error("Polar checkout failed", r.status, JSON.stringify(j).slice(0, 500));
      return json({ error: "Checkout is busy, please try again in a minute." }, 502);
    }
    return json({ url: j.url });
  }

  const base = checkoutLink(pack);
  if (!base) return json({ error: "That pack isn't available yet." }, 400);
  const u = new URL(base);
  u.searchParams.set("checkout[custom][user_id]", s.sub);
  if (s.email) u.searchParams.set("checkout[email]", s.email);
  if (s.name) u.searchParams.set("checkout[name]", s.name);
  return json({ url: u.toString() });
}
