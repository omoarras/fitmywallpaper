"""Daily compilation: N photos -> one vertical 1080x1920 video (hook, N before/after pairs, end card).

Usage: python3 daily_video.py OUT.mp4 "Hook text" name1 name2 ...
Each name needs public/pins/src/<name>.jpg (original) and results/<name>-phone.png (real Pawlo result, 525x1138).
"""
import sys, pathlib, subprocess, tempfile
from playwright.sync_api import sync_playwright
from make_mockups import CSS, phone, bad_style, GOOD, SRC, LOGO

W, H = 1080, 1920
BASE = CSS.replace("body{width:1000px;height:1500px;", "body{") + f"body{{width:{W}px;height:{H}px}}"
KINDS = ["crop", "zoom", "stretch", "blurry"]
LABEL = {"crop": "Cropped", "zoom": "Zoomed in", "stretch": "Stretched", "blurry": "Blurry"}

def pair(name, kind, i, n):
    bad = phone(bad_style(kind, SRC(name), "50% 50%"), 400, clock=False)
    good = phone(GOOD(name + "-phone"), 400)
    return f"""<div style="position:absolute;top:200px;left:0;right:0;text-align:center"><h1 style="font-size:84px">{i}/{n}</h1></div>
<div style="position:absolute;top:440px;left:50px;display:flex;flex-direction:column;align-items:center">{bad}<div class="tag x" style="font-size:64px">{LABEL[kind]}</div></div>
<div style="position:absolute;top:440px;right:50px;display:flex;flex-direction:column;align-items:center">{good}<div class="tag ok" style="font-size:64px">Pawlo fit ✨</div></div>
<div style="position:absolute;bottom:120px;left:0;right:0;text-align:center;font-size:44px;font-weight:700">pawlowallpaper.com</div>"""

def hook(text):
    return f"""<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;padding:90px">
<h1 style="font-size:120px;line-height:1.05">{text}</h1></div>"""

def end():
    return f"""<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:40px;text-align:center;padding:80px">
<img src="{LOGO}" style="width:620px"><h1 style="font-size:96px;line-height:1.05">Fit any photo to your screen</h1>
<div style="font-size:60px;font-weight:700;padding:26px 50px;border:5px solid #1C1814;border-radius:40px;background:#FFE3CC;box-shadow:8px 8px 0 #1C1814">pawlowallpaper.com</div>
<div style="font-size:46px;color:#B84A00;font-weight:700">2 free wallpapers</div></div>"""

def main(out, text, names):
    tmp = pathlib.Path(tempfile.mkdtemp())
    slides = [("hook", hook(text), 2.0)] + [(f"p{i}", pair(n, KINDS[i % 4], i + 1, len(names)), 2.2) for i, n in enumerate(names)] + [("end", end(), 2.5)]
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": H})
        for k, body, _ in slides:
            f = tmp / f"{k}.html"; f.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}</style></head><body>{body}</body></html>")
            pg.goto(f"file://{f}"); pg.wait_for_timeout(300); pg.screenshot(path=str(tmp / f"{k}.png"))
        b.close()
    args, fc, prev, off = [], [], "[s0]", 0.0
    for i, (k, _, d) in enumerate(slides):
        args += ["-loop", "1", "-t", str(d + 0.3), "-i", str(tmp / f"{k}.png")]
        fc.append(f"[{i}:v]scale={W}:{H},fps=30,setsar=1[s{i}]")
    for i in range(1, len(slides)):
        off += slides[i - 1][2]
        fc.append(f"{prev}[s{i}]xfade=transition={'wiperight' if i % 2 else 'slideleft'}:duration=0.3:offset={off:.2f}[x{i}]")
        prev = f"[x{i}]"
    fc[-1] += ";" + prev.strip("[]").join(["[", "]"]) + "format=yuv420p[v]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args, "-filter_complex", ";".join(fc),
                    "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-movflags", "+faststart", out], check=True)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
