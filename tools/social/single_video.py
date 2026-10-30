"""One photo -> one 7.6s vertical before/after video (hook, bad version, wipe to Pawlo fit, end card).

Usage: python3 single_video.py OUT.mp4 NAME KIND "Hook text" "End line"
KIND: crop | zoom | stretch | blurry.  Needs public/pins/src/NAME.jpg and results/NAME-phone.png.
"""
import sys, pathlib, subprocess, tempfile
from playwright.sync_api import sync_playwright
from make_mockups import phone, bad_style, GOOD, SRC
from make_videos import base, frame, endcard, W, H

LABEL = {"crop": "Cropped", "zoom": "Zoomed in", "stretch": "Stretched", "blurry": "Blurry"}
GOODL = {"crop": "Whole photo ✨", "zoom": "Pawlo fit ✨", "stretch": "Pawlo fit ✨", "blurry": "Sharp HD ✨"}

def main(out, name, kind, hook, end):
    tmp = pathlib.Path(tempfile.mkdtemp())
    focus = "50% 45%" if kind in ("zoom", "blurry") else "50% 50%"
    slides = {"a": frame(hook, phone(bad_style(kind, SRC(name), focus), 470, clock=False), LABEL[kind], "x"),
              "b": frame(hook, phone(GOOD(name + "-phone"), 470), GOODL[kind], "ok"),
              "c": endcard(end)}
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": H})
        for k, body in slides.items():
            f = tmp / f"{k}.html"; f.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>{base}</style></head><body>{body}</body></html>")
            pg.goto(f"file://{f}"); pg.wait_for_timeout(300); pg.screenshot(path=str(tmp / f"{k}.png"))
        b.close()
    fc = ("[0:v]scale=1080:1920,zoompan=z='1+0.0006*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=96:s=1080x1920:fps=30,setsar=1[a];"
          "[1:v]scale=1080:1920,zoompan=z='1.03-0.0003*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=96:s=1080x1920:fps=30,setsar=1[b];"
          "[2:v]scale=1080:1920,fps=30,setsar=1[c];[a][b]xfade=transition=wiperight:duration=0.6:offset=2.6[ab];"
          "[ab][c]xfade=transition=fade:duration=0.5:offset=5.2,format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", "3.2", "-i", str(tmp / "a.png"),
                    "-loop", "1", "-t", "3.2", "-i", str(tmp / "b.png"), "-loop", "1", "-t", "2.4", "-i", str(tmp / "c.png"),
                    "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-movflags", "+faststart", "-r", "30", out], check=True)

if __name__ == "__main__":
    main(*sys.argv[1:6])
