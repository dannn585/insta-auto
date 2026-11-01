"""Render a reel draft (drafts/reels/YYYY-MM-DD.json) into queue/YYYY-MM-DD/reel.mp4 + cover.jpg + caption.txt.

Usage: python scripts/reel.py drafts/reels/2026-11-03.json [--stills]

Each scene is an HTML page whose CSS animations are paused and scrubbed frame by frame
(document.getAnimations().currentTime), piped as JPEGs into ffmpeg -> one mp4 per scene,
then concatenated and muxed with a generated beat (scripts/beat.py).
"""
import json
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
W, H, FPS = 1080, 1920, 30

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0A0C12}
body{font-family:"Noto Sans CJK JP",sans-serif;color:#fff;position:relative}
.bg{position:absolute;inset:-200px;background-image:
  linear-gradient(rgba(255,255,255,.06) 2px,transparent 2px),
  linear-gradient(90deg,rgba(255,255,255,.06) 2px,transparent 2px);
  background-size:90px 90px;animation:drift 6s linear infinite}
@keyframes drift{to{transform:translate(90px,90px)}}
.glow{position:absolute;border-radius:50%;filter:blur(140px);opacity:.55}
.g1{width:900px;height:900px;background:#2B4CFF;left:-300px;top:-200px;animation:float1 6s ease-in-out infinite alternate}
.g2{width:800px;height:800px;background:#FF3B5C;right:-320px;bottom:-160px;animation:float2 6s ease-in-out infinite alternate}
@keyframes float1{to{transform:translate(160px,220px)}}
@keyframes float2{to{transform:translate(-180px,-200px)}}
.progress{position:absolute;left:0;top:0;height:14px;background:#FFD400}
.top{position:absolute;left:70px;right:70px;top:120px;display:flex;justify-content:space-between;align-items:center;font-weight:900;font-size:40px;letter-spacing:.06em}
.tag{background:#FFD400;color:#0A0C12;padding:10px 26px;border-radius:8px}
.series{color:rgba(255,255,255,.75)}
.handle{position:absolute;left:0;right:0;bottom:260px;text-align:center;font-size:38px;font-weight:700;color:rgba(255,255,255,.6)}
.stage{position:absolute;left:70px;right:70px;top:300px;bottom:380px;display:flex;flex-direction:column;justify-content:center}
.label{align-self:flex-start;font-size:46px;font-weight:900;background:#fff;color:#0A0C12;padding:12px 30px;border-radius:10px;margin-bottom:46px;
  animation:pop .35s cubic-bezier(.2,1.6,.4,1) both}
.big{font-feature-settings:"palt";font-size:118px;font-weight:900;line-height:1.25;letter-spacing:-.01em;text-shadow:0 8px 0 rgba(0,0,0,.45)}
.big .line{display:block;animation:rise .45s cubic-bezier(.2,1.2,.3,1) both}
.big .line:nth-child(2){animation-delay:.18s}.big .line:nth-child(3){animation-delay:.36s}.big .line:nth-child(4){animation-delay:.54s}
.hl{color:#FFD400}.red{color:#FF4D6A}
.box{display:inline;background:#0A0C12;box-shadow:0 0 0 18px #0A0C12;}
.sub{margin-top:60px;font-size:54px;font-weight:700;color:rgba(255,255,255,.85);line-height:1.5;animation:fade .5s ease .7s both}
.alert{align-self:flex-start;font-size:50px;font-weight:900;background:#FF2D4F;padding:14px 32px;border-radius:10px;margin-bottom:50px;
  animation:pop .35s cubic-bezier(.2,1.6,.4,1) both, blink .5s steps(2) .4s 3}
.num{font-family:"Inter",sans-serif;font-weight:900;font-size:300px;line-height:1;color:#FFD400;margin-bottom:30px;
  animation:pop .4s cubic-bezier(.2,1.6,.4,1) both;text-shadow:0 12px 0 rgba(0,0,0,.4)}
.meter{margin-top:70px;height:56px;border:6px solid #fff;border-radius:40px;overflow:hidden}
.meter i{display:block;height:100%;width:1.5%;background:#FFD400}
.stat{display:flex;justify-content:space-between;align-items:baseline;font-weight:900;margin-bottom:30px}
.stat .k{font-size:56px;color:rgba(255,255,255,.75)}
.stat .v{font-family:"Inter","Noto Sans CJK JP",sans-serif;font-size:120px}
.stat:nth-child(1){animation:rise .45s cubic-bezier(.2,1.2,.3,1) both}
.stat:nth-child(2){animation:rise .45s cubic-bezier(.2,1.2,.3,1) .5s both}
.ctabox{margin-top:70px;background:#FFD400;color:#0A0C12;font-size:64px;font-weight:900;padding:40px 46px;border-radius:20px;line-height:1.4;
  animation:pop .4s cubic-bezier(.2,1.6,.4,1) .6s both}
@keyframes pop{from{transform:scale(.4);opacity:0}to{transform:scale(1);opacity:1}}
@keyframes rise{from{transform:translateY(80px);opacity:0}to{transform:none;opacity:1}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes blink{50%{opacity:.25}}
@keyframes grow{from{width:0}}
"""


def lines(text):
    return "".join(f'<span class="line">{ln}</span>' for ln in text.split("\n"))


def scene_html(s, tag, start, total):
    t = s["type"]
    if t == "hook":
        body = ((f'<div class="alert">{s["alert"]}</div>' if s.get("alert") else "")
                + f'<div class="big">{lines(s["text"])}</div>'
                + (f'<div class="sub">{s["sub"]}</div>' if s.get("sub") else ""))
    elif t == "text":
        body = ((f'<div class="label">{s["label"]}</div>' if s.get("label") else "")
                + f'<div class="big">{lines(s["text"])}</div>'
                + (f'<div class="sub">{s["sub"]}</div>' if s.get("sub") else ""))
    elif t == "item":
        body = (f'<div class="num">{s["n"]}</div><div class="big">{lines(s["text"])}</div>'
                + (f'<div class="sub">{s["sub"]}</div>' if s.get("sub") else ""))
    elif t == "stats":
        rows = "".join(f'<div class="stat"><span class="k">{k}</span><span class="v">{v}</span></div>'
                       for k, v in s["rows"])
        body = (f'<div class="label">{s["label"]}</div>{rows}'
                f'<div class="meter"><i style="animation:grow 1s ease 1s both"></i></div>'
                + (f'<div class="sub">{s["sub"]}</div>' if s.get("sub") else ""))
    elif t == "cta":
        body = f'<div class="big">{lines(s["text"])}</div><div class="ctabox">{s["box"]}</div>'
    else:
        raise ValueError(t)
    dur = s["dur"]
    # progress bar: linear from start/total to (start+dur)/total over this scene
    p0, p1 = start / total * 100, (start + dur) / total * 100
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><style>{CSS}
@keyframes prog{{from{{width:{p0:.3f}%}}to{{width:{p1:.3f}%}}}}
.progress{{animation:prog {dur}s linear both}}
</style></head><body>
<div class="bg"></div><div class="glow g1"></div><div class="glow g2"></div>
<div class="progress"></div>
<div class="top"><span class="tag">{tag}</span><span class="series">{CONFIG['series']}</span></div>
<div class="stage">{body}</div>
<div class="handle">@{CONFIG['handle']}</div>
</body></html>"""


def scrub(page, t):
    page.evaluate("t => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t; })", t * 1000)


def main():
    draft = Path(sys.argv[1])
    stills = "--stills" in sys.argv
    d = json.loads(draft.read_text(encoding="utf-8"))
    out = ROOT / "queue" / d["date"]
    tmp = ROOT / ".build" / d["date"]
    out.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)
    total = sum(s["dur"] for s in d["scenes"])

    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": W, "height": H})
        start = 0.0
        parts = []
        for i, s in enumerate(d["scenes"]):
            page.set_content(scene_html(s, d.get("tag", ""), start, total), wait_until="load")
            if stills:
                scrub(page, min(2.0, s["dur"] - .1))
                page.screenshot(path=str(tmp / f"still_{i}.jpg"), type="jpeg", quality=90)
                if i == 0:
                    page.screenshot(path=str(out / "cover.jpg"), type="jpeg", quality=92)
                start += s["dur"]
                continue
            nframes = round(s["dur"] * FPS)
            part = tmp / f"scene_{i:02d}.mp4"
            part_tmp = tmp / f"scene_{i:02d}.tmp.mp4"
            ff = subprocess.Popen(
                ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS),
                 "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                 "-pix_fmt", "yuv420p", "-r", str(FPS), str(part_tmp)], stdin=subprocess.PIPE)
            for f in range(nframes):
                scrub(page, f / FPS)
                ff.stdin.write(page.screenshot(type="jpeg", quality=92))
                if i == 0 and f == round(1.6 * FPS):
                    page.screenshot(path=str(out / "cover.jpg"), type="jpeg", quality=92)
            ff.stdin.close()
            if ff.wait() != 0:
                sys.exit(f"ffmpeg failed on scene {i}")
            part_tmp.rename(part)
            parts.append(part)
            start += s["dur"]
            print(f"scene {i} done ({nframes} frames)")
        b.close()

    (out / "caption.txt").write_text(d["caption"].strip() + "\n", encoding="utf-8")
    if stills:
        print(f"stills in {tmp}")
        return

    listfile = tmp / "list.txt"
    listfile.write_text("".join(f"file '{p.name}'\n" for p in parts))
    video = tmp / "video.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listfile),
                    "-c", "copy", str(video)], check=True)
    beat = tmp / "beat.wav"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "beat.py"), str(beat), str(total)], check=True)
    final_tmp = tmp / "reel.tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(beat),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                    "-shortest", "-movflags", "+faststart", str(final_tmp)], check=True)
    final_tmp.rename(out / "reel.mp4")
    print(f"reel -> {out / 'reel.mp4'} ({total:.1f}s)")


if __name__ == "__main__":
    main()
