// Owner-only scratch store for marketing renders (expires after 1 hour).
import { getSession, db, json, OWNERS } from "./_lib.js";

export async function POST(request) {
  const s = getSession(request);
  if (!s || !OWNERS().includes(String(s.email).toLowerCase())) return json({ error: "forbidden" }, 403);
  const { k, image } = await request.json().catch(() => ({}));
  if (!/^[\w-]{1,40}$/.test(k || "") || !/^data:image\/(webp|png|jpeg);base64,/.test(image || "")) return json({ error: "bad input" }, 400);
  await db().set(`tmp:${k}`, image, { ex: 3600 });
  return json({ ok: true });
}

export async function GET(request) {
  const k = new URL(request.url).searchParams.get("k") || "";
  if (!/^[\w-]{1,40}$/.test(k)) return new Response("bad", { status: 400 });
  const d = await db().get(`tmp:${k}`);
  if (!d) return new Response("gone", { status: 404 });
  const mime = d.slice(5, d.indexOf(";"));
  return new Response(Buffer.from(d.split(",")[1], "base64"), { headers: { "Content-Type": mime, "Cache-Control": "no-store", "X-Robots-Tag": "noindex" } });
}
