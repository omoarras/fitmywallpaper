// Vercel serverless function: sends the photo + composition-locked prompt to OpenAI.
// Secret key lives in Vercel env var OPENAI_API_KEY (never in this file).


const MODEL = process.env.OPENAI_IMAGE_MODEL || "gpt-image-2";
const QUALITY = process.env.OPENAI_IMAGE_QUALITY || "high";
const LIMIT_PER_HOUR = Number(process.env.LIMIT_PER_HOUR || 6);

// Basic per-IP limit (resets when the server restarts; stops casual abuse).
const hits = new Map();
function allowed(ip) {
  const now = Date.now();
  const list = (hits.get(ip) || []).filter((t) => now - t < 3600_000);
  if (list.length >= LIMIT_PER_HOUR) return false;
  list.push(now);
  hits.set(ip, list);
  return true;
}

// gpt-image-2 rules: long edge <= 3840, sides multiple of 16, ratio <= 3:1.
function generationSize(w, h) {
  const long = Math.max(w, h), short = Math.min(w, h);
  if (long / short > 3) throw new Error("That shape is too extreme (max 3:1).");
  // Render as large as the model allows (up to 4K-class) so the result is sharp on any screen.
  const scale = Math.min(3840 / long, Math.sqrt(8_294_400 / (w * h)));
  const r16 = (v) => Math.max(16, Math.floor((v * scale) / 16) * 16);
  return [r16(w), r16(h)];
}

function buildPrompt(w, h) {
  const orient = w > h ? "landscape" : w < h ? "portrait" : "square";
  return `Universal Composition-Locked Wallpaper Prompt (v1)

Convert this image into a ${w}×${h} ${orient} wallpaper while preserving the exact visual composition of the original image. Composition is the highest priority. The apparent crop, framing, camera position, focal length, perspective, subject placement, subject size, and visual balance must remain identical. The final image should look like the original photograph simply exists on a canvas of the new shape—not like the camera moved, zoomed, or revealed more of the scene.

Do NOT zoom out. Do NOT widen the field of view. Do NOT reveal additional portions of objects or the environment. Do NOT reposition or resize any existing element. The visible area of every object should remain visually identical to the original.

Adapt the image to ${w}×${h} by reconstructing only what is absolutely necessary to preserve the original composition at the new aspect ratio. Any generated content must seamlessly continue existing textures, lighting, reflections, shadows, colors, grain, and geometry without attracting attention or altering the scene.

Treat the original composition as locked. If preserving the composition conflicts with showing more of the environment, always preserve the composition.

Output a sharp native ${w}×${h} image with identical color grading, contrast, noise, sharpness, and lighting. The viewer should perceive the exact same photograph, only reformatted to the new aspect ratio, with no visible AI edits or composition changes.

Composition Lock: 100%

Camera locked.
Lens locked.
Perspective locked.
Crop perception locked.
Subject scale locked.
Subject positions locked.
Visual balance locked.
No zoom.
No pan.
No camera movement.
No additional scene revealed.
Preserve the original image exactly; only adapt it to the target aspect ratio.`;
}

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "Use POST." });

  const key = process.env.OPENAI_API_KEY || process.env.OPEN_API_KEY;
  if (!key) return res.status(500).json({ error: "Server is missing its API key." });

  const ip = (req.headers["x-forwarded-for"] || "").split(",")[0].trim() || "anon";
  if (!allowed(ip)) return res.status(429).json({ error: "Limit reached. Please try again in an hour." });

  try {
    const { image, width, height } = req.body || {};
    const w = Math.round(Number(width)), h = Math.round(Number(height));
    if (!image || !/^data:image\/(jpeg|png|webp);base64,/.test(image))
      return res.status(400).json({ error: "Please choose a photo." });
    if (!(w >= 200 && h >= 200 && w <= 8000 && h <= 8000))
      return res.status(400).json({ error: "Size must be between 200 and 8000 pixels." });

    const [gw, gh] = generationSize(w, h);
    const mime = image.slice(5, image.indexOf(";"));
    const buf = Buffer.from(image.split(",")[1], "base64");

    const fd = new FormData();
    fd.append("model", MODEL);
    fd.append("prompt", buildPrompt(w, h));
    fd.append("size", `${gw}x${gh}`);
    fd.append("quality", QUALITY);
    fd.append("n", "1");
    fd.append("output_format", "webp"); // keeps the reply under Vercel's 4.5 MB limit
    fd.append("output_compression", "92");
    fd.append("image", new Blob([buf], { type: mime }), "photo." + mime.split("/")[1]);

    const r = await fetch("https://api.openai.com/v1/images/edits", {
      method: "POST",
      headers: { Authorization: `Bearer ${key}` },
      body: fd,
    });
    const data = await r.json();
    if (!r.ok) {
      console.error("OpenAI error", data);
      const msg = data?.error?.code === "moderation_blocked"
        ? "This photo can't be processed. Please try another."
        : "The image service had a problem: " + (data?.error?.message || r.status);
      return res.status(502).json({ error: msg });
    }
    const b64 = data?.data?.[0]?.b64_json;
    if (!b64) return res.status(502).json({ error: "No image came back. Please try again." });
    return res.status(200).json({ image: `data:image/webp;base64,${b64}` });
  } catch (e) {
    console.error(e);
    return res.status(500).json({ error: e.message || "Something went wrong." });
  }
}
