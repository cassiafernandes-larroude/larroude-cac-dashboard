#!/usr/bin/env python3
"""
Step 2 — Pull Meta Ads daily spend for the 3 BR accounts (last 28 days).

BR accounts:
- act_1735567560524487 (Larroude Brasil)         -> reports in USD
- act_1975682443187483 (Larroude BR Pre-Order)   -> reports in BRL
- act_756931007040325  (Larroude BR Brand)       -> reports in BRL

Saves daily spend per account in BRL (USD account converted with fixed rate).
Output: meta_spend_daily.json  -> { "YYYY-MM-DD": <total_brl_spend>, ... }
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
    ("act_1735567560524487", "USD"),
    ("act_1975682443187483", "BRL"),
    ("act_756931007040325",  "BRL"),
]

# Conversion rate (rough, fixed). Refine later if needed.
USD_TO_BRL = 5.10

END = date.today() - timedelta(days=1)
START = END - timedelta(days=89)  # 90D pra alimentar janelas 28/60/90D

OUT_PATH = Path(__file__).parent / "meta_spend_daily.json"


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
    print(f"Window: {START} -> {END}")
    daily_brl = {}

    for acct, ccy in ACCOUNTS:
        print(f"  {acct} ({ccy})...")
        per_day = fetch_daily(acct)
        for d, spend in per_day.items():
            brl = spend * USD_TO_BRL if ccy == "USD" else spend
            daily_brl[d] = round(daily_brl.get(d, 0) + brl, 2)

    # fill gaps with 0
    cur = START
    while cur <= END:
        daily_brl.setdefault(cur.isoformat(), 0.0)
        cur += timedelta(days=1)

    OUT_PATH.write_text(json.dumps(daily_brl, indent=2, sort_keys=True), encoding="utf-8")
    total = sum(daily_brl.values())
    print(f"\nOK Saved daily spend (BRL). Total 28D: R$ {total:,.2f}")
    print(f"   -> {OUT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAIL {e}", file=sys.stderr)
        sys.exit(1)
