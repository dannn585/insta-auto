"""AXIS: リール下書き (axis/drafts/reels/YYYY-MM-DD.json) -> axis/queue/YYYY-MM-DD/reel.mp4 + cover.jpg + caption.txt

Usage: python axis/scripts/reel.py axis/drafts/reels/2026-11-05.json [--stills]

Scene types: hook / text / item / cta  (same fields as the main reel.py)
Optional per scene: "photo": "file.jpg" (axis/assets/photos/) -> 写真カードを上に表示。
写真がないシーンは文字を画面中央に大きく出す。
BGM は ../scripts/beat.py のオリジナル音源。
"""
import json
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
LOGO = (ROOT / "assets" / "logo.jpg").resolve().as_uri()
W, H, FPS = 1080, 1920, 30

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden}
body{font-family:"Noto Sans CJK JP",sans-serif;color:#111;position:relative;background:#EDE7E1}
.bg{position:absolute;inset:-40px;background-size:cover;background-position:center;filter:blur(3px);animation:kb 24s linear both}
.bg.fallback{background:radial-gradient(520px 380px at 18% 25%,#F6F1E8 0%,transparent 70%),radial-gradient(600px 420px at 80% 15%,#fff 0%,transparent 70%),radial-gradient(420px 360px at 85% 60%,#8C9A78 0%,transparent 70%),radial-gradient(560px 420px at 22% 70%,#9A7B62 0%,transparent 70%),radial-gradient(600px 300px at 55% 92%,#C9A88A 0%,transparent 70%),linear-gradient(180deg,#F3EFEA 0%,#D9CFC6 55%,#CDBFB2 100%);filter:blur(36px)}
.haze{position:absolute;inset:0;background:rgba(255,255,255,.62)}
.bg.photo{filter:none}.bg.photo+.haze{background:rgba(255,255,255,.12)}
.foot{position:absolute;left:0;bottom:150px;font-weight:900;font-size:76px;z-index:3}
.flogo{position:absolute;right:56px;bottom:130px;width:170px;height:170px;border-radius:50%;mix-blend-mode:multiply;z-index:3}
.orbit{position:absolute;border:6px solid rgba(17,17,17,.05);border-radius:50%;transform:rotate(-20deg)}
.o1{width:1700px;height:640px;left:-320px;top:560px;animation:spin 24s linear both}
.o2{width:1400px;height:500px;left:-60px;top:1180px;border-color:rgba(17,17,17,.04);animation:spin2 24s linear both}
.dot{position:absolute;width:44px;height:44px;border-radius:50%;background:#FF3131;box-shadow:0 0 30px rgba(255,49,49,.5);
  offset-path:path('M 0 0 C 300 -120 700 -120 1000 0');left:40px;top:1560px;animation:fly 24s linear both}
@keyframes spin{from{transform:rotate(-24deg)}to{transform:rotate(-14deg)}}
@keyframes spin2{from{transform:rotate(-16deg)}to{transform:rotate(-24deg)}}
@keyframes fly{from{offset-distance:0%}to{offset-distance:100%}}
.progress{position:absolute;left:0;top:0;height:12px;background:#38B6FF;z-index:5}
.top{position:absolute;left:60px;right:0;top:84px;display:flex;justify-content:flex-end;align-items:center;z-index:3}
.brand{display:none}
.brand img{width:92px;height:92px;border-radius:50%;mix-blend-mode:multiply}
.tag{display:none;background:#4F136B;color:#fff;font-weight:900;font-size:34px;padding:10px 26px;border-radius:999px}
.card{position:absolute;left:70px;right:70px;top:230px;height:860px;border-radius:30px;overflow:hidden;z-index:2;
  box-shadow:0 30px 80px rgba(0,0,0,.18);animation:cardin .45s cubic-bezier(.2,1.3,.3,1) both}
.card img{width:100%;height:100%;object-fit:cover;display:block;animation:kb 6s ease-out both}
@keyframes kb{from{transform:scale(1)}to{transform:scale(1.08)}}
@keyframes cardin{from{transform:translateY(40px) scale(.96);opacity:0}to{transform:none;opacity:1}}
.cap{position:absolute;left:50px;right:50px;top:300px;bottom:330px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;z-index:3}
.has-photo .cap{top:1130px;bottom:300px}
.chip{font-size:46px;font-weight:900;padding:12px 32px;border-radius:12px;margin-bottom:34px;background:#38B6FF;color:#fff;
  animation:pop .3s cubic-bezier(.2,1.6,.4,1) both}
.chip.red{background:#FF3131;color:#fff;animation:pop .3s cubic-bezier(.2,1.6,.4,1) both, blink .5s steps(2) .35s 3}
.lines{font-feature-settings:"palt";font-size:108px;font-weight:900;line-height:1.38}
.has-photo .lines{font-size:88px}
.lines .l{display:block;animation:rise .38s cubic-bezier(.2,1.25,.3,1) both}
.lines .l:nth-child(2){animation-delay:.14s}.lines .l:nth-child(3){animation-delay:.28s}.lines .l:nth-child(4){animation-delay:.42s}
.hl{color:#FF3131}.red{color:#FF3131}
.mark{color:#38B6FF}
.sub{margin-top:40px;font-size:50px;font-weight:700;color:#333;line-height:1.5;animation:fade .4s ease .55s both}
.num{font-family:"Inter",sans-serif;font-weight:900;font-size:210px;line-height:1;color:#fff;background:#38B6FF;
  padding:4px 46px 16px;border-radius:30px;margin-bottom:40px;transform:rotate(-4deg);
  animation:pop .35s cubic-bezier(.2,1.6,.4,1) both;box-shadow:0 14px 40px rgba(0,0,0,.15);position:relative}
.num::after{content:"";position:absolute;right:-18px;top:-18px;width:52px;height:52px;border-radius:50%;background:#FF3131}
.ctabox{margin-top:44px;background:#9DD7E6;color:#111;border-radius:60px;font-size:58px;font-weight:900;padding:30px 46px;border-radius:22px;line-height:1.4;
  animation:pop .4s cubic-bezier(.2,1.6,.4,1) .5s both}
.ctabox span{color:#FF3131}
.handle{display:none}
@keyframes pop{from{transform:scale(.4);opacity:0}to{transform:scale(1) rotate(var(--r,0));opacity:1}}
@keyframes rise{from{transform:translateY(60px);opacity:0}to{transform:none;opacity:1}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes blink{50%{opacity:.3}}
"""


def lines(text):
    return "".join(f'<span class="l">{ln}</span>' for ln in text.split("\n"))


def scene_html(s, tag, start, total):
    t = s["type"]
    sub = f'<div class="sub">{s["sub"].replace(chr(10), "<br>")}</div>' if s.get("sub") else ""
    if t == "hook":
        cap = (f'<div class="chip red">{s["alert"]}</div>' if s.get("alert") else "") + f'<div class="lines">{lines(s["text"])}</div>' + sub
    elif t == "text":
        cap = (f'<div class="chip">{s["label"]}</div>' if s.get("label") else "") + f'<div class="lines">{lines(s["text"])}</div>' + sub
    elif t == "item":
        cap = f'<div class="num" style="--r:-4deg">{s["n"]}</div><div class="lines">{lines(s["text"])}</div>' + sub
    elif t == "cta":
        cap = f'<div class="lines">{lines(s["text"])}</div><div class="ctabox">{s["box"]}</div>'
    else:
        raise ValueError(t)
    dur = s["dur"]
    p0, p1 = start / total * 100, (start + dur) / total * 100
    photo = ""
    if s.get("photo"):
        uri = (ROOT / "assets" / "photos" / s["photo"]).resolve().as_uri()
        photo = f'<div class="card"><img src="{uri}"></div>'
    bgp = ROOT / "assets" / "bg.jpg"
    bgcls, bgstyle = ("photo", f"background-image:url('{bgp.resolve().as_uri()}')") if bgp.exists() else ("fallback", "")
    # 背景の動きはリール全体で連続させる（シーン開始時刻ぶん先送り）
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><style>{CSS}
@keyframes prog{{from{{width:{p0:.3f}%}}to{{width:{p1:.3f}%}}}}
.progress{{animation:prog {dur}s linear both}}
.o1,.o2,.bg{{animation-delay:-{start:.2f}s}} .dot{{animation-delay:-{start:.2f}s}}
</style></head><body class="{'has-photo' if photo else ''}">
<div class="bg {bgcls}" style="{bgstyle}"></div><div class="haze"></div>
<div class="orbit o1"></div><div class="orbit o2"></div><div class="dot"></div>
<div class="progress"></div>
<div class="top"><div class="brand"><img src="{LOGO}">{CONFIG['short']}</div><span class="tag">{tag}</span></div>
{photo}
<div class="cap">{cap}</div>
<div class="handle">@{CONFIG['handle']}</div>
<div class="foot">business×{tag}</div><img class="flogo" src="{LOGO}">
</body></html>"""


def scrub(page, t):
    # ページ内の各アニメーションの delay を尊重したまま、シーン先頭からの経過時間 t に合わせる
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
            ff = subprocess.Popen(
                ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS),
                 "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                 "-pix_fmt", "yuv420p", "-r", str(FPS), str(part)], stdin=subprocess.PIPE)
            for f in range(nframes):
                scrub(page, f / FPS)
                ff.stdin.write(page.screenshot(type="jpeg", quality=92))
                if i == 0 and f == round(1.6 * FPS):
                    page.screenshot(path=str(out / "cover.jpg"), type="jpeg", quality=92)
            ff.stdin.close()
            if ff.wait() != 0:
                sys.exit(f"ffmpeg failed on scene {i}")
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
    subprocess.run([sys.executable, str(REPO / "scripts" / "beat.py"), str(beat), str(total)], check=True)
    final_tmp = tmp / "reel.tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(beat),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                    "-shortest", "-movflags", "+faststart", str(final_tmp)], check=True)
    final_tmp.rename(out / "reel.mp4")
    print(f"reel -> {out / 'reel.mp4'} ({total:.1f}s)")


if __name__ == "__main__":
    main()
