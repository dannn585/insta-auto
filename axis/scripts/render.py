"""AXIS: 投稿の下書き (axis/drafts/YYYY-MM-DD.json) -> axis/queue/YYYY-MM-DD/{1..n}.jpg + caption.txt

Usage: python axis/scripts/render.py axis/drafts/2026-11-04.json [more.json ...]

Draft format:
{
  "date": "2026-11-04", "tag": "社会制度", "caption": "...",
  "slides": [
    {"type": "cover", "kicker": "...", "title": "...<em>強調</em>...", "sub": "..."},
    {"type": "text", "heading": "...", "items": ["...", {"text": "...", "note": "..."}]},
    {"type": "cta", "title": "...", "box": "...<span>強調</span>...<b>DM</b>..."}
  ]
}
"""
import io
import json
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = (ROOT / "templates" / "slide.html").read_text(encoding="utf-8")
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
import base64
LOGO = "data:image/jpeg;base64," + base64.b64encode((ROOT / "assets" / "logo.jpg").read_bytes()).decode()


def slide_body(s):
    t = s["type"]
    if t == "cover":
        return ((f'<div class="kicker">{s["kicker"]}</div>' if s.get("kicker") else "")
                + f'<div class="title">{s["title"]}</div>'
                + (f'<div class="sub">{s["sub"]}</div>' if s.get("sub") else ""))
    if t == "text":
        lis = []
        for i, it in enumerate(s["items"], 1):
            text, note = (it, "") if isinstance(it, str) else (it["text"], it.get("note", ""))
            lis.append(f'<li><span class="num">{i}</span><div>{text}'
                       + (f"<small>{note}</small>" if note else "") + "</div></li>")
        return f'<div class="heading">{s["heading"]}</div><ul class="items">{"".join(lis)}</ul>'
    if t == "cta":
        return f'<div class="title">{s["title"]}</div><div class="cta-box">{s["box"]}</div>'
    raise ValueError(f"unknown slide type {t}")


def render(draft_path, page):
    d = json.loads(Path(draft_path).read_text(encoding="utf-8"))
    out = ROOT / "queue" / d["date"]
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.jpg"):
        old.unlink()
    n = len(d["slides"])
    for i, s in enumerate(d["slides"], 1):
        html = (TEMPLATE.replace("{{TAG}}", d.get("tag", CONFIG["short"]))
                .replace("{{NAME}}", CONFIG["name"])
                .replace("{{HANDLE}}", CONFIG["handle"])
                .replace("{{LOGO}}", LOGO)
                .replace("{{PAGE}}", f"{i:02d} / {n:02d}")
                .replace("{{SWIPE}}", "スワイプ →" if i < n else "")
                .replace("{{TYPE}}", s["type"])
                .replace("{{BODY}}", slide_body(s)))
        page.set_content(html, wait_until="load")
        png = page.screenshot(clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
        Image.open(io.BytesIO(png)).convert("RGB").save(out / f"{i}.jpg", "JPEG", quality=92)
    (out / "caption.txt").write_text(d["caption"].strip() + "\n", encoding="utf-8")
    print(f"rendered {n} slides -> {out}")


if __name__ == "__main__":
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        for f in sys.argv[1:]:
            render(f, pg)
        b.close()
