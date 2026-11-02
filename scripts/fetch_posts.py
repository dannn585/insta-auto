"""自分のアカウントの過去投稿を Instagram公式API で取得し、<ACCOUNT_DIR>/reference/ に保存する。

保存物:
  reference/posts.json            … キャプション・投稿日時・いいね数・コメント数・URL
  reference/media/<id>_<n>.jpg    … 画像（動画はサムネイル）

Env: IG_ACCESS_TOKEN（必須）, ACCOUNT_DIR（例: axis）, IG_API_VERSION（任意）
"""
import json
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from igapi import IG  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ACCOUNT_DIR = os.environ.get("ACCOUNT_DIR", "").strip("/")
OUT = (ROOT / ACCOUNT_DIR if ACCOUNT_DIR else ROOT) / "reference"
FIELDS = ("id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count,"
          "children{media_type,media_url,thumbnail_url}")


def get(url, **params):
    r = requests.get(url, params=params, timeout=60)
    data = r.json()
    if r.status_code != 200 or "error" in data:
        sys.exit(f"API error: {json.dumps(data, ensure_ascii=False)}")
    return data


def main():
    token = os.environ.get("IG_ACCESS_TOKEN")
    if not token:
        secret = "AXIS_IG_ACCESS_TOKEN" if ACCOUNT_DIR == "axis" else "IG_ACCESS_TOKEN"
        sys.exit(f"::error::GitHub の Secret「{secret}」が未設定です（Settings → Secrets and variables → Actions で登録）")
    ig = IG(token, ACCOUNT_DIR)
    me = ig.profile()
    posts, url, params = [], f"{ig.base}/{ig.ig_id}/media", dict(fields=FIELDS, limit=50, access_token=token)
    while url:
        page = get(url, **params)
        posts += page.get("data", [])
        url, params = page.get("paging", {}).get("next"), {}

    media_dir = OUT / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    for p in posts:
        items = p.get("children", {}).get("data") or [p]
        p["files"] = []
        for n, it in enumerate(items, 1):
            src = it.get("thumbnail_url") if it.get("media_type") == "VIDEO" else it.get("media_url")
            if not src:
                continue
            f = media_dir / f"{p['id']}_{n}.jpg"
            if not f.exists():
                f.write_bytes(requests.get(src, timeout=60).content)
            p["files"].append(f"media/{f.name}")
        for k in ("media_url", "thumbnail_url"):
            p.pop(k, None)  # 期限付きURLは保存しない
        p.pop("children", None)

    (OUT / "posts.json").write_text(json.dumps({"account": me, "posts": posts}, ensure_ascii=False, indent=2),
                                    encoding="utf-8")
    print(f"@{me.get('username')}: {len(posts)} posts -> {OUT}")


if __name__ == "__main__":
    main()
