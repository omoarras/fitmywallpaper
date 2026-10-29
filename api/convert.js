// POST {image, width, height, quality:"standard"|"ultra"} → wallpaper. Uses the person's wallpaper balance.
import { getSession, takeCredits, giveCredits, isPaid, ownerTopUp, json, COST, db, userKey } from "./_lib.js";

const MODEL = process.env.OPENAI_IMAGE_MODEL || "gpt-image-2";
const QUALITY = { standard: "medium", ultra: "high" };

// gpt-image-2 rules: long edge <= 3840, sides multiple of 16, ratio <= 3:1, <= 8,294,400 pixels.
export function generationSize(w, h) {
  const long = Math.max(w, h), short = Math.min(w, h);
  if (long / short > 3) throw new Error("That shape is too extreme (max 3:1).");
  const scale = Math.min(3840 / long, Math.sqrt(8_294_400 / (w * h)));
  const r16 = (v) => Math.max(16, Math.floor((v * scale) / 16) * 16);
  return [r16(w), r16(h)];
}

// The user's "Universal Composition-Locked Wallpaper Prompt (v1)", with the size filled in per screen.
function ratioText(w, h) {
  const g = (a, b) => (b ? g(b, a % b) : a);
  const d = g(w, h), a = w / d, b = h / d;
  if (a <= 32 && b <= 32) return `${a}:${b}`;
  return w >= h ? `${(w / h * 9).toFixed(1).replace(/\.0$/, "")}:9` : `9:${(h / w * 9).toFixed(1).replace(/\.0$/, "")}`;
}
// "Universal Composition-Locked Wallpaper Prompt (v1)" + Composition Lock, size filled in per screen.
function buildPrompt(w, h) {
  const orient = w > h ? "landscape" : w < h ? "portrait" : "square";
  const r = ratioText(w, h);
  return `Convert this image into a ${w}×${h} (${r}) ${orient} wallpaper while preserving the exact visual composition of the original image. Composition is the highest priority. The apparent crop, framing, camera position, focal length, perspective, subject placement, subject size, and visual balance must remain identical. The final image should look like the original photograph simply exists on a wider canvas—not like the camera moved, zoomed, or revealed more of the scene.
Do NOT zoom out. Do NOT widen the field of view. Do NOT reveal additional portions of objects or the environment. Do NOT reposition or resize any existing element. The visible area of every object should remain visually identical to the original.
Adapt the image to ${w}×${h} by reconstructing only what is absolutely necessary to preserve the original composition at the new aspect ratio. Any generated content must seamlessly continue existing textures, lighting, reflections, shadows, colors, grain, and geometry without attracting attention or altering the scene.
Treat the original composition as locked. If preserving the composition conflicts with showing more of the environment, always preserve the composition.
Output a sharp native ${w}×${h} image with identical color grading, contrast, noise, sharpness, and lighting. The viewer should perceive the exact same photograph, only reformatted to ${r}, with no visible AI edits or composition changes.

Composition Lock: 100%
- Camera locked.
- Lens locked.
- Perspective locked.
- Crop perception locked.
- Subject scale locked.
- Subject positions locked.
- Visual balance locked.
- No zoom.
- No pan.
- No camera movement.
- No additional scene revealed.
- Preserve the original image exactly; only adapt it to the target aspect ratio.`;
}

export async function POST(request) {
  const key = process.env.OPENAI_API_KEY || process.env.OPEN_API_KEY;
  if (!key) return json({ error: "Server is missing its API key." }, 500);

  const s = getSession(request);
  if (!s) return json({ error: "Please sign in to make a wallpaper.", needLogin: true }, 401);

  let body;
  try { body = await request.json(); } catch { return json({ error: "Please choose a photo." }, 400); }
  const { image, width, height } = body || {};
  const mask = typeof body?.mask === "string" && body.mask.startsWith("data:image/png;base64,") && body.mask.length < 4_000_000 ? body.mask : null;
  const tier = body?.quality === "ultra" ? "ultra" : "standard";
  const w = Math.round(Number(width)), h = Math.round(Number(height));
  if (!image || !/^data:image\/(jpeg|png|webp);base64,/.test(image))
    return json({ error: "Please choose a photo." }, 400);
  if (!(w >= 200 && h >= 200 && w <= 8000 && h <= 8000))
    return json({ error: "Size must be between 200 and 8000 pixels." }, 400);

  let gw, gh;
  try { [gw, gh] = generationSize(w, h); } catch (e) { return json({ error: e.message }, 400); }

  try { await ownerTopUp(s.sub, s.email); } catch (e) { console.error(e); }
  if (tier === "ultra") {
    let paid = false;
    try { paid = await isPaid(s.sub); } catch (e) { console.error(e); }
    if (!paid) return json({ error: "Ultra 4K comes with any plan.", needUpgrade: true }, 402);
  }

  // Charge first, refund if anything fails.
  const cost = COST[tier];
  let left;
  try { left = await takeCredits(s.sub, cost); } catch (e) { console.error(e); return json({ error: "Please try again in a moment." }, 503); }
  if (left === null) return json({ error: "You've used all your wallpapers.", needCredits: true, cost }, 402);

  try {
    const mime = image.slice(5, image.indexOf(";"));
    const buf = Buffer.from(image.split(",")[1], "base64");
    if (buf.length > 3_000_000) throw Object.assign(new Error("That photo is too large."), { user: true });

    const fd = new FormData();
    fd.append("model", MODEL);
    fd.append("prompt", buildPrompt(w, h));
    fd.append("size", `${gw}x${gh}`);
    fd.append("quality", QUALITY[tier]);
    fd.append("n", "1");
    fd.append("output_format", "webp");
    fd.append("output_compression", "88"); // keeps the reply under Vercel's 4.5 MB limit
    fd.append("user", s.sub.slice(0, 64));
    fd.append("image", new Blob([buf], { type: mime }), "photo." + mime.split("/")[1]);
    if (mask) fd.append("mask", new Blob([Buffer.from(mask.split(",")[1], "base64")], { type: "image/png" }), "mask.png");

    const r = await fetch("https://api.openai.com/v1/images/edits", {
      method: "POST",
      headers: { Authorization: `Bearer ${key}` },
      body: fd,
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      console.error("OpenAI error", r.status, data?.error);
      const code = data?.error?.code;
      const msg = code === "moderation_blocked"
        ? "This photo can't be processed. Please try another."
        : "Our image service is busy. Please try again in a minute.";
      throw Object.assign(new Error(msg), { user: true });
    }
    const b64 = data?.data?.[0]?.b64_json;
    if (!b64) throw Object.assign(new Error("No image came back. Please try again."), { user: true });
    // Free users: first wallpaper is clean, later ones carry the small Pawlo mark. Plan holders: never marked.
    let mark = false;
    try {
      if (!(await isPaid(s.sub))) mark = (await db().hincrby(userKey(s.sub), "free_made", 1)) > 1;
    } catch (e) { console.error(e); }
    return json({ image: `data:image/webp;base64,${b64}`, credits: left, mark });
  } catch (e) {
    await giveCredits(s.sub, cost).catch((err) => console.error("refund failed", err));
    console.error(e);
    return json({ error: e.user ? e.message : "Something went wrong. Your wallpaper wasn't charged." }, 502);
  }
}
