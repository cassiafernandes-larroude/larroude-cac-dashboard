#!/usr/bin/env python3
"""
Step 1 (US) — Pull Shopify US orders for last 28 days via Admin GraphQL API.
Saves orders_raw_us.json (same schema as orders_raw.json).
"""

import json
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv("C:/Projects/.env")

SHOP = os.environ["SHOPIFY_US_STORE_DOMAIN"]
TOKEN = os.environ["SHOPIFY_US_ADMIN_API_TOKEN"]
VERSION = os.environ.get("SHOPIFY_API_VERSION", "2025-01")

ENDPOINT = f"https://{SHOP}/admin/api/{VERSION}/graphql.json"
HEADERS = {"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"}

END = date.today() - timedelta(days=1)
START = END - timedelta(days=27)
START_ISO = datetime.combine(START, datetime.min.time(), tzinfo=timezone.utc).isoformat()
END_ISO = datetime.combine(END + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc).isoformat()

OUT_PATH = Path(__file__).parent / "orders_raw_us.json"

QUERY = """
query Orders($cursor: String, $query: String!) {
  orders(first: 100, after: $cursor, query: $query, sortKey: CREATED_AT) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id
      name
      createdAt
      displayFinancialStatus
      cancelledAt
      customer {
        id
        numberOfOrders
      }
      lineItems(first: 50) {
        nodes {
          quantity
          product { id title }
          variant { id sku }
          originalTotalSet { shopMoney { amount currencyCode } }
          discountedTotalSet { shopMoney { amount } }
        }
      }
    }
  }
}
"""


def gql(query, variables):
    for attempt in range(5):
        r = requests.post(ENDPOINT, headers=HEADERS, json={"query": query, "variables": variables}, timeout=60)
        if r.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        d = r.json()
        if "errors" in d:
            raise RuntimeError(d["errors"])
        cost = d.get("extensions", {}).get("cost", {})
        avail = cost.get("throttleStatus", {}).get("currentlyAvailable", 1000)
        if avail < 200:
            time.sleep(1.5)
        return d["data"]
    raise RuntimeError("Rate limited too many times")


def main():
    print(f"[US] Window: {START} -> {END}  ({(END - START).days + 1} days)")
    query_str = f"created_at:>='{START_ISO}' AND created_at:<'{END_ISO}'"

    cursor = None
    orders = []
    page = 0
    while True:
        page += 1
        data = gql(QUERY, {"cursor": cursor, "query": query_str})
        block = data["orders"]
        nodes = block["nodes"]
        orders.extend(nodes)
        print(f"  page {page}: {len(nodes)} orders  (total {len(orders)})")
        if not block["pageInfo"]["hasNextPage"]:
            break
        cursor = block["pageInfo"]["endCursor"]

    OUT_PATH.write_text(json.dumps(orders, indent=2), encoding="utf-8")
    print(f"\nOK Saved {len(orders)} orders -> {OUT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAIL {e}", file=sys.stderr)
        sys.exit(1)
