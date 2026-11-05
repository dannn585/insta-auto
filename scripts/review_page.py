"""投稿予定（queue/ と axis/queue/）を1ページで確認できる HTML を作る。

Usage: python scripts/review_page.py [出力フォルダ]（既定: .build/review）
出力: index.html と media/（画像・動画のコピー）。Claude の確認ページとして公開する用。
"""
import html
import json
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".build" / "review"
WEEK = "月火水木金土日"

ACCOUNTS = [
    {"key": "panda", "name": "@panda.7475341", "dir": ROOT / "queue", "time": "毎日 19:30〜23:59 の間",
     "note": "自動投稿 稼働中"},
    {"key": "axis", "name": "@axis_doshisha（AXIS）", "dir": ROOT / "axis" / "queue", "time": "毎日 20:30〜23:59 の間",
     "note": "AXISの鍵が未登録のため、自動投稿は停止中"},
]


def collect(acc):
    posts = []
    if not acc["dir"].exists():
        return posts
    for d in sorted(p for p in acc["dir"].iterdir() if p.is_dir()):
        imgs = sorted(d.glob("[0-9]*.jpg"), key=lambda p: int(p.stem))
        reel = d / "reel.mp4"
        cover = d / "cover.jpg"
        cap = (d / "caption.txt").read_text(encoding="utf-8").strip() if (d / "caption.txt").exists() else ""
        files = []
        for f in ([cover, reel] if reel.exists() else imgs):
            if f.exists():
                rel = f"media/{acc['key']}-{d.name}-{f.name}"
                (OUT / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, OUT / rel)
                files.append(rel)
        posts.append({"date": d.name, "kind": "リール" if reel.exists() else f"カルーセル {len(imgs)}枚",
                      "is_reel": reel.exists(), "files": files, "caption": cap})
    return posts


def jp_date(s):
    try:
        d = date.fromisoformat(s)
        return f"{d.month}/{d.day}（{WEEK[d.weekday()]}）"
    except ValueError:
        return s


def card(p):
    if p["is_reel"]:
        cover, video = p["files"]
        media = f'<video controls playsinline preload="none" poster="{cover}" src="{video}"></video>'
    else:
        media = '<div class="strip">' + "".join(
            f'<img loading="lazy" src="{f}" alt="{i}枚目" data-full="{f}">' for i, f in enumerate(p["files"], 1)) + "</div>"
    cap = html.escape(p["caption"])
    return f"""<article class="post">
  <header><span class="date">{jp_date(p['date'])}</span><span class="kind {'reel' if p['is_reel'] else ''}">{p['kind']}</span></header>
  {media}
  <details><summary>キャプションを見る</summary><pre>{cap}</pre>
  <button class="copy" data-cap="{cap}">キャプションをコピー</button></details>
</article>"""


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    sections, counts = [], []
    for acc in ACCOUNTS:
        posts = collect(acc)
        counts.append(f'<a href="#{acc["key"]}">{acc["name"]} <b>{len(posts)}本</b></a>')
        body = "".join(card(p) for p in posts) or '<p class="empty">投稿予定はありません</p>'
        sections.append(f"""<section id="{acc['key']}">
  <h2>{acc['name']}</h2>
  <p class="meta">{acc['time']}に投稿 ・ {acc['note']}</p>
  {body}
</section>""")
    stamp = datetime.now().strftime("%Y/%m/%d %H:%M")
    page = TEMPLATE.replace("{{COUNTS}}", "".join(counts)).replace("{{SECTIONS}}", "".join(sections)).replace("{{STAMP}}", stamp)
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print(f"-> {OUT}/index.html")


TEMPLATE = """<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>投稿予定の確認</title>
<style>
  :root{--ink:#14171c;--sub:#68707d;--line:#e4e6ea;--bg:#f6f7f9;--blue:#2f7fd8;--red:#e5484d}
  *{box-sizing:border-box;margin:0}
  body{font-family:system-ui,-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;color:var(--ink);background:var(--bg);line-height:1.6}
  .wrap{max-width:980px;margin:0 auto;padding:28px 18px 80px}
  h1{font-size:24px;letter-spacing:.02em}
  .stamp{color:var(--sub);font-size:13px;margin-top:4px}
  nav{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 6px}
  nav a{background:#fff;border:1px solid var(--line);border-radius:999px;padding:6px 14px;color:var(--ink);text-decoration:none;font-size:14px}
  section{margin-top:34px}
  h2{font-size:19px;padding-bottom:6px;border-bottom:2px solid var(--ink)}
  .meta{color:var(--sub);font-size:13px;margin:8px 0 14px}
  .post{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px;margin-bottom:16px}
  .post header{display:flex;align-items:center;gap:10px;margin-bottom:10px}
  .date{font-weight:800;font-size:17px}
  .kind{font-size:12px;font-weight:700;padding:2px 10px;border-radius:999px;background:#eef3fb;color:var(--blue)}
  .kind.reel{background:#fdeeee;color:var(--red)}
  .strip{display:flex;gap:8px;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:6px}
  .strip img{height:300px;aspect-ratio:4/5;object-fit:cover;border-radius:8px;scroll-snap-align:start;cursor:zoom-in;border:1px solid var(--line);flex:none}
  video{width:min(100%,300px);aspect-ratio:9/16;border-radius:10px;background:#000;display:block}
  details{margin-top:10px}
  summary{cursor:pointer;color:var(--blue);font-size:14px;font-weight:600}
  pre{white-space:pre-wrap;font-family:inherit;font-size:14px;background:var(--bg);border-radius:8px;padding:12px;margin-top:8px}
  .copy{margin-top:8px;border:1px solid var(--line);background:#fff;border-radius:8px;padding:6px 12px;font-size:13px;cursor:pointer}
  .empty{color:var(--sub)}
  #zoom{position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;align-items:center;justify-content:center;z-index:9;padding:16px}
  #zoom img{max-width:100%;max-height:100%;border-radius:8px}
  #zoom.on{display:flex}
  @media (max-width:600px){.strip img{height:240px}}
</style></head>
<body><div class="wrap">
  <h1>投稿予定の確認</h1>
  <p class="stamp">{{STAMP}} 時点のGitHub（insta-auto）の中身。画像は横にスクロール、押すと拡大</p>
  <nav>{{COUNTS}}</nav>
  {{SECTIONS}}
</div>
<div id="zoom"><img alt=""></div>
<script>
  const z=document.getElementById('zoom'), zi=z.querySelector('img');
  document.querySelectorAll('.strip img').forEach(i=>i.addEventListener('click',()=>{zi.src=i.dataset.full;z.classList.add('on')}));
  z.addEventListener('click',()=>z.classList.remove('on'));
  document.querySelectorAll('.copy').forEach(b=>b.addEventListener('click',async()=>{
    try{await navigator.clipboard.writeText(b.dataset.cap);b.textContent='コピーしました'}catch(e){b.textContent='コピーできませんでした'}
    setTimeout(()=>b.textContent='キャプションをコピー',1800)}));
</script>
</body></html>"""

if __name__ == "__main__":
    main()
