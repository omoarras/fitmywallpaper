"""Device pins (1000x1500): Samsung / Pixel phones, iPad, desktop monitor, phone+iPad combos. Real Pawlo results only."""
import pathlib
from playwright.sync_api import sync_playwright
from make_mockups import CSS, FOOT, ARROW, bad_style, GOOD, SRC, RESU

OUT = pathlib.Path(__file__).parent / "mockups3"; OUT.mkdir(exist_ok=True)
X = """
.andr{position:relative;border:10px solid #1C1814;border-radius:44px;overflow:hidden;background:#000;box-shadow:12px 12px 0 #FFE3CC}
.andr .hole{position:absolute;top:16px;left:50%;width:22px;height:22px;margin-left:-11px;border-radius:50%;background:#1C1814;z-index:3}
.pix{border-radius:34px}
.pix .bar{position:absolute;top:0;left:0;right:0;height:26px;background:rgba(0,0,0,.25);z-index:2}
.tab{position:relative;border:22px solid #1C1814;border-radius:40px;overflow:hidden;background:#000;box-shadow:12px 12px 0 #FFE3CC}
.tab .cam{position:absolute;top:-15px;left:50%;width:8px;height:8px;margin-left:-4px;border-radius:50%;background:#444;z-index:3}
.mon .scr2{position:relative;border:16px solid #1C1814;border-bottom-width:30px;border-radius:16px;overflow:hidden;background:#000;box-shadow:12px 12px 0 #FFE3CC}
.mon .neck{width:90px;height:90px;margin:0 auto;background:#2B2620}
.mon .foot{width:300px;height:18px;margin:0 auto;background:#1C1814;border-radius:10px}
.aclock{position:absolute;top:9%;left:22px;color:#fff;font-weight:700;text-shadow:0 2px 12px rgba(0,0,0,.45);z-index:2}
.aclock b{display:block;font-size:64px;line-height:1}.aclock span{font-size:18px}
.devlbl{font-size:24px;font-weight:700;color:#5B534A;text-align:center;margin-top:6px}
"""
ACLOCK = '<div class="aclock"><b>09:41</b><span>Fri, 30 Oct</span></div>'

def samsung(style, w, clock=True):
    h = round(w * 2340 / 1080)
    return f'<div class="andr" style="width:{w}px;height:{h}px"><div class="scr" style="{style}"></div><div class="hole"></div>{ACLOCK if clock else ""}</div>'

def pixel(style, w, clock=True):
    h = round(w * 2424 / 1080)
    return f'<div class="andr pix" style="width:{w}px;height:{h}px"><div class="scr" style="{style}"></div><div class="hole"></div>{ACLOCK if clock else ""}</div>'

def ipad(style, w):
    h = round((w - 44) * 2732 / 2048) + 44
    return f'<div class="tab" style="width:{w}px;height:{h}px"><div class="scr" style="{style}"></div><div class="cam"></div></div>'

def monitor(style, w):
    h = round((w - 32) * 10 / 16) + 46
    return f'<div class="mon" style="width:{w}px"><div class="scr2" style="height:{h}px"><div class="scr" style="{style}"></div></div><div class="neck"></div><div class="foot"></div></div>'

IPAD = lambda n: f"background-image:url({RESU(n + '-ipad')});background-size:100% 100%"
LAP = lambda n: f"background-image:url({RESU(n + '-laptop')});background-size:cover;background-position:center"

def top(t, s): return f'<div class="top"><h1>{t}</h1><p class="sub">{s}</p></div>'

def two(dev, name, title, sub, kind, bl, gl, model, focus="50% 50%"):
    f = samsung if dev == "samsung" else pixel
    return f"""{top(title, sub)}
<div class="dev" style="left:80px;top:500px">{f(bad_style(kind, SRC(name), focus), 330, clock=False)}<div class="tag x">{bl}</div></div>
<div class="arrow" style="left:445px;top:800px">{ARROW}</div>
<div class="dev" style="right:80px;top:460px">{f(GOOD(name + '-phone'), 370)}<div class="tag ok">{gl}</div><div class="devlbl">{model}</div></div>{FOOT}"""

def tabs(name, title, sub, kind):
    return f"""{top(title, sub)}
<div class="dev" style="left:70px;top:390px">{ipad(bad_style(kind, SRC(name), '50% 50%'), 380)}<div class="tag x">{'Cropped' if kind=='crop' else 'Black bars'}</div></div>
<div class="arrow" style="left:470px;top:650px;transform:rotate(60deg)">{ARROW}</div>
<div class="dev" style="right:60px;top:560px">{ipad(IPAD(name), 470)}<div class="tag ok">Fits your iPad</div></div>{FOOT}"""

def combo(name, title, sub):
    return f"""{top(title, sub)}
<div class="dev" style="left:70px;top:420px">{ipad(IPAD(name), 540)}<div class="devlbl">iPad</div></div>
<div class="dev" style="right:60px;top:640px">{samsung(GOOD(name + '-phone'), 270)}<div class="devlbl">Phone</div></div>{FOOT}"""

def desk(name, title, sub):
    return f"""{top(title, sub)}
<div class="dev" style="left:60px;top:390px;transform:scale(.55);transform-origin:top left">{monitor(f"background:#000 url({SRC(name)}) center/contain no-repeat", 860)}<div class="tag x" style="font-size:70px">Black bars</div></div>
<div class="arrow" style="left:560px;top:600px;transform:rotate(60deg)">{ARROW}</div>
<div class="dev" style="right:50px;top:800px">{monitor(LAP(name), 520)}<div class="tag ok">Full screen</div></div>{FOOT}"""

PINS = [
  ("80-slothberry-samsung", two("samsung", "slothberry", "Samsung wallpaper cut off?", "Pawlo fits any photo to your Galaxy screen, edge to edge.", "crop", "Cropped", "Whole photo", "Galaxy S25")),
  ("81-gingerkit-samsung", two("samsung", "gingerkit", "Square pic stretched on your Galaxy?", "Rebuilt at your Samsung's exact size. No stretching.", "stretch", "Stretched", "Pawlo fit", "Galaxy A55")),
  ("82-pug-samsung", two("samsung", "pug", "Galaxy lock screen too zoomed in?", "Keep the whole view, fitted in one tap.", "zoom", "Zoomed in", "Pawlo fit", "Galaxy S24", "60% 55%")),
  ("83-dog3-samsung", two("samsung", "dog3", "Make any photo fit your Samsung", "Pick your Galaxy model, tap once, save.", "crop", "Cropped", "Whole photo", "Galaxy S25 Ultra")),
  ("84-nyc-samsung", two("samsung", "nyc", "Blurry pic → sharp Galaxy wallpaper", "HD wallpapers sized for Samsung screens.", "blurry", "Blurry", "Sharp HD", "Galaxy S25", "50% 72%")),
  ("85-monkey2-samsung", two("samsung", "monkey2", "Android wallpaper that actually fits", "No crop, no stretch, no blur.", "crop", "Cropped", "Whole photo", "Galaxy A15")),
  ("86-chick-pixel", two("pixel", "chick", "Pixel wallpaper too zoomed in?", "Pawlo fits the whole photo to your Google Pixel.", "zoom", "Zoomed in", "Pawlo fit", "Pixel 9", "50% 55%")),
  ("87-chicken-pixel", two("pixel", "chicken", "Square pic stretched on your Pixel?", "Rebuilt at your Pixel's exact screen size.", "stretch", "Stretched", "Pawlo fit", "Pixel 9 Pro")),
  ("88-orangutan-pixel", two("pixel", "orangutan", "Blurry photo → sharp Pixel wallpaper", "HD wallpapers sized to the exact pixel.", "blurry", "Blurry", "Sharp HD", "Pixel 8a", "50% 45%")),
  ("90-samoyed-ipad", tabs("samoyed", "Make any photo fit your iPad", "No black bars, no cropping. Edge to edge.", "bars")),
  ("91-sloths-ipad", tabs("sloths", "iPad wallpaper cut off?", "Pawlo fits the whole photo to your iPad screen.", "crop")),
  ("92-catcliff-ipad", tabs("catcliff", "Wide photo → iPad wallpaper", "Same scene, fitted to your tablet in one tap.", "bars")),
  ("93-kitten-ipad", tabs("kitten", "iPad lock screen that fits", "Any photo, sized for iPad, iPad Air and iPad Pro.", "crop")),
  ("94-dogapple-ipad", tabs("dogapple", "Your pet on your iPad, fully", "No cropping. The whole photo, fitted.", "crop")),
  ("95-samoyed-combo", combo("samoyed", "One photo. Phone and iPad.", "Pawlo fits the same picture to every screen you own.")),
  ("96-sloths-combo", combo("sloths", "Matching phone & iPad wallpapers", "Each one sized exactly for its screen.")),
  ("97-catcliff-combo", combo("catcliff", "Same view, every screen", "Phone and tablet wallpapers from one photo.")),
  ("98-kitten-combo", combo("kitten", "Kitten on every screen", "Fitted to your phone and your iPad, edge to edge.")),
  ("99-dogapple-combo", combo("dogapple", "Your pup, phone + tablet", "One upload, wallpapers for every device.")),
  ("100-cat-monitor", desk("cat", "Phone photo → desktop wallpaper", "No black bars on your monitor. Same framing, full screen.")),
  ("101-car-monitor", desk("car", "Full-screen car wallpaper for PC", "Portrait to landscape, fitted to your monitor.")),
  ("102-bridge-monitor", desk("bridge", "Tall photo → monitor wallpaper", "Pawlo fills the edges naturally. No stretching.")),
  ("103-street-monitor", desk("street", "Aesthetic desktop wallpaper from any pic", "Fitted to your monitor's exact size.")),
]

if __name__ == "__main__":
    import sys
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1000, "height": 1500})
        for name, body in PINS:
            if sys.argv[1:] and name not in sys.argv[1:]: continue
            f = OUT / f"{name}.html"; f.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}{X}</style></head><body>{body}</body></html>")
            pg.goto(f"file://{f}"); pg.wait_for_timeout(400); pg.screenshot(path=str(OUT / f"{name}.png")); f.unlink()
        b.close()
    print(len(list(OUT.glob("*.png"))))
