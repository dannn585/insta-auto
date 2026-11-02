"""Instagram API の共通部分。鍵の種類を見分けて、正しい接続先を選ぶ。

- IGAA… で始まる鍵（Instagramログインで発行）       → graph.instagram.com
- それ以外（EAA… など。統合ログイン/システムユーザー） → graph.facebook.com

Instagram のアカウントID は、鍵から分かればそれを使い、分からなければ
<ACCOUNT_DIR>/config.json の "ig_user_id"（または環境変数 IG_USER_ID）を使う。
"""
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
VERSION = os.environ.get("IG_API_VERSION", "v26.0")


class IG:
    def __init__(self, token, account_dir=""):
        self.token = token
        self.kind = "instagram" if token.startswith("IG") else "facebook"
        host = "graph.instagram.com" if self.kind == "instagram" else "graph.facebook.com"
        self.base = f"https://{host}/{VERSION}"
        print(f"Token: {token[:3]}… ({len(token)}文字) → {host}")
        cfg_path = (ROOT / account_dir if account_dir else ROOT) / "config.json"
        self.config = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
        self.ig_id = self._resolve_id()

    def call(self, method, path, **params):
        r = requests.request(method, f"{self.base}/{path}",
                             params={**params, "access_token": self.token}, timeout=60)
        try:
            data = r.json()
        except ValueError:
            data = {"raw": r.text[:500]}
        if r.status_code != 200 or "error" in data:
            sys.exit(f"API error on {path}: {json.dumps(data, ensure_ascii=False)}")
        return data

    def _resolve_id(self):
        if self.kind == "instagram":
            return str(self.call("GET", "me", fields="user_id")["user_id"])
        ig_id = os.environ.get("IG_USER_ID") or self.config.get("ig_user_id")
        if ig_id:
            return str(ig_id)
        # Facebookページ経由で連携している場合の探し方
        pages = self.call("GET", "me/accounts", fields="instagram_business_account").get("data", [])
        for p in pages:
            if p.get("instagram_business_account"):
                return p["instagram_business_account"]["id"]
        sys.exit("InstagramのアカウントIDが分かりません。config.json に ig_user_id を書いてください。")

    def profile(self):
        return self.call("GET", self.ig_id, fields="id,username,followers_count,media_count")
