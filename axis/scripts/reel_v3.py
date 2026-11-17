"""AXIS リール v3（積み上げチェックリスト型・効果音だけ）

Usage:
  python axis/scripts/reel_v3.py axis/drafts/reels/v3/2026-11-25.json [--out DIR] [--audio sfx|silent|bgm] [--stills]

- 出力先：--out を省くと axis/queue/<date>/（自動投稿の置き場）。下書き確認は --out で drafts 側に出す
- 出力：reel.mp4（音つき）・reel_mute.mp4（無音。アプリで流行りの音源を付けて手動投稿する用）・cover.jpg・caption.txt
- v2（reel.py）との違い（2026-11-17）
  1. 1フレーム目から題名が全部見えている（出だしのアニメーションなし）。スキップ率 88〜96% 対策
  2. あるあるの項目を同じ画面に1つずつ積み上げる（チェックリスト）。題名は上に出たまま
  3. 尺を約18秒 → 約12〜15秒に短く
  4. 動く飾り（輪・赤い点）をやめ、文字だけに目が行くようにする
  5. 音は自作BGMをやめ、項目が出るときの小さな「ポン」だけ（--audio sfx。著作権の心配なし）

Draft JSON:
{
  "date": "2026-11-25", "tag": "大学",
  "hook": {"alert": "1・2回生へ", "title": "大学生の\\n<span class=\\"hl\\">12月</span>あるある", "sub": "1つでも当てはまったら最後まで見て"},
  "items": ["12月の予定<br><span class=\\"hl\\">バイトと忘年会</span>だけ", ...],   # 3〜5個。1〜2行
  "turn": {"label": "今年はちがう冬に", "text": "...", "sub": "..."},
  "cta":  {"text": "...", "box": "...", "note": "参加は完全に任意・Zoom・興味ある回だけでOK"},
  "caption": "..."
}
"""
import argparse
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
LOGO = (ROOT / "assets" / "logo.jpg").resolve().as_uri()
BG = ROOT / "assets" / "bg.jpg"
W, H, FPS, SR = 1080, 1920, 30, 48000

HOOK_ALONE = 1.3      # 題名だけの時間
HOLD_AFTER = 1.2      # 全部出そろってから
TURN_DUR = 2.6
CTA_DUR = 3.0
FADE = 0.22

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden}
body{font-family:"Noto Sans CJK JP",sans-serif;color:#111;position:relative;background:#F3F1EE;font-feature-settings:"palt"}
.bg{position:absolute;inset:0;background-size:cover;background-position:center}
.haze{position:absolute;inset:0;background:rgba(255,255,255,.62)}
.progress{position:absolute;left:0;top:0;height:10px;background:#38B6FF;z-index:9}
.foot{position:absolute;left:40px;bottom:150px;font-weight:900;font-size:72px;z-index:3}
.flogo{position:absolute;right:56px;bottom:130px;width:160px;height:160px;border-radius:50%;mix-blend-mode:multiply;z-index:3}
.grp{position:absolute;left:0;right:0;top:0;bottom:0;z-index:4}
.band{position:absolute;left:0;right:0;top:200px;padding:34px 60px 40px;background:#DFF1F5;text-align:center}
.chip{display:inline-block;font-size:44px;font-weight:900;padding:8px 30px;border-radius:12px;background:#FF3131;color:#fff;margin-bottom:18px}
.title{font-size:100px;font-weight:900;line-height:1.3}
.hl{color:#FF3131}.mark{color:#38B6FF}
.hsub{position:absolute;left:60px;right:60px;top:var(--subtop);text-align:center;font-size:48px;font-weight:700;color:#333}
.list{position:absolute;left:60px;right:60px;top:var(--listtop)}
.row{display:flex;align-items:center;gap:28px;background:rgba(255,255,255,.94);border-radius:24px;padding:26px 34px;margin-bottom:26px;
  box-shadow:0 10px 30px rgba(0,0,0,.08);border-left:14px solid #38B6FF}
.row .ck{flex:none;width:76px;height:76px;border-radius:50%;background:#FF3131;color:#fff;font-size:50px;font-weight:900;
  display:flex;align-items:center;justify-content:center;font-family:"Segoe UI Symbol","Noto Sans CJK JP",sans-serif}
.row .tx{font-size:var(--fs);font-weight:900;line-height:1.32}
.center{position:absolute;left:50px;right:50px;top:330px;bottom:520px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center}
.label{font-size:48px;font-weight:900;padding:12px 34px;border-radius:12px;background:#38B6FF;color:#fff;margin-bottom:38px}
.big{font-size:104px;font-weight:900;line-height:1.36}
.csub{margin-top:40px;font-size:52px;font-weight:700;color:#333;line-height:1.5}
.ctabox{margin-top:46px;background:#9DD7E6;color:#111;font-size:62px;font-weight:900;padding:30px 50px;border-radius:24px;line-height:1.4}
.ctabox span{color:#FF3131}
.note{margin-top:34px;font-size:42px;font-weight:700;color:#333}
@keyframes show{from{opacity:0}to{opacity:1}}
@keyframes hide{from{opacity:1}to{opacity:0}}
@keyframes slide{from{opacity:0;transform:translateX(70px)}to{opacity:1;transform:none}}
@keyframes ckpop{0%{transform:scale(.3)}70%{transform:scale(1.15)}100%{transform:scale(1)}}
@keyframes dim{from{opacity:1}to{opacity:.78}}
"""


def plain(s):
    return re.sub(r"<[^>]+>", "", s).replace("\n", "")


def timeline(d):
    """各項目が出る時刻と、全体の区切りを返す"""
    t = HOOK_ALONE
    starts = []
    for it in d["items"]:
        starts.append(t)
        t += min(2.6, max(1.6, 0.8 + len(plain(it)) / 10))
    list_end = t + HOLD_AFTER
    turn_end = list_end + TURN_DUR
    total = turn_end + CTA_DUR
    return starts, list_end, turn_end, total


def build_html(d):
    starts, list_end, turn_end, total = timeline(d)
    n = len(d["items"])
    two_line = any("<br>" in it for it in d["items"])
    fs = 58 if (n >= 5 or (n >= 4 and two_line)) else 64
    title_lines = d["hook"]["title"].count("\n") + 1
    band_bottom = 200 + 34 + (62 if d["hook"].get("alert") else 0) + int(100 * 1.3 * title_lines) + 40
    subtop = band_bottom + 50
    listtop = band_bottom + 60
    rows = []
    for i, (it, st) in enumerate(zip(d["items"], starts)):
        nxt = starts[i + 1] if i + 1 < n else None
        dim = f",dim .3s ease {nxt:.2f}s forwards" if nxt is not None else ""
        rows.append(
            f'<div class="row" style="animation:slide .2s ease-out {st:.2f}s both{dim}">'
            f'<div class="ck" style="animation:ckpop .3s ease-out {st + .05:.2f}s both">✓</div>'
            f'<div class="tx">{it}</div></div>')
    h = d["hook"]
    alert = f'<div class="chip">{h["alert"]}</div><br>' if h.get("alert") else ""
    hsub = (f'<div class="hsub" style="animation:hide .2s ease {starts[0]:.2f}s both">{h["sub"]}</div>'
            if h.get("sub") else "")
    tr, ct = d["turn"], d["cta"]
    turn_sub = f'<div class="csub">{tr["sub"]}</div>' if tr.get("sub") else ""
    cta_note = f'<div class="note">{ct["note"]}</div>' if ct.get("note") else ""
    bg = f'<div class="bg" style="background-image:url(\'{BG.resolve().as_uri()}\')"></div>' if BG.exists() else ""
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><style>{CSS}
@keyframes prog{{from{{width:0%}}to{{width:100%}}}}
.progress{{animation:prog {total:.2f}s linear both}}
</style></head><body style="--fs:{fs}px;--subtop:{subtop}px;--listtop:{listtop}px">
{bg}<div class="haze"></div><div class="progress"></div>
<div class="grp" style="animation:hide {FADE}s ease {list_end:.2f}s both">
  <div class="band">{alert}<div class="title">{h["title"].replace(chr(10), "<br>")}</div></div>
  {hsub}
  <div class="list">{''.join(rows)}</div>
</div>
<div class="grp" style="animation:show {FADE}s ease {list_end:.2f}s both,hide {FADE}s ease {turn_end:.2f}s forwards">
  <div class="center"><div class="label">{tr["label"]}</div><div class="big">{tr["text"].replace(chr(10), "<br>")}</div>{turn_sub}</div>
</div>
<div class="grp" style="animation:show {FADE}s ease {turn_end:.2f}s both">
  <div class="center"><div class="big">{ct["text"].replace(chr(10), "<br>")}</div><div class="ctabox">{ct["box"]}</div>{cta_note}</div>
</div>
<div class="foot">business×{d.get("tag", "")}</div><img class="flogo" src="{LOGO}">
</body></html>""", total


def tone(freqs, dur, decay, amp):
    t = np.arange(int(SR * dur)) / SR
    w = sum(np.sin(2 * np.pi * f * t) * (0.6 ** k) for k, f in enumerate(freqs))
    att = np.minimum(t / 0.004, 1.0)
    return w * att * np.exp(-t / decay) * amp


def make_audio(path, d, total, mode):
    n = int(SR * total)
    mix = np.zeros(n)
    if mode == "sfx":
        starts, list_end, turn_end, _ = timeline(d)

        def put(sig, at):
            i = int(at * SR)
            j = min(n, i + len(sig))
            mix[i:j] += sig[: j - i]
        put(tone([520, 1040], .5, .12, .22), 0.05)                       # 出だしの合図（やわらかい1音）
        for k, st in enumerate(starts):
            put(tone([880 + 60 * k, 1760 + 120 * k], .25, .05, .20), st)   # ポン（少しずつ高く）
        put(tone([659.3, 1318.5], .9, .25, .16), list_end)                # ころん（場面転換）
        put(tone([783.99, 1567.98], .9, .25, .14), list_end + .12)
        put(tone([659.3, 1318.5], 1.2, .35, .15), turn_end)               # 最後の画面
        put(tone([987.77, 1975.5], 1.2, .35, .13), turn_end + .14)
        mix = np.clip(mix, -0.9, 0.9)
    elif mode == "bgm":
        subprocess.run([sys.executable, str(REPO / "scripts" / "beat.py"), str(path), str(total)], check=True)
        return
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("--out")
    ap.add_argument("--audio", default="sfx", choices=["sfx", "silent", "bgm"])
    ap.add_argument("--stills", action="store_true")
    a = ap.parse_args()
    d = json.loads(Path(a.draft).read_text(encoding="utf-8"))
    out = Path(a.out) if a.out else ROOT / "queue" / d["date"]
    tmp = ROOT / ".build" / ("v3_" + d["date"])
    out.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)
    html, total = build_html(d)
    htmlf = tmp / "reel.html"
    htmlf.write_text(html, encoding="utf-8")
    starts, list_end, turn_end, _ = timeline(d)
    still_times = {"0_first": 0.0, "1_list": list_end - .1, "2_turn": turn_end - .3, "3_cta": total - .1}

    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": W, "height": H})
        page.goto(htmlf.as_uri(), wait_until="load")
        page.evaluate("document.fonts.ready")

        def at(t):
            page.evaluate("t => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t; })", t * 1000)

        at(0.6)
        page.screenshot(path=str(out / "cover.jpg"), type="jpeg", quality=92)
        for name, t in still_times.items():
            at(t)
            page.screenshot(path=str(tmp / f"still_{name}.jpg"), type="jpeg", quality=88)
        if a.stills:
            b.close()
            print(f"stills in {tmp}")
            return
        video = tmp / "video.mp4"
        ff = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS),
             "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
             "-pix_fmt", "yuv420p", "-r", str(FPS), str(video)], stdin=subprocess.PIPE)
        for f in range(round(total * FPS)):
            at(f / FPS)
            ff.stdin.write(page.screenshot(type="jpeg", quality=92))
        ff.stdin.close()
        if ff.wait() != 0:
            sys.exit("ffmpeg failed")
        b.close()

    (out / "caption.txt").write_text(d["caption"].strip() + "\n", encoding="utf-8")

    def mux(wav, dest):
        tmpf = tmp / (dest.stem + ".tmp.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(wav),
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                        "-shortest", "-movflags", "+faststart", str(tmpf)], check=True)
        tmpf.replace(dest)

    wav = tmp / "audio.wav"
    make_audio(wav, d, total, a.audio)
    mux(wav, out / "reel.mp4")
    if a.audio != "silent":
        mute = tmp / "mute.wav"
        make_audio(mute, d, total, "silent")
        mux(mute, out / "reel_mute.mp4")
    print(f"reel -> {out / 'reel.mp4'} ({total:.1f}s, audio={a.audio})")


if __name__ == "__main__":
    main()
