"""New pin layouts (1000x1500) from existing real Pawlo results — no new generations.
A "wallpaper": the fitted result fills the pin like a real lock screen, small "before" polaroid + caption.
B "split": one phone, left half the bad version, right half the Pawlo fit, divider.
C "trio": three fitted phones side by side, "Pick your wallpaper".
D "stack": original photo as a polaroid on top, arrow, big fitted phone below.
"""
import pathlib
from playwright.sync_api import sync_playwright
from make_mockups import CSS, FOOT, CLOCK, phone, laptop, bad_style, GOOD, SRC, RESU

OUT = pathlib.Path(__file__).parent / "mockups2"; OUT.mkdir(exist_ok=True)
X = """
.full{position:absolute;inset:0;background-size:cover;background-position:center}
.shade{position:absolute;left:0;right:0;bottom:0;height:520px;background:linear-gradient(transparent,rgba(0,0,0,.75))}
.cap{position:absolute;left:60px;right:60px;bottom:200px;color:#fff;font-family:Kalam;font-weight:700;font-size:76px;line-height:1.02;text-shadow:0 3px 18px rgba(0,0,0,.5)}
.capsub{position:absolute;left:60px;right:60px;bottom:150px;color:#fff;font-size:30px;text-shadow:0 2px 10px rgba(0,0,0,.6)}
.pola{position:absolute;background:#fff;padding:14px 14px 50px;box-shadow:0 10px 30px rgba(0,0,0,.35);transform:rotate(-6deg)}
.pola div{background-size:cover;background-position:center}
.pola span{position:absolute;bottom:10px;left:0;right:0;text-align:center;font-family:Kalam;font-weight:700;font-size:26px;color:#C0392B}
.bigclock{position:absolute;top:140px;left:0;right:0;text-align:center;color:#fff;font-weight:700;text-shadow:0 2px 16px rgba(0,0,0,.45)}
.bigclock b{display:block;font-size:170px;line-height:1}.bigclock span{font-size:34px}
.half{position:absolute;top:0;bottom:0;background-repeat:no-repeat}
.div{position:absolute;top:0;bottom:0;left:50%;width:6px;margin-left:-3px;background:#fff;box-shadow:0 0 12px rgba(0,0,0,.5);z-index:4}
.lbl{position:absolute;bottom:40px;z-index:5;font-family:Kalam;font-weight:700;font-size:34px;color:#fff;background:rgba(0,0,0,.55);padding:4px 16px;border-radius:30px}
"""
BIGCLOCK = '<div class="bigclock"><span>Friday, October 30</span><b>9:41</b></div>'

def A(name, title, sub, kind, pos="center"):
    return f"""<div class="full" style="background-image:url({RESU(name + '-phone')});background-position:{pos}"></div>{BIGCLOCK}<div class="shade"></div>
<div class="pola" style="right:60px;top:560px"><div style="width:230px;height:230px;background-image:url({SRC(name)})"></div><span>before: {kind}</span></div>
<div class="cap">{title}</div><div class="capsub">{sub}</div>{FOOT}"""

def B(name, title, sub, kind, focus="50% 50%"):
    w = 450; h = round(w * 2556 / 1179)
    bad = bad_style(kind, SRC(name), focus)
    inner = (f'<div class="half" style="left:0;width:50%;overflow:hidden"><div class="scr" style="width:{w-28}px;{bad}"></div></div>'
             f'<div class="half" style="right:0;width:50%;overflow:hidden"><div class="scr" style="left:auto;right:0;width:{w-28}px;{GOOD(name + "-phone")}"></div></div>'
             f'<div class="div"></div><div class="lbl" style="left:24px">before</div><div class="lbl" style="right:24px">Pawlo</div>')
    return f"""<div class="top"><h1>{title}</h1><p class="sub">{sub}</p></div>
<div class="dev" style="left:{(1000-w)//2}px;top:310px"><div class="phone" style="width:{w}px;height:{h}px">{inner}<div class="isl"></div></div></div>{FOOT}"""

def C(names, title, sub):
    ph = "".join(f'<div style="transform:rotate({r}deg) translateY({y}px)">{phone(GOOD(n + "-phone"), 280)}</div>'
                 for n, r, y in zip(names, (-5, 0, 5), (40, 0, 40)))
    return f"""<div class="top"><h1>{title}</h1><p class="sub">{sub}</p></div>
<div style="position:absolute;top:480px;left:0;right:0;display:flex;justify-content:center;gap:24px">{ph}</div>{FOOT}"""

def D(name, title, sub):
    return f"""<div class="top"><h1>{title}</h1><p class="sub">{sub}</p></div>
<div class="pola" style="left:70px;top:430px"><div style="width:300px;height:300px;background-image:url({SRC(name)})"></div><span>your photo</span></div>
<div style="position:absolute;left:300px;top:820px;font-family:Kalam;font-weight:700;font-size:40px;transform:rotate(-8deg)">→ Pawlo</div>
<div class="dev" style="right:90px;top:400px">{phone(GOOD(name + '-phone'), 400)}<div class="tag ok">Fits every corner</div></div>{FOOT}"""

PINS = [
  ("40-monkey-wall", A("monkey", "This wallpaper used to be blurry", "Fitted to my phone with Pawlo. No zoom, no blur.", "zoomed")),
  ("41-samoyed-wall", A("samoyed", "Beach dog lock screen", "The whole photo, fitted to every corner. Make yours free.", "cropped")),
  ("42-chick-wall", A("chick", "Golden hour lock screen", "From a square pic to a full phone wallpaper.", "square")),
  ("43-sloths-wall", A("sloths", "Sloth hugs wallpaper", "Any cute photo, fitted to your phone in one tap.", "zoomed")),
  ("44-nyc-wall", A("nyc", "Follow that dream wallpaper", "Blurry Pinterest pic → sharp HD lock screen.", "blurry")),
  ("45-catcliff-wall", A("catcliff", "Sea cat lock screen", "Wide photo, now a full phone wallpaper.", "cropped")),
  ("46-dogapple-wall", A("dogapple", "Happy pup wallpaper", "No cropping, no stretching. Just fit.", "cropped")),
  ("47-cat3-wall", A("cat3", "Autumn kitten lock screen", "Square photo → full screen, nothing cut off.", "square")),
  ("50-dog1-split", B("dog1", "Stretched vs fitted", "Same photo. Left: stretched. Right: Pawlo.", "stretch")),
  ("51-orangutan-split", B("orangutan", "Blurry vs sharp HD", "Same photo, fitted to the exact pixel.", "blurry", "50% 45%")),
  ("52-kitten-split", B("kitten", "Cropped vs whole photo", "Your phone crops. Pawlo fills every corner.", "crop")),
  ("53-monkey3-split", B("monkey3", "Zoomed in vs fitted", "See the whole sunset, not a zoomed-in crop.", "zoom", "30% 60%")),
  ("54-chicken-split", B("chicken", "Before and after: lock screen", "Square pic, stretched vs fitted with Pawlo.", "stretch")),
  ("55-dog2-split", B("dog2", "Low quality vs HD wallpaper", "Pawlo rebuilds your photo at your screen's exact size.", "blurry", "50% 45%")),
  ("60-trio-cute", C(["samoyed", "sloths", "kitten"], "Pick your lock screen", "Cute photos, each fitted to the phone with Pawlo.")),
  ("61-trio-sunset", C(["chick", "monkey3", "chicken"], "Sunset wallpapers that actually fit", "Square pics turned into full phone wallpapers.")),
  ("62-trio-pets", C(["dog3", "cat3", "dogapple"], "Pet photos → phone wallpapers", "No crop, no stretch, no blur. Try 2 free.")),
  ("63-trio-mix", C(["catcliff", "orangutan", "nyc"], "Any photo, made to fit your phone", "From Pinterest to your lock screen in one tap.")),
  ("70-dog3-stack", D("dog3", "Your photo → a wallpaper that fits", "Square pics become full-screen phone wallpapers.")),
  ("71-sloths-stack", D("sloths", "Turn any photo into a lock screen", "Pawlo fits it to your exact phone, edge to edge.")),
  ("72-samoyed-stack", D("samoyed", "From camera roll to lock screen", "No cropping. The whole photo, fitted.")),
  ("73-cat2-stack", D("cat2", "Make your favourite pic fit", "iPhone, Samsung, Pixel… any screen size.")),
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

PINS2 = [
  ("110-slothberry-wall", A("slothberry", "Strawberry sloth lock screen", "Cute photo, fitted to every corner of the phone.", "cut off")),
  ("111-gingerkit-wall", A("gingerkit", "Sunny kitten wallpaper", "Square pic turned into a full lock screen.", "square", "50% 75%")),
  ("112-pug-wall", A("pug", "Happy pug lock screen", "The whole view, sized to your phone.", "zoomed", "50% 70%")),
  ("113-orangutan-wall", A("orangutan", "Summer sea wallpaper", "Blurry pic → sharp HD lock screen.", "blurry")),
  ("114-kitten-wall", A("kitten", "Clover kitten lock screen", "No stretching. Just a perfect fit.", "stretched")),
  ("115-dog1-wall", A("dog1", "Tulip pup wallpaper", "Fitted edge to edge, no cropping.", "stretched")),
  ("116-dog2-wall", A("dog2", "Cap dog lock screen", "Low quality pic → HD phone wallpaper.", "blurry")),
  ("117-monkey2-wall", A("monkey2", "Hoodie monkey wallpaper", "The whole photo on your lock screen.", "cropped")),
  ("118-monkey3-wall", A("monkey3", "Sunset monkey lock screen", "Keep the whole sunset, not a zoomed crop.", "zoomed")),
  ("119-cat2-wall", A("cat2", "Car cat lock screen", "Any photo, fitted to your exact phone.", "cropped")),
  ("120-slothberry-crop", B("slothberry", "Stop your phone cropping your pets", "Left: what your phone does. Right: Pawlo.", "crop")),
  ("121-dog3-crop", B("dog3", "Your phone crops your photos. Here's the fix", "Keep the whole picture on your lock screen.", "crop")),
  ("122-cat3-crop", B("cat3", "No more cut-off lock screens", "Pawlo fills every corner without cropping.", "crop")),
  ("123-samoyed-crop", B("samoyed", "Keep the whole photo, every time", "Cropped vs fitted, same photo.", "crop")),
]
if __name__ == "__main__" and sys.argv[1:2] == ["more"]:
    pass
