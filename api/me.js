// GET → who is signed in + wallpapers left. Also returns public config for the page.
import { getSession, getCredits, json, clearCookie, PACKS, checkoutLink } from "./_lib.js";

const config = () => ({
  googleClientId: process.env.GOOGLE_CLIENT_ID || "",
  packs: Object.keys(PACKS).filter((n) => checkoutLink(n)).map(Number),
});

export async function GET(request) {
  const s = getSession(request);
  if (!s) return json({ user: null, ...config() });
  try {
    return json({ user: { name: s.name, email: s.email, credits: await getCredits(s.sub) }, ...config() });
  } catch (e) {
    console.error(e);
    return json({ user: null, error: e.message, ...config() });
  }
}

// POST /api/me with {action:"logout"}
export async function POST() {
  return json({ ok: true }, 200, { "Set-Cookie": clearCookie() });
}
