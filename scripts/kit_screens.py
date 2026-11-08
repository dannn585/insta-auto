"""Build the large, readable 'screen' images for the kit-launch reels (T40, v3 style).

v3 rule: the top card must show "input -> result" in letters big enough to read on a phone.
Content mirrors the real files of this project (CLAUDE.md, tasks.md, proposals.md, the agent list),
shortened and with personal details removed.
Usage: python scripts/kit_screens.py   -> assets/screens/kit_*.png  (does not touch other screens)
"""
import html
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "screens"
W = 960

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:960px;background:#0F1117;color:#E6E6E6;font-family:"Noto Sans CJK JP","Yu Gothic UI","Meiryo",sans-serif}
.bar{height:64px;display:flex;align-items:center;gap:14px;padding:0 26px;background:#1A1D27;border-bottom:1px solid #2A2E3B;font:600 26px "DejaVu Sans Mono",Consolas,monospace;color:#9AA3B5}
.dot{width:18px;height:18px;border-radius:50%}
.body{padding:34px 36px 40px}
.day{font-size:28px;color:#9AA3B5;font-weight:700;margin:6px 0 12px}
.me,.ai{font-size:38px;line-height:1.5;padding:22px 28px;border-radius:22px;margin-bottom:22px;max-width:86%}
.me{background:#2B5BD7;color:#fff;margin-left:auto}
.ai{background:#1F2330;border:1px solid #2F3445}
.ai b,.hl{color:#FFD400}
.ai ol{margin:10px 0 0 1.3em}.ai li{margin:8px 0}
.x{color:#FF4D6A;font-weight:900}
.file pre{font:34px/1.6 Consolas,"DejaVu Sans Mono",monospace;white-space:pre-wrap}
.file .h{color:#FFD400;font-weight:700}.file .c{color:#9AA3B5}
table{width:100%;border-collapse:collapse;font-size:32px}
td,th{border-bottom:1px solid #2A2E3B;padding:16px 10px;text-align:left}
th{color:#9AA3B5;font-size:26px}
.ok{color:#7EE787;font-weight:700}.wait{color:#FFD400;font-weight:700}
.org{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.boss{grid-column:1/3;text-align:center;background:#FFD400;color:#07080C;border-radius:20px;padding:24px;font-size:44px;font-weight:900}
.boss span{display:block;font-size:30px;font-weight:700}
.dept{background:#1F2330;border:1px solid #2F3445;border-radius:20px;padding:22px 24px}
.dept b{display:block;font-size:38px;color:#fff}.dept span{font-size:28px;color:#9AA3B5}
.tree pre{font:36px/1.65 Consolas,"DejaVu Sans Mono",monospace}
"""


def window(title, inner, cls=""):
    dots = "".join(f'<span class="dot" style="background:{c}"></span>' for c in ("#FF5F57", "#FEBC2E", "#28C840"))
    return f'<div class="bar">{dots}<span style="margin-left:12px">{html.escape(title)}</span></div><div class="body {cls}">{inner}</div>'


def pages():
    # ① problem: retyping the same intro every day (how it was before)
    intro = "私は大学生で、Instagramをやってて、目標は…"
    days = "".join(f'<div class="day">11/0{d}</div><div class="me">{intro}</div>' for d in (1, 2, 3))
    yield "kit_retype", window("Claude（前の使い方）", days + '<div class="ai">はい、よろしくお願いします。<br>まずは状況を教えてください。</div>')

    # ① / ② the rule file that remembers it
    md = ('<pre><span class="h"># 自己紹介</span>\n- 名前はダン。大学生\n- 回答は日本語で\n\n'
          '<span class="h"># 毎日のルール</span>\n- 始める前に tasks.md と\n  前日の日報を読む\n- 終わったら日報を書く\n\n'
          '<span class="h"># 秘書</span>\n- 朝は「次にやること」を\n  3つまで提案する</pre>')
    yield "kit_claudemd", window("my-company/CLAUDE.md", md, "file")

    # ①② morning: "おはよう" -> 3 proposals -> "1でOK"
    chat = ('<div class="me">おはよう</div>'
            '<div class="ai">おはようございます。昨日の日報の続きから、今日は<b>3つ</b>です。<ol>'
            '<li>11/10からの投稿を作る<br><span style="color:#9AA3B5;font-size:30px">予約が11/09で切れるため・1〜2時間</span></li>'
            '<li>投稿もれの予備を用意<br><span style="color:#9AA3B5;font-size:30px">昨日は23:56でギリギリ・20分</span></li>'
            '<li>コメント文案を作る<br><span style="color:#9AA3B5;font-size:30px">期限が今日・30分</span></li></ol></div>'
            '<div class="me">1でOK</div>'
            '<div class="ai">了解です。始めます。</div>')
    yield "kit_morning", window("秘書リン", chat)

    # ② the task table the secretary reads
    rows = [("投稿づくり（11/10〜）", "進行中", "wait"), ("投稿もれの予備", "完了", "ok"),
            ("投稿もれのメール通知", "完了", "ok"), ("プロフィール変更", "完了", "ok"), ("コメント文案", "未着手", "")]
    t = "<table><tr><th>タスク</th><th>状態</th></tr>" + "".join(
        f'<tr><td>{a}</td><td class="{c}">{b}</td></tr>' for a, b, c in rows) + "</table>"
    yield "kit_tasks", window("my-company/tasks.md", t)

    # ③ the 6-person company
    depts = [("リサーチ", "伸びてる投稿を調べる"), ("クリエイティブ", "台本・画像を作る"), ("コミュニティ", "コメント・DMの返信案"),
             ("マーケティング", "LINE・販売までの流れ"), ("プロダクト", "売る商品を作る")]
    org = ('<div class="org"><div class="boss">秘書<span>窓口・振り分け・日報</span></div>'
           + "".join(f'<div class="dept"><b>{a}</b><span>{b}</span></div>' for a, b in depts) + "</div>")
    yield "kit_org", window("AI社員6人の会社", org)

    # ③ start with one: the folder for "secretary only"
    tree = ('<pre>my-company/\n├─ CLAUDE.md     <span class="hl">会社のルール</span>\n├─ agents/\n'
            '│   └─ secretary.md <span class="hl">秘書</span>\n├─ tasks.md      タスク表\n└─ reports/      日報</pre>')
    yield "kit_folder", window("最初はこれだけ", tree, "tree")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": 800})
        for name, body in pages():
            pg.set_content(f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head>'
                           f"<body>{body}</body></html>", wait_until="load")
            pg.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
            print(name)
        b.close()


if __name__ == "__main__":
    main()
