"""Before/after mockup pins (1000x1500) using REAL Pawlo results that fill the whole screen."""
import pathlib
from playwright.sync_api import sync_playwright

REPO = str(pathlib.Path(__file__).resolve().parents[2] / "public")
HERE = pathlib.Path(__file__).parent
RES = HERE / "results"          # real Pawlo outputs: <name>-phone.png / <name>-laptop.png
OUT = HERE / "mockups"; OUT.mkdir(exist_ok=True)
SRC = lambda n: f"file://{REPO}/pins/src/{n}.jpg"
RESU = lambda n: f"file://{RES}/{n}.png"
LOGO = f"file://{REPO}/brand/pawlo-lockup.png"

CSS = f"""
@font-face{{font-family:Kalam;font-weight:700;src:url(file://{REPO}/fonts/kalam-latin-700-normal.woff2)}}
@font-face{{font-family:Figtree;font-weight:400;src:url(file://{REPO}/fonts/figtree-latin-400-normal.woff2)}}
@font-face{{font-family:Figtree;font-weight:700;src:url(file://{REPO}/fonts/figtree-latin-700-normal.woff2)}}
*{{box-sizing:border-box;margin:0}}
body{{width:1000px;height:1500px;background:#FBF8F1;color:#1C1814;font-family:Figtree;position:relative;overflow:hidden}}
.top{{padding:64px 70px 0}}
h1{{font-family:Kalam;font-weight:700;font-size:84px;line-height:1.02}}
.sub{{font-size:34px;color:#5B534A;line-height:1.3;margin-top:14px}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:150px;display:flex;align-items:center;justify-content:space-between;padding:0 60px;border-top:3px solid #1C1814;background:#FFF3E8}}
.foot img{{height:100px}} .foot .url{{font-size:32px;font-weight:700;text-align:right}} .foot small{{display:block;font-size:22px;color:#B84A00}}
.dev{{position:absolute}}
.phone{{position:relative;border:14px solid #1C1814;border-radius:58px;overflow:hidden;background:#000;box-shadow:12px 12px 0 #FFE3CC}}
.phone .isl{{position:absolute;top:14px;left:50%;width:32%;height:30px;transform:translateX(-50%);background:#1C1814;border-radius:99px;z-index:3}}
.scr{{position:absolute;inset:0;background-repeat:no-repeat}}
.clock{{position:absolute;top:8.5%;left:0;right:0;text-align:center;color:#fff;font-weight:700;text-shadow:0 2px 14px rgba(0,0,0,.45);z-index:2}}
.clock b{{display:block;font-size:84px;line-height:1}} .clock span{{font-size:20px}}
.laptop .lid{{position:relative;border:14px solid #1C1814;border-bottom-width:20px;border-radius:22px;overflow:hidden;background:#000;box-shadow:12px 12px 0 #FFE3CC}}
.laptop .base{{height:24px;margin:0 -34px;background:#1C1814;border-radius:0 0 26px 26px}}
.tag{{font-family:Kalam;font-weight:700;font-size:42px;text-align:center;margin-top:16px;white-space:nowrap}}
.x{{color:#C0392B}} .ok{{color:#B84A00}}
.arrow{{position:absolute}}
"""
FOOT = f'<div class="foot"><img src="{LOGO}"><div class="url">pawlowallpaper.com<small>2 free wallpapers</small></div></div>'
ARROW = '<svg width="110" height="70" viewBox="0 0 120 80"><path d="M6 44c30-30 70-30 100-6" stroke="#1C1814" stroke-width="6" fill="none" stroke-linecap="round"/><path d="M92 18l16 22-26 6" stroke="#1C1814" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'
CLOCK = '<div class="clock"><span>Friday, October 30</span><b>9:41</b></div>'

def bad_style(kind, src, focus):
    if kind == "zoom":    return f"background-image:url({src});background-size:auto 175%;background-position:{focus};filter:blur(5px)"
    if kind == "crop":    return f"background-image:url({src});background-size:cover;background-position:center"
    if kind == "stretch": return f"background-image:url({src});background-size:100% 100%"
    if kind == "blurry":  return f"background-image:url({src});background-size:cover;background-position:{focus};filter:blur(7px) saturate(.9);transform:scale(1.06)"
    if kind == "bars":    return f"background:#000 url({src}) center/contain no-repeat"

def phone(style, w, clock=True):
    h = round(w * 2556 / 1179)
    return f'<div class="phone" style="width:{w}px;height:{h}px"><div class="scr" style="{style}"></div><div class="isl"></div>{CLOCK if clock else ""}</div>'

def laptop(style, w):
    h = round((w - 28) * 1664 / 2560) + 34
    return f'<div class="laptop" style="width:{w}px"><div class="lid" style="height:{h}px"><div class="scr" style="{style}"></div></div><div class="base"></div></div>'

GOOD = lambda r: f"background-image:url({RESU(r)});background-size:100% 100%"

def two_phones(name, title, sub, kind, bad_label, good_label, focus="50% 50%"):
    return f"""<div class="top"><h1>{title}</h1><p class="sub">{sub}</p></div>
<div class="dev" style="left:80px;top:500px">{phone(bad_style(kind, SRC(name), focus), 330, clock=False)}<div class="tag x">{bad_label}</div></div>
<div class="arrow" style="left:445px;top:800px">{ARROW}</div>
<div class="dev" style="right:80px;top:460px">{phone(GOOD(name + '-phone'), 370)}<div class="tag ok">{good_label}</div></div>{FOOT}"""

def two_laptops(name, title, sub, kind, bad_label, good_label):
    return f"""<div class="top"><h1>{title}</h1><p class="sub">{sub}</p></div>
<div class="dev" style="left:90px;top:390px">{laptop(bad_style(kind, SRC(name), '50% 50%'), 520)}<div class="tag x">{bad_label}</div></div>
<div class="arrow" style="left:690px;top:640px;transform:rotate(70deg)">{ARROW}</div>
<div class="dev" style="right:90px;top:840px">{laptop(GOOD(name + '-laptop'), 600)}<div class="tag ok">{good_label}</div></div>{FOOT}"""

def phone_and_laptop(name, title, sub):
    return f"""<div class="top"><h1>{title}</h1><p class="sub">{sub}</p></div>
<div class="dev" style="left:60px;top:470px">{phone(GOOD(name + '-phone'), 280)}<div class="tag ok">Phone</div></div>
<div class="dev" style="right:50px;top:700px">{laptop(GOOD(name + '-laptop'), 560)}<div class="tag ok">Laptop</div></div>{FOOT}"""

PINS = [
  ("11-monkey-zoomed", two_phones("monkey", "Why your wallpaper looks blurry", "Your phone zooms in on photos that don't fit its screen. Pawlo fixes it in one tap.", "zoom", "Zoomed &amp; blurry", "Pawlo fit", "48% 62%")),
  ("12-monkey-cropped", two_phones("monkey2", "Stop your phone cropping your photos", "Keep the whole picture. Pawlo fits it to every corner of your screen.", "crop", "Cropped", "Whole photo")),
  ("13-dog-stretched", two_phones("dog1", "Wallpaper looks stretched?", "Pawlo rebuilds your photo at your phone's exact size. No stretching.", "stretch", "Stretched", "Pawlo fit")),
  ("14-dog-blurry", two_phones("dog2", "Low quality photo to sharp HD wallpaper", "Sized to the exact pixel for iPhone, Samsung and more.", "blurry", "Blurry", "Sharp HD", "50% 45%")),
  ("15-cat-laptop-bars", two_laptops("cat", "Phone photo to laptop wallpaper", "No black bars. Same framing, edges filled in naturally.", "bars", "Black bars", "Pawlo fit")),
  ("16-car-laptop", two_laptops("car", "Any photo, full screen on your laptop", "Portrait to landscape without cropping or stretching.", "crop", "Cropped", "Pawlo fit")),
  ("18-cat-cropped", two_phones("cat3", "Square photo, full phone screen", "No more cut-off edges. Pawlo fills every corner of your phone.", "crop", "Cropped", "Whole photo")),
  ("19-dog-stretched", two_phones("dog3", "Square pics look stretched?", "Pawlo rebuilds your photo at your phone's exact size.", "stretch", "Stretched", "Pawlo fit")),
  ("20-monkey-zoomed", two_phones("monkey3", "Lock screen zoomed in too much?", "Keep the whole view. Fitted to your screen in one tap.", "zoom", "Zoomed in", "Pawlo fit", "30% 60%")),
  ("21-nyc-blurry", two_phones("nyc", "Blurry Pinterest pic to sharp wallpaper", "Sized to the exact pixel for iPhone, Samsung and more.", "blurry", "Blurry", "Sharp HD", "50% 72%")),
  ("22-bridge-laptop", two_laptops("bridge", "Phone wallpaper to laptop wallpaper", "No black bars. Same photo, full screen.", "bars", "Black bars", "Pawlo fit")),
  ("17-cat-every-screen", phone_and_laptop("cat2", "One photo. Every screen.", "Pawlo fits the same picture to your phone and your laptop, edge to edge.")),
]

def render(only=None):
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1000, "height": 1500})
        for name, body in PINS:
            if only and name not in only: continue
            f = OUT / f"{name}.html"; f.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>")
            pg.goto(f"file://{f}"); pg.wait_for_timeout(500); pg.screenshot(path=str(OUT / f"{name}.png"))
        b.close()

if __name__ == "__main__":
    import sys; render(sys.argv[1:] or None); print(sorted(x.name for x in OUT.glob("*.png")))
