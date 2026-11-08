"""Render a v3 reel (Dan's recorded voice + readable screens) -> drafts/reels/<date>/reel.mp4, cover.jpg, caption.txt

v3 = company/marketing/panda-reels-v3.md: real voice, fixed title band on top, big readable "screen" card,
caption box below. Scenes are cut on the silences of the recording (silence shortened to ~0.2 s).

Usage: python scripts/reel_v3.py drafts/reels/2026-11-10.json
  needs: <same name>.cards.html  (<template id="..."> per card; "reasonsN" style = template "reasons" with N items shown)
Output goes to drafts/ (not queue/): the first reels of a new style are checked by Dan before queue/.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#07080C}
body{font-family:"Noto Sans JP","Yu Gothic","Meiryo",sans-serif;color:#fff;position:relative;font-feature-settings:"palt"}
.bg{position:absolute;inset:-80px;background-size:cover;background-position:center;filter:blur(30px) brightness(.38) saturate(1.1)}
.title{position:absolute;left:0;right:0;top:150px;height:190px;background:#07080C;display:flex;align-items:center;justify-content:center;
  font-size:60px;font-weight:900;text-align:center;line-height:1.25;padding:0 30px;white-space:nowrap}
.card{position:absolute;left:44px;right:44px;top:380px;height:930px;border-radius:30px;overflow:hidden;background:#F5F4EE;color:#1F1E1B;
  box-shadow:0 30px 80px rgba(0,0,0,.55)}
.cap{position:absolute;left:40px;right:40px;top:1350px;height:270px;display:flex;align-items:center;justify-content:center}
.cap span.t{background:#07080C;border-radius:18px;padding:18px 34px;font-size:78px;font-weight:900;line-height:1.3;text-align:center}
y{color:#FFD400}
.title y{color:#FFD400}
/* chat screen */
.chat{padding:46px 40px;display:flex;flex-direction:column;gap:30px;height:100%}
.chat.end{justify-content:flex-end}
.me{align-self:flex-end;max-width:92%;background:#E7E4DA;border-radius:28px;padding:24px 30px;font-size:44px;line-height:1.5;font-weight:500}
.me b{font-weight:900}
.quote{margin-top:14px;padding-left:18px;border-left:6px solid #B9B4A6;font-size:34px;color:#5A574F;line-height:1.5}
.ai{font-size:44px;line-height:1.6;font-weight:500}
.ai.small{font-size:36px;color:#5A574F}
.ai.dim{color:#8A867B}
.mark{background:linear-gradient(transparent 55%,#FFE15A 55%);font-weight:900}
.input{background:#fff;border:3px solid #D8D3C4;border-radius:30px;padding:34px 34px;font-size:48px;line-height:1.55;font-weight:500;min-height:300px}
.cur{display:inline-block;width:5px;height:52px;background:#1F1E1B;vertical-align:-8px;margin-left:4px}
ol.reasons{list-style:none;display:flex;flex-direction:column;gap:18px;counter-reset:r}
ol.reasons li{counter-increment:r;border-radius:20px;padding:16px 22px 16px 92px;position:relative;background:#fff;border:2px solid #E2DED2}
ol.reasons li::before{content:counter(r);position:absolute;left:22px;top:16px;width:52px;height:52px;border-radius:50%;background:#D7262E;color:#fff;
  font-weight:900;font-size:34px;display:flex;align-items:center;justify-content:center}
ol.reasons li b{display:block;font-size:44px;font-weight:900;line-height:1.35}
ol.reasons li span{display:block;font-size:31px;color:#5A574F;line-height:1.4}
ol.reasons li.new{background:#FFF3B0;border-color:#FFD400}
ol.reasons li.hide{visibility:hidden}
/* ES paper (hook) */
.paper{position:absolute;inset:40px;background:#fff;border-radius:10px;padding:56px 50px;box-shadow:0 6px 20px rgba(0,0,0,.12)}
.ptitle{font-size:40px;font-weight:900;border-bottom:3px solid #1F1E1B;padding-bottom:14px;margin-bottom:28px}
.paper p{font-size:40px;line-height:1.8;font-weight:500}
.paper s{text-decoration:line-through;text-decoration-color:#E0202E;text-decoration-thickness:6px}
.paper u{text-decoration:underline wavy #E0202E;text-decoration-thickness:4px;text-underline-offset:10px}
.note{position:absolute;color:#E0202E;font-weight:900;font-size:46px;transform:rotate(-6deg);border:5px solid #E0202E;border-radius:50px;padding:4px 22px;background:rgba(255,255,255,.85)}
.n1{right:40px;top:470px}.n2{left:30px;top:560px;transform:rotate(4deg)}.n3{left:30px;top:660px;transform:rotate(-3deg)}
.stamp{position:absolute;right:40px;bottom:36px;transform:rotate(-4deg);background:#E0202E;color:#fff;font-weight:900;font-size:46px;
  text-align:center;padding:14px 50px;border-radius:16px;line-height:1.2}
.stamp b{font-size:84px}
/* before / after */
.ba{padding:40px 38px;display:flex;flex-direction:column;gap:14px}
.box{border-radius:22px;padding:24px 28px;font-size:38px;line-height:1.6;position:relative}
.before{background:#E7E4DA;color:#6B675D}
.after{background:#fff;border:4px solid #FFD400;font-weight:500}
.lab{font-family:"Inter","Noto Sans JP",sans-serif;font-weight:900;font-size:30px;letter-spacing:.08em;margin-bottom:6px}
.before .lab{color:#8A867B}.after .lab{color:#D7262E}
.arrow{text-align:center;font-size:44px;color:#D7262E;line-height:1}
/* save card */
.save{padding:56px 46px;display:flex;flex-direction:column;gap:34px}
.slab{font-size:40px;font-weight:900;color:#D7262E}
.pr{background:#fff;border:3px solid #D8D3C4;border-radius:24px;padding:30px 32px;font-size:50px;line-height:1.55;font-weight:500}
.pr b{color:#D7262E;margin-right:10px}
.tip{font-size:34px;color:#5A574F;text-align:right}
"""


def templates(path):
    return dict(re.findall(r'<template id="([^"]+)">(.*?)</template>', path.read_text(encoding="utf-8"), re.S))


def card_html(name, tpl):
    m = re.fullmatch(r"reasons(\d)", name)
    if not m:
        return tpl[name]
    n = int(m.group(1))
    html = tpl["reasons"]
    i = 0

    def cls(_):
        nonlocal i
        i += 1
        return '<li class="new">' if i == n else ("<li>" if i < n else '<li class="hide">')
    return re.sub(r"<li>", cls, html)


def page(spec, tpl, step, bg_uri):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="bg" style="background-image:url('{bg_uri}')"></div>
<div class="title"><span>{spec['title']}</span></div>
<div class="card">{card_html(step['card'], tpl)}</div>
<div class="cap"><span class="t">{step['cap']}</span></div>
</body></html>"""


def data_uri(path):
    """Small JPEG as data: URI (file:// images do not load in set_content pages)."""
    import base64
    import io
    from PIL import Image
    im = Image.open(path).convert("RGB")
    im.thumbnail((540, 960))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    spec_path = (ROOT / sys.argv[1]).resolve() if not Path(sys.argv[1]).is_absolute() else Path(sys.argv[1])
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    tpl = templates(spec_path.with_suffix(".cards.html"))
    out = spec_path.parent / spec_path.stem
    out.mkdir(parents=True, exist_ok=True)
    voice = ROOT / spec["voice"]
    bg_uri = data_uri(ROOT / spec["background"])

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        # 1) stills, one per step; each step gets an equal share of its scene's speech
        items = []
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": W, "height": H})
            k = 0
            for sc in spec["scenes"]:
                a, z = sc["audio"]
                d = (z - a) / len(sc["steps"])
                for st in sc["steps"]:
                    f = td / f"s{k:03d}.png"
                    pg.set_content(page(spec, tpl, st, bg_uri), wait_until="load")
                    pg.wait_for_timeout(150)
                    pg.screenshot(path=str(f))
                    items.append((f, d))
                    k += 1
            b.close()
        # 2) video from stills (exact durations), 3) voice cut on the silences, 4) mux
        lst = td / "list.txt"
        lines = []
        for f, d in items:
            lines += [f"file '{f.as_posix()}'", f"duration {d:.3f}"]
        lines.append(f"file '{items[-1][0].as_posix()}'")
        lst.write_text("\n".join(lines), encoding="utf-8")
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
             "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "20", str(td / "v.mp4")])
        segs = [sc["audio"] for sc in spec["scenes"]]
        parts = "".join(f"[0:a]atrim={a}:{z},asetpts=PTS-STARTPTS[a{i}];" for i, (a, z) in enumerate(segs))
        fc = parts + "".join(f"[a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1,loudnorm=I=-14:TP=-1.5[out]"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(voice), "-filter_complex", fc, "-map", "[out]",
             "-ar", "48000", "-c:a", "aac", "-b:a", "192k", str(td / "a.m4a")])
        run(["ffmpeg", "-y", "-v", "error", "-i", str(td / "v.mp4"), "-i", str(td / "a.m4a"),
             "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(out / "reel.mp4")])
        run(["ffmpeg", "-y", "-v", "error", "-i", str(items[0][0]), "-q:v", "3", str(out / "cover.jpg")])
    (out / "caption.txt").write_text(spec["caption"], encoding="utf-8")
    print(out / "reel.mp4")


if __name__ == "__main__":
    main()
