#!/usr/bin/env python3
"""
Step 2 (US) — Pull Meta Ads daily spend for the 3 US accounts (last 28 days).

US accounts (all USD, no conversion):
- act_2047856822417350 (Larroudé US)
- act_929449929417505  (PRE-ORDER US)
- act_312869193575906  (Larroude New)

Output: meta_spend_daily_us.json -> { "YYYY-MM-DD": <total_usd_spend>, ... }
"""

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv("C:/Projects/.env")

TOKEN = os.environ["META_ACCESS_TOKEN"]
GRAPH = "https://graph.facebook.com/v19.0"

ACCOUNTS = [
    "act_2047856822417350",
    "act_929449929417505",
    "act_312869193575906",
]

END = date.today() - timedelta(days=1)
START = END - timedelta(days=89)  # 90D pra alimentar janelas 28/60/90D

OUT_PATH = Path(__file__).parent / "meta_spend_daily_us.json"


def fetch_daily(account):
    url = f"{GRAPH}/{account}/insights"
    params = {
        "access_token": TOKEN,
        "level": "account",
        "fields": "spend",
        "time_increment": 1,
        "time_range": json.dumps({"since": START.isoformat(), "until": END.isoformat()}),
        "limit": 200,
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    data = r.json().get("data", [])
    return {row["date_start"]: float(row.get("spend") or 0) for row in data}


def main():
    print(f"[US] Window: {START} -> {END}")
    daily_usd = {}

    for acct in ACCOUNTS:
        print(f"  {acct}...")
        per_day = fetch_daily(acct)
        for d, spend in per_day.items():
            daily_usd[d] = round(daily_usd.get(d, 0) + spend, 2)

    cur = START
    while cur <= END:
        daily_usd.setdefault(cur.isoformat(), 0.0)
        cur += timedelta(days=1)

    OUT_PATH.write_text(json.dumps(daily_usd, indent=2, sort_keys=True), encoding="utf-8")
    total = sum(daily_usd.values())
    print(f"\nOK Saved daily spend (USD). Total 28D: $ {total:,.2f}")
    print(f"   -> {OUT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAIL {e}", file=sys.stderr)
        sys.exit(1)
