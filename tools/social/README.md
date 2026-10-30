# Daily cute-wallpaper video (Pawlo)

1. Pick 10 photos (see rules in the scheduled task). Save each as `public/pins/src/<name>.jpg` (≤ 3 MB, JPEG), commit + push to main (Vercel deploys in ~1 min).
2. Convert each with the real site, in the browser pane signed in as the owner (pawlowallpaper@gmail.com) on https://www.pawlowallpaper.com:
   ```js
   const toData=b=>new Promise(r=>{const f=new FileReader();f.onload=()=>r(f.result);f.readAsDataURL(b)});
   window.R={};window.E={};
   names.forEach(async n=>{try{const img=await toData(await fetch('/pins/src/'+n+'.jpg?'+Date.now()).then(r=>r.blob()));
   const r=await fetch('/api/convert',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image:img,width:1179,height:2556,device:'iPhone 16 Pro Max',quality:'standard'})});
   const j=await r.json();if(j.image)R[n]=j.image;else E[n]=j.error}catch(e){E[n]=String(e)}});
   ```
   Poll `Object.keys(R)` / `E` (each takes 1–3 min). Moderation-blocked photos: drop them.
3. Capture each result: resize the pane viewport to 780x850, show the image in a fixed overlay
   (`#ov{position:fixed;inset:0;z-index:99999;background:#000;overflow:hidden} #ov img{max-width:none!important;position:absolute;left:0;width:780px}`),
   set `top:0` then `top:-841px`, take a full-scale screenshot each time (retry once if it times out), then stitch in Python:
   780x1691 canvas, tile 1 at y=0, tile 2 at y=841, resize to 525x1138 → `tools/social/results/<name>-phone.png`.
   Reset the viewport (preset desktop) after.
4. `python3 daily_video.py public/videos/daily-YYYY-MM-DD.mp4 "<hook>" n1 n2 ... n10`
5. Commit + push, then Pinterest: settings/bulk-create-pins, inject a CSV (File via DataTransfer into the file input, CSV text inline — Pinterest CSP blocks fetching our site). Titles must be unique across all pins.

## TikTok (Claude in Chrome — the user's real Chrome, signed in)
Browser pane can't upload files there; use the Claude in Chrome tools (`mcp__claude-in-chrome__*`).
1. Open https://www.tiktok.com/tiktokstudio/upload, `find` "video file input", then `file_upload` with the **cloud path** of the MP4 in this repo clone (e.g. /home/claude/repo/public/videos/x.mp4 — device paths are rejected).
2. Dismiss tips ("Got it"). Caption: typing into the Draft.js editor does NOT work (text goes in reversed/invisible). Instead run JS:
   ```js
   const ed=document.querySelector('.public-DraftEditor-content'); ed.focus();
   const dt=new DataTransfer(); dt.setData('text/plain', CAPTION);
   ed.dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true}));
   ```
   The paste is appended after the default text (the file name without .mp4). Remove it: click the editor, key ctrl+Home, key Delete × len(name). Verify `ed.textContent === CAPTION`.
3. Sound: `find` "Sounds button under preview" → click → in For You list click the first "+" (any popular instrumental) → Save (top right).
4. Settings → When to post: Now, or Schedule (pick date/time) → Post. If something goes wrong use the in-page Discard button (never reload: it raises a leave-page dialog).
