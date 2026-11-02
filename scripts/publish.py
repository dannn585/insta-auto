"""Publish today's queued post to Instagram via the official Instagram API (Instagram Login).

Queue layout:
  queue/YYYY-MM-DD/reel.mp4 (+cover.jpg)  -> Reel
  queue/YYYY-MM-DD/1.jpg, 2.jpg, ...      -> 1 image = single post, 2-10 = carousel
  queue/YYYY-MM-DD/caption.txt

Runs in GitHub Actions. Images are served to Instagram from raw.githubusercontent.com,
so the repository must be public and the images already pushed to the default branch.

Env:
  IG_ACCESS_TOKEN  (required, GitHub secret)
  GITHUB_REPOSITORY / GITHUB_REF_NAME (set automatically by Actions)
  IG_API_VERSION   (optional, default v26.0)
  POST_DATE        (optional, YYYY-MM-DD; default = today in Asia/Tokyo)
  DRY_RUN=1        (optional, print what would happen without calling the API)
"""
import json
import os
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from igapi import IG  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
# ACCOUNT_DIR を指定すると別アカウント用のフォルダ（例: axis）を使う
ACCOUNT_DIR = os.environ.get("ACCOUNT_DIR", "").strip("/")
QUEUE = ROOT / ACCOUNT_DIR / "queue" if ACCOUNT_DIR else ROOT / "queue"
POSTED = QUEUE.parent / "posted"
JST = timezone(timedelta(hours=9))


IG_CLIENT = None


def api(method, path, token, **params):
    return IG_CLIENT.call(method, path, **params)


def wait_ready(container_id, token):
    for _ in range(72):  # up to 6 minutes (video processing takes a while)
        status = api("GET", container_id, token, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            sys.exit(f"Container {container_id} failed: {status}")
        time.sleep(5)
    sys.exit(f"Container {container_id} not ready in time")


def missing_token():
    secret = "AXIS_IG_ACCESS_TOKEN" if ACCOUNT_DIR == "axis" else "IG_ACCESS_TOKEN"
    msg = f"GitHub の Secret「{secret}」が未設定です（Settings → Secrets and variables → Actions で登録）"
    if ACCOUNT_DIR:  # サブアカウントは鍵が届くまでスキップ扱い
        print(f"::warning::{msg}。投稿をスキップしました。")
        return
    sys.exit(f"::error::{msg}")


def main():
    global IG_CLIENT
    if os.environ.get("CHECK_ONLY") == "2":  # 投稿の手前（下書きコンテナ作成）まで試す。公開はしない
        token = os.environ.get("IG_ACCESS_TOKEN")
        if not token:
            return missing_token()
        IG_CLIENT = IG(token, ACCOUNT_DIR)
        folders = sorted(p for p in QUEUE.iterdir() if p.is_dir()) if QUEUE.is_dir() else []
        if not folders:
            sys.exit("テストに使う予約投稿（queue/）がありません")
        f = folders[0]
        repo = os.environ["GITHUB_REPOSITORY"]
        prefix = f"{ACCOUNT_DIR}/" if ACCOUNT_DIR else ""
        base = f"https://raw.githubusercontent.com/{repo}/main/{prefix}queue/{f.name}"
        if (f / "reel.mp4").exists():
            params = dict(media_type="REELS", video_url=f"{base}/reel.mp4", caption="test")
        else:
            params = dict(image_url=f"{base}/1.jpg", caption="test")
        print(f"Testing with {f.name} ({params.get('media_type', 'IMAGE')})")
        cid = api("POST", f"{IG_CLIENT.ig_id}/media", token, **params)["id"]
        wait_ready(cid, token)
        print(f"Publish test OK: container {cid} is ready (not published)")
        return
    if os.environ.get("CHECK_ONLY") == "1":
        if not os.environ.get("IG_ACCESS_TOKEN"):
            return missing_token()
        me = IG(os.environ["IG_ACCESS_TOKEN"], ACCOUNT_DIR).profile()
        print(f"Token OK: @{me.get('username')} (followers {me.get('followers_count')}, posts {me.get('media_count')})")
        return
    date = os.environ.get("POST_DATE") or datetime.now(JST).strftime("%Y-%m-%d")
    folder = QUEUE / date
    if not folder.is_dir():
        print(f"No post queued for {date}. Nothing to do.")
        return

    caption = (folder / "caption.txt").read_text(encoding="utf-8").strip()
    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    prefix = f"{ACCOUNT_DIR}/" if ACCOUNT_DIR else ""
    base = f"https://raw.githubusercontent.com/{repo}/{branch}/{prefix}queue/{date}"

    is_reel = (folder / "reel.mp4").exists()
    images = [] if is_reel else sorted(
        (p for p in folder.glob("*.jpg") if p.stem.isdigit()), key=lambda p: int(p.stem))
    if not is_reel and not 1 <= len(images) <= 10:
        sys.exit(f"{folder}: need reel.mp4 or 1-10 numbered .jpg images, found {len(images)}")
    urls = [f"{base}/reel.mp4"] if is_reel else [f"{base}/{p.name}" for p in images]

    if os.environ.get("DRY_RUN") == "1":
        print(json.dumps({"date": date, "type": "REELS" if is_reel else "IMAGE/CAROUSEL",
                          "urls": urls, "caption": caption}, ensure_ascii=False, indent=2))
        return

    token = os.environ.get("IG_ACCESS_TOKEN")
    if not token:
        return missing_token()
    IG_CLIENT = IG(token, ACCOUNT_DIR)
    ig_id = IG_CLIENT.ig_id

    if is_reel:
        params = dict(media_type="REELS", video_url=urls[0], caption=caption, share_to_feed="true")
        if (folder / "cover.jpg").exists():
            params["cover_url"] = f"{base}/cover.jpg"
        creation_id = api("POST", f"{ig_id}/media", token, **params)["id"]
    elif len(urls) == 1:
        creation_id = api("POST", f"{ig_id}/media", token, image_url=urls[0], caption=caption)["id"]
    else:
        children = []
        for u in urls:
            cid = api("POST", f"{ig_id}/media", token, image_url=u, is_carousel_item="true")["id"]
            wait_ready(cid, token)
            children.append(cid)
        creation_id = api("POST", f"{ig_id}/media", token, media_type="CAROUSEL",
                          children=",".join(children), caption=caption)["id"]

    wait_ready(creation_id, token)
    media_id = api("POST", f"{ig_id}/media_publish", token, creation_id=creation_id)["id"]
    print(f"Published {date}: media id {media_id}")

    POSTED.mkdir(exist_ok=True)
    dest = POSTED / date
    shutil.move(str(folder), str(dest))
    (dest / "result.json").write_text(
        json.dumps({"media_id": media_id, "published_at": datetime.now(JST).isoformat()}, indent=2),
        encoding="utf-8")


if __name__ == "__main__":
    main()
