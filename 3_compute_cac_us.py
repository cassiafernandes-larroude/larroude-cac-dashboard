#!/usr/bin/env python3
"""
Step 3 (US) — Compute CAC by product by day for THREE rolling windows: 28D, 60D, 90D.
Same as BR version + EXCLUDE_KEYWORDS filter for non-shoe products.
"""

import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
ORDERS = json.loads((ROOT / "orders_raw_us.json").read_text(encoding="utf-8"))
SPEND_DAILY = json.loads((ROOT / "meta_spend_daily_us.json").read_text(encoding="utf-8"))

OUT_PATH = ROOT / "cac_by_product_us.json"

PERIODS = [28, 60, 90]

# Produtos a ignorar (não são calçados — upsells, seguros, gift cards, etc)
EXCLUDE_KEYWORDS = [
    "returns coverage", "shipping", "warranty", "protection",
    "gift card", "store credit", "tip", "donation",
    "route", "corso",
]


def is_excluded(title):
    t = (title or "").lower()
    return any(k in t for k in EXCLUDE_KEYWORDS)


def min_new_customers_for(period):
    return max(20, round(20 * period / 28))


def parse_day(iso_dt):
    return datetime.fromisoformat(iso_dt.replace("Z", "+00:00")).date().isoformat()


all_units_d = defaultdict(lambda: defaultdict(int))
all_revenue_d = defaultdict(lambda: defaultdict(float))
all_total_revenue_d = defaultdict(float)
all_new_cust_d = defaultdict(lambda: defaultdict(int))
all_titles = {}

for o in ORDERS:
    if o.get("cancelledAt"):
        continue
    cust = o.get("customer") or {}
    try:
        n_orders = int(cust.get("numberOfOrders") or 0)
    except (TypeError, ValueError):
        n_orders = 0
    is_new = n_orders == 1
    day = parse_day(o["createdAt"])

    products_in_order = set()
    for li in o.get("lineItems", {}).get("nodes", []):
        prod = li.get("product")
        if not prod:
            continue
        pid = prod["id"]
        title = prod.get("title") or pid
        if is_excluded(title):
            continue
        all_titles[pid] = title
        qty = int(li.get("quantity") or 0)
        rev = float(li.get("discountedTotalSet", {}).get("shopMoney", {}).get("amount") or 0)

        all_units_d[day][pid] += qty
        all_revenue_d[day][pid] += rev
        all_total_revenue_d[day] += rev
        products_in_order.add(pid)

    if is_new:
        for pid in products_in_order:
            all_new_cust_d[day][pid] += 1


def compute_for_window(period_days):
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=period_days - 1)

    dates = []
    cur = start
    while cur <= end:
        dates.append(cur.isoformat())
        cur += timedelta(days=1)

    units_by_product = defaultdict(int)
    revenue_by_product = defaultdict(float)
    new_cust_by_product = defaultdict(int)
    title_by_product = {}

    for d in dates:
        for pid, q in all_units_d[d].items():
            units_by_product[pid] += q
            title_by_product[pid] = all_titles[pid]
        for pid, r in all_revenue_d[d].items():
            revenue_by_product[pid] += r
        for pid, n in all_new_cust_d[d].items():
            new_cust_by_product[pid] += n

    allocated_d = defaultdict(lambda: defaultdict(float))
    for d in dates:
        spend = float(SPEND_DAILY.get(d, 0))
        total_rev = all_total_revenue_d[d]
        if total_rev <= 0 or spend <= 0:
            continue
        for pid, r in all_revenue_d[d].items():
            allocated_d[d][pid] = round(spend * (r / total_rev), 2)

    spend_by_product = defaultdict(float)
    for d in dates:
        for pid, sp in allocated_d[d].items():
            spend_by_product[pid] += sp

    def cac_window(pid):
        nc = new_cust_by_product[pid]
        return round(spend_by_product[pid] / nc, 2) if nc > 0 else None

    all_pids = list(units_by_product.keys())
    top15_units = sorted(all_pids, key=lambda p: -units_by_product[p])[:15]

    min_nc = min_new_customers_for(period_days)
    eligible = [p for p in all_pids if new_cust_by_product[p] >= min_nc and cac_window(p) is not None]
    top15_low = sorted(eligible, key=lambda p: cac_window(p))[:15]

    union_pids = list(dict.fromkeys(top15_units + top15_low))

    def build_row(pid):
        row = {
            "product_id": pid,
            "title": title_by_product[pid],
            "units": units_by_product[pid],
            "revenue": round(revenue_by_product[pid], 2),
            "new_customers": new_cust_by_product[pid],
            "allocated_spend": round(spend_by_product[pid], 2),
            "cac": cac_window(pid),
            "daily": [],
        }
        for d in dates:
            nc = all_new_cust_d[d].get(pid, 0)
            sp = allocated_d[d].get(pid, 0)
            cac_d = round(sp / nc, 2) if nc > 0 else None
            row["daily"].append({
                "date": d,
                "units": all_units_d[d].get(pid, 0),
                "revenue": round(all_revenue_d[d].get(pid, 0), 2),
                "new_customers": nc,
                "spend": round(sp, 2),
                "cac": cac_d,
            })
        return row

    products = [build_row(pid) for pid in union_pids]

    total_spend = sum(SPEND_DAILY.get(d, 0) for d in dates)
    total_top15u_revenue = sum(revenue_by_product[p] for p in top15_units)
    total_top15u_new_cust = sum(new_cust_by_product[p] for p in top15_units)
    total_top15u_spend = sum(spend_by_product[p] for p in top15_units)
    total_revenue = sum(revenue_by_product.values())
    share_revenue = total_top15u_revenue / total_revenue if total_revenue else 0

    total_low_new = sum(new_cust_by_product[p] for p in top15_low)
    total_low_spend = sum(spend_by_product[p] for p in top15_low)
    total_low_revenue = sum(revenue_by_product[p] for p in top15_low)

    summary = {
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "days": period_days,
        "total_orders_in_window": sum(1 for o in ORDERS if not o.get("cancelledAt") and start.isoformat() <= parse_day(o["createdAt"]) <= end.isoformat()),
        "total_marketing_spend": round(total_spend, 2),
        "min_new_customers_lowcac_filter": min_nc,
        "top15_units_ids": top15_units,
        "top15_units_revenue": round(total_top15u_revenue, 2),
        "top15_units_revenue_share_of_total": round(share_revenue, 4),
        "top15_units_allocated_spend": round(total_top15u_spend, 2),
        "top15_units_new_customers": total_top15u_new_cust,
        "top15_units_blended_cac": round(total_top15u_spend / total_top15u_new_cust, 2) if total_top15u_new_cust else None,
        "top15_lowcac_ids": top15_low,
        "top15_lowcac_revenue": round(total_low_revenue, 2),
        "top15_lowcac_allocated_spend": round(total_low_spend, 2),
        "top15_lowcac_new_customers": total_low_new,
        "top15_lowcac_blended_cac": round(total_low_spend / total_low_new, 2) if total_low_new else None,
    }

    print(f"\n[US · {period_days}D] {start} → {end}  spend=${total_spend:>10,.0f}  CAC_vol={summary['top15_units_blended_cac']}  CAC_low={summary['top15_lowcac_blended_cac']}")
    return {
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "dates": dates,
        "products": products,
        "summary": summary,
    }


result = {
    "country": "us",
    "currency": "USD",
    "shop": "Larroude US",
    "generated_at": date.today().isoformat(),
    "usd_to_brl_rate": None,
    "periods": {str(p): compute_for_window(p) for p in PERIODS},
}

OUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nOK Saved -> {OUT_PATH}")
