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
html,body{width:1080px;height:1920px;overflow:hidden;background:#07080C}
body{font-family:"Noto Sans CJK JP",sans-serif;color:#fff;position:relative}
.bgimg{position:absolute;inset:-80px;background-size:cover;background-position:center;filter:blur(46px) brightness(.32) saturate(1.2);transform:scale(1.15)}
.vignette{position:absolute;inset:0;background:linear-gradient(180deg,rgba(7,8,12,.2) 0%,rgba(7,8,12,.55) 55%,rgba(7,8,12,.92) 100%)}
.progress{position:absolute;left:0;top:0;height:12px;background:#FFD400;z-index:5}
.top{position:absolute;left:60px;right:60px;top:78px;display:flex;justify-content:space-between;align-items:center;font-weight:900;font-size:36px;letter-spacing:.06em}
.tag{background:#FFD400;color:#07080C;padding:8px 22px;border-radius:8px}
.series{color:rgba(255,255,255,.8)}
.card{position:absolute;left:60px;right:60px;top:170px;height:980px;border-radius:30px;overflow:hidden;
  box-shadow:0 30px 80px rgba(0,0,0,.6),0 0 0 3px rgba(255,255,255,.12);background:#0F1117;
  animation:cardin .45s cubic-bezier(.2,1.3,.3,1) both}
.card img{width:100%;display:block;transform-origin:50% 30%}
@keyframes cardin{from{transform:translateY(40px) scale(.96);opacity:.0}to{transform:none;opacity:1}}
.cap{position:absolute;left:50px;right:50px;top:1180px;bottom:290px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center}
.chip{font-size:42px;font-weight:900;padding:10px 28px;border-radius:10px;margin-bottom:28px;background:#fff;color:#07080C;
  animation:pop .3s cubic-bezier(.2,1.6,.4,1) both}
.chip.red{background:#FF2D4F;color:#fff;animation:pop .3s cubic-bezier(.2,1.6,.4,1) both, blink .5s steps(2) .35s 3}
.lines{font-feature-settings:"palt";font-size:94px;font-weight:900;line-height:1.42}
.lines .l{display:block;animation:rise .38s cubic-bezier(.2,1.25,.3,1) both}
.lines .l:nth-child(2){animation-delay:.14s}.lines .l:nth-child(3){animation-delay:.28s}.lines .l:nth-child(4){animation-delay:.42s}
.lines .l>span.bx{background:#07080C;padding:0 22px;border-radius:10px;-webkit-box-decoration-break:clone;box-decoration-break:clone}
.hl{color:#FFD400}.red{color:#FF4D6A}
.sub{margin-top:30px;font-size:46px;font-weight:700;color:rgba(255,255,255,.88);animation:fade .4s ease .55s both}
.num{position:absolute;right:24px;top:200px;z-index:4;font-family:"Inter",sans-serif;font-weight:900;font-size:170px;line-height:1;
  color:#07080C;background:#FFD400;padding:6px 30px 14px;border-radius:24px;transform:rotate(4deg);
  animation:pop .35s cubic-bezier(.2,1.6,.4,1) both;box-shadow:0 14px 40px rgba(0,0,0,.5)}
.stats{display:flex;gap:26px;margin-bottom:26px}
.stat{background:#07080C;border-radius:18px;padding:18px 34px;animation:rise .4s cubic-bezier(.2,1.25,.3,1) both}
.stat:nth-child(2){animation-delay:.35s}
.stat .k{font-size:38px;color:rgba(255,255,255,.7);font-weight:700}
.stat .v{font-family:"Inter","Noto Sans CJK JP",sans-serif;font-size:96px;font-weight:900;line-height:1.1}
.ctabox{margin-top:30px;background:#FFD400;color:#07080C;font-size:56px;font-weight:900;padding:26px 40px;border-radius:18px;line-height:1.35;
  animation:pop .4s cubic-bezier(.2,1.6,.4,1) .5s both}
.handle{position:absolute;left:0;right:0;bottom:215px;text-align:center;font-size:34px;font-weight:700;color:rgba(255,255,255,.55)}
@keyframes pop{from{transform:scale(.4);opacity:0}to{transform:scale(1);opacity:1}}
@keyframes rise{from{transform:translateY(60px);opacity:0}to{transform:none;opacity:1}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes blink{50%{opacity:.3}}
"""
CARD_W, CARD_H = 960, 980


def lines(text):
    return "".join(f'<span class="l"><span class="bx">{ln}</span></span>' for ln in text.split("\n"))


def screen_anim(screen, dur):
    """Scroll tall screens through the card; slowly zoom short ones."""
    from PIL import Image
    w, h = Image.open(screen).size
    shown_h = h * CARD_W / w
    travel = max(0.0, shown_h - CARD_H)
    if travel > 40:
        travel = min(travel, 520 * dur)  # cap speed so text stays readable
        return f"@keyframes pan{{from{{transform:translateY(0)}}to{{transform:translateY(-{travel:.0f}px)}}}}.card img{{animation:pan {dur}s cubic-bezier(.45,0,.55,1) .25s both}}"
    return f"@keyframes pan{{from{{transform:scale(1.0)}}to{{transform:scale(1.05)}}}}.card img{{animation:pan {dur}s ease-out both}}"


def scene_html(s, tag, start, total):
    t = s["type"]
    sub = f'<div class="sub">{s["sub"]}</div>' if s.get("sub") else ""
    num = ""
    if t == "hook":
        cap = (f'<div class="chip red">{s["alert"]}</div>' if s.get("alert") else "") + f'<div class="lines">{lines(s["text"])}</div>' + sub
    elif t == "text":
        cap = (f'<div class="chip">{s["label"]}</div>' if s.get("label") else "") + f'<div class="lines">{lines(s["text"])}</div>' + sub
    elif t == "item":
        num = f'<div class="num">{s["n"]}</div>'
        cap = f'<div class="lines">{lines(s["text"])}</div>' + sub
    elif t == "stats":
        rows = "".join(f'<div class="stat"><div class="k">{k}</div><div class="v">{v}</div></div>' for k, v in s["rows"])
        cap = f'<div class="chip">{s["label"]}</div><div class="stats">{rows}</div>' + sub
    elif t == "cta":
        cap = f'<div class="lines">{lines(s["text"])}</div><div class="ctabox">{s["box"]}</div>'
    else:
        raise ValueError(t)
    dur = s["dur"]
    screen = (ROOT / "assets" / "screens" / f'{s["screen"]}.png').resolve()
    p0, p1 = start / total * 100, (start + dur) / total * 100
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><style>{CSS}
@keyframes prog{{from{{width:{p0:.3f}%}}to{{width:{p1:.3f}%}}}}
.progress{{animation:prog {dur}s linear both}}
{screen_anim(screen, dur)}
</style></head><body>
<div class="bgimg" style="background-image:url('{screen.as_uri()}')"></div><div class="vignette"></div>
<div class="progress"></div>
<div class="top"><span class="tag">{tag}</span><span class="series">{CONFIG['series']}</span></div>
<div class="card"><img src="{screen.as_uri()}"></div>{num}
<div class="cap">{cap}</div>
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
            htmlf = tmp / f"scene_{i:02d}.html"
            htmlf.write_text(scene_html(s, d.get("tag", ""), start, total), encoding="utf-8")
            page.goto(htmlf.as_uri(), wait_until="load")
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
