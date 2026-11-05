"""AXIS: 投稿の下書き (axis/drafts/YYYY-MM-DD.json) -> axis/queue/YYYY-MM-DD/{1..n}.jpg + caption.txt

Usage: python axis/scripts/render.py axis/drafts/2026-11-04.json [more.json ...]

見た目はサークルのCanvaテンプレ（DAG8ijGL2Fc）に合わせた v2。強調：<em>赤</em> / <strong>水色</strong>
背景写真：axis/assets/bg.jpg（活動の写真）があれば白く薄めて使う。下書きの "bg" で個別指定も可。

Draft format (v2):
{
  "date": "2026-11-04", "tag": "お金", "caption": "...", "bg": "assets/bg.jpg"(任意),
  "slides": [
    {"type": "cover", "lines": ["<em>年金</em>・<em>税金</em>", "知らないと損する", "..."]},
    {"type": "text", "blocks": [["1行目", "2行目"], {"lines": ["・箇条書き"], "align": "left", "size": "s"}]},
    {"type": "cta", "blocks": [...], "bubble": "興味ある人はタップ<br>してDMください！"}
  ]
}
size: 省略=標準 / "s"=少し小さめ / "xs"=注釈
"""
import base64
import io
import json
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = (ROOT / "templates" / "slide.html").read_text(encoding="utf-8")
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


def data_uri(path):
    mime = "png" if path.suffix.lower() == ".png" else "jpeg"
    return f"data:image/{mime};base64," + base64.b64encode(path.read_bytes()).decode()


LOGO = data_uri(ROOT / "assets" / "logo.jpg")


def block_html(b):
    if isinstance(b, list):
        b = {"lines": b}
    cls = " ".join(c for c in ("block", b.get("size", ""), "left" if b.get("align") == "left" else "") if c)
    return f'<div class="{cls}">' + "<br>".join(b["lines"]) + "</div>"


def slide_body(s, tag):
    t = s["type"]
    if t == "cover":
        return (f'<div class="tag">{tag}</div>' if tag else "") + \
            '<div class="band"><div class="block">' + "<br>".join(s["lines"]) + "</div></div>"
    if t == "text":
        return '<div class="content">' + "".join(block_html(b) for b in s["blocks"]) + "</div>"
    if t == "cta":
        return ('<div class="content">' + "".join(block_html(b) for b in s.get("blocks", [])) + "</div>"
                + f'<img class="biglogo" src="{LOGO}">'
                + f'<div class="bubble">{s.get("bubble", "興味ある人はタップ<br>してDMください！")}</div>')
    raise ValueError(f"unknown slide type {t}")


def render(draft_path, page):
    d = json.loads(Path(draft_path).read_text(encoding="utf-8"))
    out = ROOT / "queue" / d["date"]
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.jpg"):
        old.unlink()
    n = len(d["slides"])
    bg_path = ROOT / d.get("bg", "assets/bg.jpg")
    bg = data_uri(bg_path) if bg_path.exists() else ""
    for i, s in enumerate(d["slides"], 1):
        foot = "" if s["type"] == "cta" else f'<div class="foot">business×大学</div><img class="logo" src="{LOGO}">'
        html = (TEMPLATE.replace("{{BGCLASS}}", "" if bg else "fallback")
                .replace("{{BGSTYLE}}", f"background-image:url('{bg}')" if bg else "")
                .replace("{{PAGE}}", f"{i} / {n}" if i > 1 else "")
                .replace("{{TYPE}}", s["type"])
                .replace("{{FOOT}}", foot)
                .replace("{{BODY}}", slide_body(s, d.get("tag", ""))))
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
