"""TikTok videos for iPad / laptop (1080x1920, no audio) from existing real Pawlo results."""
import pathlib, subprocess, tempfile
from playwright.sync_api import sync_playwright
from make_mockups import phone, laptop, bad_style, GOOD, SRC, RESU
from make_videos import base, endcard, W, H
from make_pins3 import ipad, X as DEVCSS

OUT = pathlib.Path(__file__).parent / "videos"; OUT.mkdir(exist_ok=True)
IPAD = lambda n: f"background-image:url({RESU(n + '-ipad')});background-size:100% 100%"
LAP = lambda n: f"background-image:url({RESU(n + '-laptop')});background-size:100% 100%"
CSS = base + DEVCSS + """
.hook{position:absolute;top:150px;left:60px;right:60px;text-align:center;font-family:Kalam;font-weight:700;font-size:92px;line-height:1.05}
.mid{position:absolute;left:0;right:0;display:flex;flex-direction:column;align-items:center}
.big{font-family:Kalam;font-weight:700;font-size:96px;margin-top:30px}
.rate{font-family:Kalam;font-weight:700;font-size:170px;color:#B84A00;margin-top:30px;text-shadow:6px 6px 0 #FFE3CC}
.url{position:absolute;bottom:120px;left:0;right:0;text-align:center;font-size:44px;font-weight:700}
.row{display:flex;gap:40px;align-items:flex-end}
"""

def scene(hook, inner, top=520, label="", cls="ok", url=True):
    lab = f'<div class="big {cls}">{label}</div>' if label else ""
    return f'<div class="hook">{hook}</div><div class="mid" style="top:{top}px">{inner}{lab}</div>' + ('<div class="url">pawlowallpaper.com</div>' if url else "")

def v1():
    hook = "POV: your iPad wallpaper finally fits 😍"
    s = []
    for n in ["sloths", "samoyed", "kitten"]:
        s += [(scene(hook, ipad(bad_style("crop", SRC(n), "50% 50%"), 720), 500, "Cropped ❌", "x"), 1.3, "wiperight"),
              (scene(hook, ipad(IPAD(n), 720), 500, "Fits ✅"), 1.4, "fade")]
    return s + [(endcard("Make any photo fit your iPad"), 2.4, None)]

def v2():
    hook = "Phone pic → MacBook wallpaper in 1 tap 💻"
    s = []
    for n in ["cat", "car", "bridge"]:
        s += [(scene(hook, laptop(f"background:#000 url({SRC(n)}) center/contain no-repeat", 980), 640, "Black bars ❌", "x"), 1.3, "wiperight"),
              (scene(hook, laptop(LAP(n), 980), 640, "Full screen ✅"), 1.4, "fade")]
    return s + [(endcard("Any photo, full screen on your laptop"), 2.4, None)]

def v3():
    hook = "Rating my laptop wallpapers (made from phone pics 👀)"
    s = []
    for n, r in [("street", "7/10"), ("cat", "8/10"), ("cat2", "9/10"), ("car", "10/10"), ("bridge", "11/10")]:
        s.append((scene(hook, laptop(LAP(n), 980) + f'<div class="rate">{r}</div>', 600), 1.5, "slideleft"))
    return s + [(endcard("Make yours from any photo"), 2.4, None)]

def v4():
    hook = "Same photo. Phone AND iPad. 🤯"
    s = []
    for n in ["sloths", "catcliff", "dogapple"]:
        p = phone(GOOD(n + "-phone"), 300)
        s += [(scene(hook, f'<div class="row">{p}</div>', 620, "Phone ✅"), 1.1, "fade"),
              (scene(hook, f'<div class="row">{p}{ipad(IPAD(n), 560)}</div>', 620, "Phone + iPad ✅"), 1.5, "slideleft")]
    return s + [(endcard("One photo, every screen"), 2.4, None)]

def build(name, slides):
    tmp = pathlib.Path(tempfile.mkdtemp())
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": H})
        for i, (body, _, _) in enumerate(slides):
            f = tmp / f"{i}.html"; f.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>")
            pg.goto(f"file://{f}"); pg.wait_for_timeout(300); pg.screenshot(path=str(tmp / f"{i}.png"))
        b.close()
    args, fc, prev, off, T = [], [], "[s0]", 0.0, 0.3
    for i, (_, d, _) in enumerate(slides):
        args += ["-loop", "1", "-t", str(d + T), "-i", str(tmp / f"{i}.png")]
        fc.append(f"[{i}:v]scale={W}:{H},fps=30,setsar=1[s{i}]")
    for i in range(1, len(slides)):
        off += slides[i - 1][1]
        fc.append(f"{prev}[s{i}]xfade=transition={slides[i-1][2] or 'fade'}:duration={T}:offset={off:.2f}[x{i}]"); prev = f"[x{i}]"
    fc.append(f"{prev}format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args, "-filter_complex", ";".join(fc), "-map", "[v]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-movflags", "+faststart", str(OUT / f"{name}.mp4")], check=True)
    (tmp / "0.png").rename(OUT / f"{name}-first.png")

if __name__ == "__main__":
    for n, f in [("tt1-ipad-pov", v1), ("tt2-macbook", v2), ("tt3-rate-laptops", v3), ("tt4-phone-ipad", v4)]:
        build(n, f())
    print("done")

POLA = lambda n, w=300, lab="original": f'<div class="pola" style="position:relative;transform:rotate(-5deg);margin-top:30px"><div style="width:{w}px;height:{w}px;background-image:url({SRC(n)})"></div><span>{lab}</span></div>'
CSS += """.pola{background:#fff;padding:14px 14px 50px;box-shadow:0 10px 30px rgba(0,0,0,.3)}
.pola div{background-size:cover;background-position:center}.pola span{position:absolute;bottom:8px;left:0;right:0;text-align:center;font-family:Kalam;font-weight:700;font-size:30px;color:#C0392B}
.tagbig{font-family:Kalam;font-weight:700;font-size:110px;margin-top:24px}"""

def v5():
    hook = "Stop doing this to your iPad wallpaper 😭"
    s = []
    for n in ["kitten", "dogapple"]:
        s += [(scene(hook, ipad(bad_style("zoom", SRC(n), "50% 45%"), 720), 500, "Pinch-zoomed ❌", "x"), 1.5, "wiperight"),
              (scene(hook, ipad(IPAD(n), 720), 500, "Do this instead ✅"), 1.6, "fade")]
    return s + [(endcard("Fit it to your exact iPad"), 2.4, None)]

def v6():
    hook = "Guess what this wallpaper used to be 👀"
    s = []
    for n, dev in [("cat2", "lap"), ("catcliff", "ipad"), ("bridge", "lap")]:
        d = laptop(LAP(n), 960) if dev == "lap" else ipad(IPAD(n), 620)
        s += [(scene(hook, d, 560), 1.4, "fade"),
              (scene(hook, d + POLA(n), 470, "wait WHAT 😳"), 1.7, "slideleft")]
    return s + [(endcard("Any photo → any screen"), 2.4, None)]

def v7():
    hook = "Which iPad wallpaper are you? 🤔"
    s = []
    for n, lab in [("samoyed", "Calm 🌊"), ("kitten", "Cozy 🐱"), ("dogapple", "Happy 🐶"), ("sloths", "Cuddly 🦥"), ("catcliff", "Dreamy 🌅")]:
        s.append((scene(hook, ipad(IPAD(n), 720), 500, lab), 1.3, "slideleft"))
    return s + [(endcard("Make yours from any photo"), 2.4, None)]

def v8():
    hook = "Desk setup glow-up ✨"
    s = []
    for n in ["cat2", "street"]:
        s += [(scene(hook, laptop(f"background:#000 url({SRC(n)}) center/contain no-repeat", 980), 640, "Before", "x"), 1.4, "circleopen"),
              (scene(hook, laptop(LAP(n), 980), 640, "After ✨"), 1.7, "fade")]
    return s + [(endcard("Glow up your laptop wallpaper"), 2.4, None)]

def v9():
    hook = "3 phone pics that became laptop wallpapers"
    s = []
    for i, n in enumerate(["car", "cat", "bridge"]):
        num = f'<div class="tagbig ok">{3-i}</div>'
        s += [(scene(hook, num + phone(f"background-image:url({SRC(n)});background-size:cover;background-position:center", 330), 470), 1.1, "zoomin"),
              (scene(hook, num + laptop(LAP(n), 980), 520), 1.6, "fade")]
    return s + [(endcard("Phone photo → laptop wallpaper"), 2.4, None)]

if __name__ == "__main__":
    pass
