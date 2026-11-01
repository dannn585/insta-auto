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

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "queue"
POSTED = ROOT / "posted"
API = f"https://graph.instagram.com/{os.environ.get('IG_API_VERSION', 'v26.0')}"
JST = timezone(timedelta(hours=9))


def api(method, path, token, **params):
    r = requests.request(method, f"{API}/{path}", params={**params, "access_token": token}, timeout=60)
    data = r.json()
    if r.status_code != 200 or "error" in data:
        sys.exit(f"API error on {path}: {json.dumps(data, ensure_ascii=False)}")
    return data


def wait_ready(container_id, token):
    for _ in range(72):  # up to 6 minutes (video processing takes a while)
        status = api("GET", container_id, token, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            sys.exit(f"Container {container_id} failed: {status}")
        time.sleep(5)
    sys.exit(f"Container {container_id} not ready in time")


def main():
    if os.environ.get("CHECK_ONLY") == "1":
        me = api("GET", "me", os.environ["IG_ACCESS_TOKEN"], fields="user_id,username,account_type")
        print(f"Token OK: @{me.get('username')} ({me.get('account_type')})")
        return
    date = os.environ.get("POST_DATE") or datetime.now(JST).strftime("%Y-%m-%d")
    folder = QUEUE / date
    if not folder.is_dir():
        print(f"No post queued for {date}. Nothing to do.")
        return

    caption = (folder / "caption.txt").read_text(encoding="utf-8").strip()
    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    base = f"https://raw.githubusercontent.com/{repo}/{branch}/queue/{date}"

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

    token = os.environ["IG_ACCESS_TOKEN"]
    ig_id = api("GET", "me", token, fields="user_id,username")["user_id"]

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
