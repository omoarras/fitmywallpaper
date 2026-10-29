// GET → who is signed in + wallpapers left. Also returns public config for the page.
import { getSession, getCredits, isPaid, ownerTopUp, json, clearCookie, PACKS, checkoutLink, googleClientId } from "./_lib.js";

const config = () => ({
  googleClientId: googleClientId(),
  packs: Object.keys(PACKS).filter((n) => checkoutLink(n)).map(Number),
});

export async function GET(request) {
  const s = getSession(request);
  if (!s) return json({ user: null, ...config() });
  try {
    await ownerTopUp(s.sub, s.email);
    return json({ user: { name: s.name, email: s.email, credits: await getCredits(s.sub), paid: await isPaid(s.sub) }, ...config() });
  } catch (e) {
    console.error(e);
    return json({ user: null, error: e.message, ...config() });
  }
}

// POST /api/me with {action:"logout"}
export async function POST() {
  return json({ ok: true }, 200, { "Set-Cookie": clearCookie() });
}
