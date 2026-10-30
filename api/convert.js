// POST {image, width, height, quality:"standard"|"ultra"} → wallpaper. Uses the person's wallpaper balance.
import { getSession, takeCredits, giveCredits, isPaid, ownerTopUp, json, COST, db, userKey } from "./_lib.js";

const MODEL = process.env.OPENAI_IMAGE_MODEL || "gpt-image-2";
// Chat model that reads the photo and prompt first, like ChatGPT does ("chat-latest" = ChatGPT model).
const CHAT_MODEL = process.env.OPENAI_CHAT_MODEL || "chat-latest";
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
// The user's controlled-outpainting prompt, word for word (as used in ChatGPT); target fields filled from the user's selection.
function buildPrompt(w, h, device) {
  const orient = w > h ? "Landscape" : w < h ? "Portrait" : "Square";
  const r = ratioText(w, h);
  const name = String(device || "").replace(/[^\w\s.\-+/()"']/g, "").slice(0, 60) || "Selected screen";
  return `TASK: Expand the supplied photograph to fit the user's selected wallpaper aspect ratio using controlled AI outpainting.
TARGET DEVICE: ${name}
TARGET ORIENTATION: ${orient}
TARGET RESOLUTION: ${w} × ${h} pixels
TARGET ASPECT RATIO: ${r}
PRIMARY OBJECTIVE
Preserve the original photograph exactly and generate only the additional image content required to fit the target canvas.
This is an OUTPAINTING task, not an image regeneration, image recreation, image enhancement, or subject reconstruction task.
The original photograph is the immutable source of truth.
1. ORIGINAL IMAGE PROTECTION
Treat the entire original image as a protected, composition-locked region.
Preserve its existing pixels, subject proportions, framing, camera perspective, lighting, colors, textures, grain, sharpness, and every visible object.
Do not redraw, regenerate, reinterpret, enhance, or reconstruct any part of the original image.
Do not change the subject's face, body, proportions, expression, clothing, position, or size.
Do not alter the existing background, objects, shadows, reflections, or other visible details.
The original image must remain pixel-identical wherever it overlaps the final canvas.
2. CONTROLLED CANVAS EXPANSION
Calculate the exact difference between the source image's aspect ratio and the selected target aspect ratio.
Generate new pixels ONLY outside the protected original-image boundaries.
Determine whether the canvas needs expansion on the left, right, top, or bottom based on the selected target dimensions and the application's composition-preservation rules.
Continue the existing environment naturally.
Match the source image's perspective, geometry, lighting direction, exposure, color grading, texture, grain, shadows, and depth of field.
If the source shows a street, continue the road markings, pavement, buildings, shadows, and other existing environmental details.
Do not introduce new subjects, objects, people, animals, vehicles, or structures unless they are unavoidably implied by the existing scene.
Do not extend the subject's body or invent body parts simply to fill empty space.
Prefer conservative, unobtrusive background continuation whenever a reliable reconstruction is uncertain.
3. STRICT GEOMETRY CONSTRAINTS
Do not stretch, distort, rotate, or independently scale the image's width and height.
Do not zoom in or zoom out to compensate for the aspect-ratio difference.
Do not move the subject.
Do not change the original camera perspective or reconstruct the photograph from a different viewpoint.
Do not add black bars, solid-color borders, blurred duplicate backgrounds, mirrored edges, or artificial padding.
Do not fill missing areas with large smooth gradients or repetitive textures.
Do not allow generated pixels to overwrite existing image content.
4. FINAL IMAGE REQUIREMENTS
Produce a seamless, photorealistic outpainting result suitable for a premium smartphone wallpaper.
Preserve the original image's visual appearance and composition.
The transition between the original photograph and the generated areas must be natural and unobtrusive.
The final canvas must match the user's selected aspect ratio.
The final export must have the exact pixel dimensions required by the selected device.
IMPORTANT: The AI model must generate only the missing regions. The application must preserve and composite the original pixels independently of the model's output. Do not rely on prompt instructions alone to protect the original image.`;
}

export async function POST(request) {
  const key = process.env.OPENAI_API_KEY || process.env.OPEN_API_KEY;
  if (!key) return json({ error: "Server is missing its API key." }, 500);

  const s = getSession(request);
  if (!s) return json({ error: "Please sign in to make a wallpaper.", needLogin: true }, 401);

  let body;
  try { body = await request.json(); } catch { return json({ error: "Please choose a photo." }, 400); }
  const { image, width, height } = body || {};
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
    if (buf.length > 3_200_000) throw Object.assign(new Error("That photo is too large."), { user: true });

    const prompt = buildPrompt(w, h, body?.device);
    let b64 = null, errCode = null;

    // 1) Same path as ChatGPT: a chat model reads the photo + prompt, then calls the image tool.
    try {
      const r = await fetch("https://api.openai.com/v1/responses", {
        method: "POST",
        headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          model: CHAT_MODEL,
          input: [{ role: "user", content: [
            { type: "input_text", text: prompt },
            { type: "input_image", image_url: image },
          ] }],
          tools: [{ type: "image_generation", model: MODEL, action: "edit", size: `${gw}x${gh}`, quality: QUALITY[tier], output_format: "webp", output_compression: 88 }],
          tool_choice: { type: "image_generation" },
          user: s.sub.slice(0, 64),
        }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) { errCode = data?.error?.code; console.error("Responses error", r.status, data?.error); }
      else b64 = (data.output || []).find((o) => o.type === "image_generation_call" && o.result)?.result || null;
    } catch (e) { console.error("Responses failed", e); }

    // 2) Backup: direct image edit (used only if the first path fails).
    if (!b64 && errCode !== "moderation_blocked") {
      const fd = new FormData();
      fd.append("model", MODEL);
      fd.append("prompt", prompt);
      fd.append("size", `${gw}x${gh}`);
      fd.append("quality", QUALITY[tier]);
      fd.append("n", "1");
      fd.append("output_format", "webp");
      fd.append("output_compression", "88"); // keeps the reply under Vercel's 4.5 MB limit
      fd.append("user", s.sub.slice(0, 64));
      fd.append("image", new Blob([buf], { type: mime }), "photo." + mime.split("/")[1]);
      const r = await fetch("https://api.openai.com/v1/images/edits", { method: "POST", headers: { Authorization: `Bearer ${key}` }, body: fd });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) { errCode = data?.error?.code; console.error("OpenAI error", r.status, data?.error); }
      else b64 = data?.data?.[0]?.b64_json || null;
    }
    if (!b64) throw Object.assign(new Error(errCode === "moderation_blocked"
      ? "This photo can't be processed. Please try another."
      : "Our image service is busy. Please try again in a minute."), { user: true });
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
