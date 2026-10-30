# Fit My Wallpaper – how to put it online (free)

1. Make a free account at https://github.com and create a new repository called `fitmywallpaper`.
   Click "uploading an existing file" and drag in everything from this folder (api, public, package.json, vercel.json).
2. Make a free account at https://vercel.com (sign in with GitHub).
3. Click "Add New → Project", pick `fitmywallpaper`, then "Deploy".
4. In the project: Settings → Environment Variables → add
   - Name: OPENAI_API_KEY   Value: your OpenAI key
   Then Deployments → ⋯ → Redeploy.
5. Your site is live at https://<project-name>.vercel.app

Optional settings (Environment Variables):
- LIMIT_PER_HOUR   conversions per visitor per hour (default 6)
- OPENAI_IMAGE_QUALITY   high | medium | low (default high; lower = cheaper)

If your address isn't www.pawlowallpaper.com, replace that address in
public/index.html, public/robots.txt and public/sitemap.xml.
