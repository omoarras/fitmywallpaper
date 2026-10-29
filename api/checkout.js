// GET ?pack=10|30|100 → Lemon Squeezy checkout link tied to the signed-in person.
import { getSession, json, PACKS } from "./_lib.js";

export async function GET(request) {
  const s = getSession(request);
  if (!s) return json({ error: "Please sign in first." }, 401);
  const pack = new URL(request.url).searchParams.get("pack");
  const base = PACKS[pack] && process.env[PACKS[pack]];
  if (!base) return json({ error: "That pack isn't available yet." }, 400);

  const u = new URL(base);
  u.searchParams.set("checkout[custom][user_id]", s.sub);
  if (s.email) u.searchParams.set("checkout[email]", s.email);
  if (s.name) u.searchParams.set("checkout[name]", s.name);
  return json({ url: u.toString() });
}
