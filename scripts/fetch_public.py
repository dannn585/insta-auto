"""自分の鍵（@dan_aishain（旧 @panda.7475341））で、他のプロアカウントの「公開投稿」を読み込む。

Instagram公式API の Business Discovery を使う。相手の鍵は不要。
相手がビジネス／クリエイターアカウントで、こちらが統合ログイン（EAA…）の鍵なら使える。

保存物（fetch_posts.py と同じ形式）:
  <ACCOUNT_DIR>/reference/posts.json          … プロフィール＋投稿（キャプション・日時・いいね・コメント・URL）
  <ACCOUNT_DIR>/reference/media/<id>_<n>.jpg  … 画像（動画はサムネイル。取れないものはスキップ）

Env: IG_ACCESS_TOKEN（自分の鍵・必須）, TARGET_USERNAME（例: axis_doshisha）, ACCOUNT_DIR（保存先。例: axis）
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
TARGET = os.environ.get("TARGET_USERNAME", "").lstrip("@").strip()
OUT = (ROOT / ACCOUNT_DIR if ACCOUNT_DIR else ROOT) / "reference"

PROFILE = "username,name,biography,website,followers_count,follows_count,media_count,profile_picture_url"
MEDIA_FULL = ("id,caption,media_type,media_product_type,media_url,thumbnail_url,permalink,timestamp,"
              "like_count,comments_count,children{media_type,media_url,thumbnail_url}")
MEDIA_LITE = "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count"


def discover(ig, media_fields, after=None):
    media = f"media.limit(25){{{media_fields}}}" if not after else f"media.after({after}).limit(25){{{media_fields}}}"
    r = requests.get(f"{ig.base}/{ig.ig_id}", timeout=60, params={
        "fields": f"business_discovery.username({TARGET}){{{PROFILE},{media}}}",
        "access_token": ig.token,
    })
    data = r.json()
    if r.status_code != 200 or "error" in data:
        return None, data.get("error", data)
    return data["business_discovery"], None


def main():
    token = os.environ.get("IG_ACCESS_TOKEN")
    if not token:
        sys.exit("::error::GitHub の Secret「IG_ACCESS_TOKEN」が未設定です")
    if not TARGET:
        sys.exit("::error::TARGET_USERNAME（読み込む相手のユーザー名）を指定してください")
    if token.startswith("IG"):
        sys.exit("::error::Instagramログイン（IGAA…）の鍵では Business Discovery が使えません。統合ログイン（EAA…）の鍵が必要です")

    ig = IG(token)  # 自分（main）の config.json の ig_user_id を使う
    fields = MEDIA_FULL
    bd, err = discover(ig, fields)
    if err:  # 一部の項目（children など）が拒否されたら、最小構成でやり直す
        print(f"詳細項目つきで失敗 → 最小構成で再試行: {json.dumps(err, ensure_ascii=False)}")
        fields = MEDIA_LITE
        bd, err = discover(ig, fields)
    if err:
        hint = ""
        if err.get("code") == 110 or "business" in str(err.get("message", "")).lower():
            hint = "（相手がビジネス／クリエイターアカウントでない、またはユーザー名の誤りの可能性）"
        sys.exit(f"::error::Business Discovery 失敗{hint}: {json.dumps(err, ensure_ascii=False)}")

    posts = list(bd.get("media", {}).get("data", []))
    after = bd.get("media", {}).get("paging", {}).get("cursors", {}).get("after")
    while after:
        page, err = discover(ig, fields, after)
        if err or not page:
            print(f"続きの取得で停止: {err}")
            break
        posts += page.get("media", {}).get("data", [])
        nxt = page.get("media", {}).get("paging", {})
        after = nxt.get("cursors", {}).get("after") if nxt.get("next") else None

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
                try:
                    f.write_bytes(requests.get(src, timeout=60).content)
                except requests.RequestException as e:
                    print(f"画像の保存に失敗 {p['id']}_{n}: {e}")
                    continue
            p["files"].append(f"media/{f.name}")
        for k in ("media_url", "thumbnail_url"):
            p.pop(k, None)  # 期限付きURLは保存しない
        p.pop("children", None)

    account = {k: v for k, v in bd.items() if k not in ("media", "profile_picture_url")}
    account["fetched_via"] = "business_discovery"
    (OUT / "posts.json").write_text(json.dumps({"account": account, "posts": posts}, ensure_ascii=False, indent=2),
                                    encoding="utf-8")
    print(f"@{account.get('username')}: フォロワー{account.get('followers_count')} / {len(posts)}件 -> {OUT}")


if __name__ == "__main__":
    main()
