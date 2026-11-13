"""Dark code / terminal screens for the v1/v2 reels. Since 11/13 do not use them as the first screen
of a reel (style v3: light background, no code screen on the cover).

Build 'screen' images (code, terminal logs, notes, post grids) used as the visual layer of reels.

Everything shown is a real artifact of this project (its own code, logs and posts).
Usage: python scripts/screens.py   -> assets/screens/*.png
"""
import base64
import html
from pathlib import Path

from playwright.sync_api import sync_playwright
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer, YamlLexer

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "screens"
W = 960

BASE_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:%dpx;background:#0F1117;color:#E6E6E6;font-family:"Noto Sans CJK JP",sans-serif}
.bar{height:64px;display:flex;align-items:center;gap:14px;padding:0 26px;background:#1A1D27;border-bottom:1px solid #2A2E3B;font:600 26px "DejaVu Sans Mono",monospace;color:#9AA3B5}
.dot{width:18px;height:18px;border-radius:50%%}
.body{padding:30px 34px}
pre{font:25px/1.55 "DejaVu Sans Mono",monospace;white-space:pre-wrap;word-break:break-all}
.term .p{color:#7EE787}.term .c{color:#9AA3B5}.term .y{color:#FFD400}
.note h2{font-size:40px;font-weight:900;margin-bottom:26px;color:#FFD400}
.note li{list-style:none;font-size:32px;line-height:1.55;padding:18px 0;border-bottom:1px solid #2A2E3B}
.note li b{color:#fff}.note li span{color:#9AA3B5;font-size:26px;display:block}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.grid img{width:100%%;border-radius:10px;display:block}
""" % W


def window(title, inner, cls=""):
    dots = "".join(f'<span class="dot" style="background:{c}"></span>' for c in ("#FF5F57", "#FEBC2E", "#28C840"))
    return f'<div class="bar">{dots}<span style="margin-left:12px">{html.escape(title)}</span></div><div class="body {cls}">{inner}</div>'


def code(path, lexer, start=0, lines=70):
    src = "\n".join((ROOT / path).read_text(encoding="utf-8").splitlines()[start:start + lines])
    fmt = HtmlFormatter(style="monokai", nowrap=True)
    return window(path, f"<pre>{highlight(src, lexer, fmt)}</pre>"), fmt.get_style_defs("pre")


def img_tag(p):
    b64 = base64.b64encode(Path(p).read_bytes()).decode()
    return f'<img src="data:image/jpeg;base64,{b64}">'


def pages():
    yield "code_publish", *code("scripts/publish.py", PythonLexer(), 30, 75)
    yield "code_reel", *code("scripts/reel.py", PythonLexer(), 150, 70)
    yield "code_workflow", *code(".github/workflows/publish.yml", YamlLexer(), 0, 60)

    log = [("p", "$ python scripts/render.py drafts/2026-11-05.json"), ("c", "rendered 5 slides -> queue/2026-11-05"),
           ("p", "$ python scripts/reel.py drafts/reels/2026-11-03.json")]
    log += [("c", f"scene {i} done ({n} frames)") for i, n in enumerate([96, 84, 84, 96, 84, 102, 90])]
    log += [("y", "reel -> queue/2026-11-03/reel.mp4 (21.2s)"),
            ("p", "$ DRY_RUN=1 python scripts/publish.py"),
            ("c", "2026-11-03 REELS 1"), ("c", "2026-11-04 REELS 1"), ("c", "2026-11-05 IMAGE/CAROUSEL 5"),
            ("p", "$ git push -u origin main"), ("c", "To https://github.com/dannn585/insta-auto"),
            ("y", " * [new branch]      main -> main")]
    term = "<pre>" + "\n".join(f'<span class="{k}">{html.escape(t)}</span>' for k, t in log) + "</pre>"
    yield "terminal", window("terminal", term, "term"), ""

    summary = [("きっかけの動画", "コードが書けない40歳がAIに起業を丸投げした話"),
               ("最初の商品", "売上ゼロ。評価0のアカウントは誰にも見られない"),
               ("逆転", "コメント約200件から「欲しい」を発見"),
               ("作る前に売る", "前払い予約で需要を確認"),
               ("学び", "何を作るか探す / 先に売る / 全部見せる")]
    yield "notes_summary", window("notes / youtube-summary.md", '<div class="note"><h2>動画の要点</h2><ul>' + "".join(
        f"<li><b>{a}</b><span>{b}</span></li>" for a, b in summary) + "</ul></div>"), ""

    research = [("Claudeの神機能7選", "34万回"), ("Claude Codeで自動化できること8選", "33万回"),
                ("Claude使い方 神機能10選", "15万回"), ("Claude code×ショート動画自動化", "6万回"),
                ("AIで0円から1万円を目指す大学生", "223回"),
                ("型：最初の3秒で止める・番号付きリスト・音声＋BGM", "")]
    yield "notes_research", window("notes / research.md", '<div class="note"><h2>伸びてる動画の共通点</h2><ul>' + "".join(
        f"<li><b>{a}</b><span>{b}</span></li>" for a, b in research) + "</ul></div>"), ""

    slides = sorted((ROOT / "queue" / "2026-11-05").glob("[0-9].jpg"))
    yield "posts", window("queue/2026-11-05", '<div class="grid">' + "".join(img_tag(s) for s in slides) + "</div>"), ""

    stills = sorted((ROOT / ".build" / "2026-11-04").glob("still_*.jpg"))
    yield "reel_frames", window("queue/2026-11-04/reel.mp4", '<div class="grid">' + "".join(
        img_tag(s) for s in stills[:6]) + "</div>"), ""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": 800})
        for name, body, extra in pages():
            pg.set_content(f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE_CSS}{extra}</style></head>'
                           f"<body>{body}</body></html>", wait_until="load")
            pg.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
            print(name)
        b.close()


if __name__ == "__main__":
    main()
