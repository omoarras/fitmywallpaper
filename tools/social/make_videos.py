"""5 vertical before/after videos (1080x1920) from real Pawlo results: stills via Playwright, motion via ffmpeg."""
import pathlib, subprocess
from playwright.sync_api import sync_playwright
from make_mockups import CSS, phone, laptop, bad_style, GOOD, SRC, LOGO

OUT = pathlib.Path(__file__).parent / "videos"; OUT.mkdir(exist_ok=True)
W, H = 1080, 1920
base = CSS.replace("body{width:1000px;height:1500px;", "body{") + f"body{{width:{W}px;height:{H}px}}"

def frame(hook, device_html, label, label_cls):
    top = 640 if 'laptop' in device_html else 490
    return f"""<div style="position:absolute;top:150px;left:60px;right:60px;text-align:center">
<h1 style="font-size:96px;line-height:1.05">{hook}</h1></div>
<div style="position:absolute;top:{top}px;left:0;right:0;display:flex;flex-direction:column;align-items:center">{device_html}
<div class="tag {label_cls}" style="font-size:80px;margin-top:30px">{label}</div></div>
<div style="position:absolute;bottom:120px;left:0;right:0;text-align:center;font-size:44px;font-weight:700">pawlowallpaper.com</div>"""

def endcard(line):
    return f"""<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:40px;text-align:center;padding:80px">
<img src="{LOGO}" style="width:620px"><h1 style="font-size:96px;line-height:1.05">{line}</h1>
<div style="font-size:60px;font-weight:700;padding:26px 50px;border:5px solid #1C1814;border-radius:40px;background:#FFE3CC;box-shadow:8px 8px 0 #1C1814">pawlowallpaper.com</div>
<div style="font-size:46px;color:#B84A00;font-weight:700">2 free wallpapers</div></div>"""

PW = 470  # phone width on screen
def ph(style, clock=True): return phone(style, PW, clock=clock)
def lap(style): return laptop(style, 940)

VIDEOS = [
  ("v1-blurry", "Why does my wallpaper look blurry? 😩",
   ph(bad_style("zoom", SRC("monkey"), "48% 62%"), False), "Zoomed & blurry",
   ph(GOOD("monkey-phone")), "Pawlo fit ✨",
   "Make any photo fit your screen"),
  ("v2-stretched", "My wallpaper always looks stretched…",
   ph(bad_style("stretch", SRC("dog1"), "50% 50%"), False), "Stretched",
   ph(GOOD("dog1-phone")), "Pawlo fit ✨", "No more stretched wallpapers"),
  ("v3-hd", "Low quality pic → HD wallpaper",
   ph(bad_style("blurry", SRC("dog2"), "50% 45%"), False), "Blurry",
   ph(GOOD("dog2-phone")), "Sharp HD ✨", "Any photo, sharp HD"),
  ("v4-cropped", "Stop cropping my photos 😤",
   ph(bad_style("crop", SRC("monkey2"), "50% 50%"), False), "Cropped",
   ph(GOOD("monkey2-phone")), "Whole photo ✨", "Keep the whole picture"),
  ("v5-laptop", "Phone pic → laptop wallpaper 💻",
   lap(bad_style("bars", SRC("cat"), "50% 50%")), "Black bars",
   lap(GOOD("cat-laptop")), "Pawlo fit ✨", "Fits laptops too"),
  ("v6-cat-cropped", "Why does my phone cut my cat's leaf off? 🍁",
   ph(bad_style("crop", SRC("cat3"), "50% 50%"), False), "Cropped",
   ph(GOOD("cat3-phone")), "Whole photo ✨", "Square photo → full screen"),
  ("v7-dog-stretched", "Square pics look stretched on my phone 😭",
   ph(bad_style("stretch", SRC("dog3"), "50% 50%"), False), "Stretched",
   ph(GOOD("dog3-phone")), "Pawlo fit ✨", "No more stretched pets"),
  ("v8-monkey-zoomed", "Lock screen zoomed in too much?",
   ph(bad_style("zoom", SRC("monkey3"), "30% 60%"), False), "Zoomed in",
   ph(GOOD("monkey3-phone")), "Pawlo fit ✨", "See the whole sunset"),
  ("v9-nyc-blurry", "Blurry Pinterest pic → sharp wallpaper",
   ph(bad_style("blurry", SRC("nyc"), "50% 72%"), False), "Blurry",
   ph(GOOD("nyc-phone")), "Sharp HD ✨", "Follow that dream ✨"),
  ("v10-bridge-laptop", "Phone wallpaper → laptop wallpaper 💻",
   lap(bad_style("bars", SRC("bridge"), "50% 50%")), "Black bars",
   lap(GOOD("bridge-laptop")), "Pawlo fit ✨", "One photo, every screen"),
]

def render():
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": H})
        for name, hook, bad, bl, good, gl, end in VIDEOS:
            for suffix, body in [("a", frame(hook, bad, bl, "x")), ("b", frame(hook, good, gl, "ok")), ("c", endcard(end))]:
                f = OUT / f"{name}-{suffix}.html"
                f.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>{base}</style></head><body>{body}</body></html>")
                pg.goto(f"file://{f}"); pg.wait_for_timeout(400); pg.screenshot(path=str(OUT / f"{name}-{suffix}.png")); f.unlink()
        b.close()

def encode(name):
    a, bb, c = (str(OUT / f"{name}-{s}.png") for s in "abc")
    # a: 2.6s (slow push-in), wipe to b over 0.6s, b: 2.6s, fade to end card 0.5s, c: 2.2s
    fc = ("[0:v]scale=1080:1920,zoompan=z='1+0.0006*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=96:s=1080x1920:fps=30,setsar=1[a];"
          "[1:v]scale=1080:1920,zoompan=z='1.03-0.0003*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=96:s=1080x1920:fps=30,setsar=1[b];"
          "[2:v]scale=1080:1920,fps=30,setsar=1[c];"
          "[a][b]xfade=transition=wiperight:duration=0.6:offset=2.6[ab];"
          "[ab][c]xfade=transition=fade:duration=0.5:offset=5.2,format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                    "-loop", "1", "-t", "3.2", "-i", a, "-loop", "1", "-t", "3.2", "-i", bb, "-loop", "1", "-t", "2.4", "-i", c,
                    "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-movflags", "+faststart", "-r", "30", str(OUT / f"{name}.mp4")], check=True)

if __name__ == "__main__":
    import sys
    only = sys.argv[1:]
    if only: VIDEOS[:] = [v for v in VIDEOS if v[0] in only]
    render()
    for v in VIDEOS: encode(v[0])
    print(sorted(x.name for x in OUT.glob("*.mp4")))
