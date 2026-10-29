// POST {image, width, height, quality:"standard"|"ultra"} → wallpaper. Uses the person's wallpaper balance.
import { getSession, takeCredits, giveCredits, isPaid, json, COST, db, userKey } from "./_lib.js";

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

function buildPrompt(w, h) {
  const orient = w > h ? "landscape" : w < h ? "upright" : "square";
  return `Convert the original photograph into a ${w}×${h} ${orient} wallpaper.

ABSOLUTE PRIORITY: preserve the original photograph without regenerating or modifying its existing pixels. The original photo is placed in the canvas and is a locked, immutable photographic layer. Only generate pixels in the masked area outside the original image boundaries. The blurred border is only a placeholder showing which colours continue there; replace it with a natural continuation of the scene.

Composition and subject preservation
- Keep every person, animal and main subject exactly as photographed: faces, expressions, hairstyles, clothing, body proportions, hands, fingers and poses.
- Do not enlarge, reshape, duplicate or reconstruct any hand, finger, arm, limb or face.
- Keep every object, surface, piece of furniture, vehicle interior, building and landscape in the original area unchanged: same shape, position, texture and lighting.
- Preserve the natural shape of surfaces such as seats, walls, floors, skies and fabrics. Do not create elongated strips, stretched surfaces, giant geometric shapes, artificial panels or other anomalous structures.
- Do not invent, extend or reconstruct any existing body part or object beyond what is needed to continue it naturally past the edge.

Canvas expansion
Expand the canvas to ${w}×${h} using only the minimum necessary outpainting. Preserve the source image's original crop and scale. Do not zoom, pan, stretch, distort or resize the original image.

Where new pixels are required, continue the existing scene naturally. Match textures, materials, seams, perspective, shadows and lighting. Maintain physically plausible geometry and realistic boundaries between subjects, clothing and background.

Do not fill the new areas with large smooth shapes or repeated textures. Do not create extra people, arms, hands, fingers, limbs, or duplicate objects. Do not blend a person's clothing into the background.

Strict editing rule: never regenerate the people or the original visible parts of the scene. If an area cannot be extended reliably, use a conservative, unobtrusive continuation of the surrounding background rather than inventing details.

Maintain the original color grading, exposure, grain, sharpness and natural camera appearance (if the original is an illustration or artwork, match its style instead). Output a clean ${w}×${h} wallpaper without visible AI artifacts or seams.

Negative constraints: giant hands, distorted fingers, extra fingers, duplicated limbs, altered faces, changed body proportions, melted clothing, elongated or stretched surfaces, giant flat strips, warped geometry, invented objects, extra people, excessive outpainting, composition changes, artificial smoothing, visible seams.`;
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
