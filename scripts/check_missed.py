"""Missed post alert: fail (= GitHub sends Dan an email) if a past day's post is still waiting in queue/.

Checks queue/ (@dan_aishain) and axis/queue/ (@axis_doshisha). A folder dated before today (JST)
means that day's post was not published. TEST_ALERT=1 forces a failure to test the email.
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JST = timezone(timedelta(hours=9))
today = datetime.now(JST).strftime("%Y-%m-%d")

missed = []
for label, q in (("@dan_aishain", ROOT / "queue"), ("@axis_doshisha", ROOT / "axis" / "queue")):
    if q.is_dir():
        missed += [f"{label} {p.name}" for p in sorted(q.iterdir()) if p.is_dir() and p.name < today]

if os.environ.get("TEST_ALERT") == "1":
    missed.append("（テスト通知です。実際の投稿もれではありません）")

if missed:
    for m in missed:
        print(f"::error title=投稿されていない日があります::{m} が queue に残っています。Actions の手動実行で post_date を指定して投稿してください")
    sys.exit(1)
print(f"OK: {today} より前の投稿はすべて済んでいます")
