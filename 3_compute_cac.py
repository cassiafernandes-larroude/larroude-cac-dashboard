#!/usr/bin/env python3
"""
Step 3 — Compute CAC by product by day (Larroude BR, last 28D).

Methodology:
- Two product rankings:
  (A) Top 15 by units sold in the 28D window (excluding cancelled orders).
  (B) Top 15 with lowest 28D CAC, restricted to products with >= MIN_NEW_CUSTOMERS
      to avoid statistical noise from low-volume products.
- New customer = order where customer.numberOfOrders == 1 (first order ever).
- A product gets +1 new customer if it appears in a new-customer order.
- Daily spend is allocated proportionally to each product's share of TOTAL daily
  revenue (across ALL products). CAC[p,d] = allocated_spend[p,d] / new_customers[p,d].
"""

import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
ORDERS = json.loads((ROOT / "orders_raw.json").read_text(encoding="utf-8"))
SPEND_DAILY = json.loads((ROOT / "meta_spend_daily.json").read_text(encoding="utf-8"))

OUT_PATH = ROOT / "cac_by_product.json"

# Threshold to be eligible for "lowest CAC" ranking — avoids noise.
MIN_NEW_CUSTOMERS = 20


def parse_day(iso_dt):
    return datetime.fromisoformat(iso_dt.replace("Z", "+00:00")).date().isoformat()


# ─── Pass 1: 28D totals for ALL products ──────────────────────────────────────
units_by_product = defaultdict(int)
revenue_by_product = defaultdict(float)
title_by_product = {}
new_cust_by_product = defaultdict(int)

# Daily aggregates for ALL products (we'll filter later when emitting matrix)
new_customers_d = defaultdict(lambda: defaultdict(int))   # [day][pid]
revenue_d = defaultdict(lambda: defaultdict(float))       # [day][pid]
units_d = defaultdict(lambda: defaultdict(int))           # [day][pid]
total_revenue_d = defaultdict(float)                      # [day]

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
        title_by_product[pid] = prod.get("title") or pid
        qty = int(li.get("quantity") or 0)
        rev = float(li.get("discountedTotalSet", {}).get("shopMoney", {}).get("amount") or 0)

        units_by_product[pid] += qty
        revenue_by_product[pid] += rev
        units_d[day][pid] += qty
        revenue_d[day][pid] += rev
        total_revenue_d[day] += rev
        products_in_order.add(pid)

    if is_new:
        for pid in products_in_order:
            new_cust_by_product[pid] += 1
            new_customers_d[day][pid] += 1


# ─── Pass 2: allocate daily spend across ALL products by daily revenue share ──
END = date.today() - timedelta(days=1)
START = END - timedelta(days=27)

dates = []
cur = START
while cur <= END:
    dates.append(cur.isoformat())
    cur += timedelta(days=1)

allocated_spend_d = defaultdict(lambda: defaultdict(float))
for d in dates:
    spend = float(SPEND_DAILY.get(d, 0))
    total_rev = total_revenue_d[d]
    if total_rev <= 0 or spend <= 0:
        continue
    for pid, r in revenue_d[d].items():
        allocated_spend_d[d][pid] = round(spend * (r / total_rev), 2)


# ─── Pass 3: compute 28D CAC per product ──────────────────────────────────────
spend_28d_by_product = defaultdict(float)
for d in dates:
    for pid, sp in allocated_spend_d[d].items():
        spend_28d_by_product[pid] += sp

def cac_28d(pid):
    nc = new_cust_by_product[pid]
    if nc <= 0:
        return None
    return round(spend_28d_by_product[pid] / nc, 2)


# ─── Rankings ─────────────────────────────────────────────────────────────────
all_pids = list(units_by_product.keys())

# (A) Top 15 by units
top15_units = sorted(all_pids, key=lambda p: -units_by_product[p])[:15]

# (B) Top 15 by lowest CAC (with MIN_NEW_CUSTOMERS filter)
eligible_low_cac = [p for p in all_pids if new_cust_by_product[p] >= MIN_NEW_CUSTOMERS and cac_28d(p) is not None]
top15_low_cac = sorted(eligible_low_cac, key=lambda p: cac_28d(p))[:15]

# Union (so dashboard JSON has daily data for both)
union_pids = list(dict.fromkeys(top15_units + top15_low_cac))


def build_row(pid):
    row = {
        "product_id": pid,
        "title": title_by_product[pid],
        "units_28d": units_by_product[pid],
        "revenue_28d": round(revenue_by_product[pid], 2),
        "new_customers_28d": new_cust_by_product[pid],
        "allocated_spend_28d": round(spend_28d_by_product[pid], 2),
        "cac_28d": cac_28d(pid),
        "daily": [],
    }
    for d in dates:
        nc = new_customers_d[d][pid]
        sp = allocated_spend_d[d][pid]
        cac = round(sp / nc, 2) if nc > 0 else None
        row["daily"].append({
            "date": d,
            "units": units_d[d][pid],
            "revenue": round(revenue_d[d][pid], 2),
            "new_customers": nc,
            "spend": round(sp, 2),
            "cac": cac,
        })
    return row


products = [build_row(pid) for pid in union_pids]


# ─── Print rankings ───────────────────────────────────────────────────────────
print("Top 15 produtos por UNIDADES vendidas (28D):")
for i, pid in enumerate(top15_units, 1):
    print(f"  {i:2d}. {title_by_product[pid][:55]:55s}  units={units_by_product[pid]:5d}  CAC=R${cac_28d(pid) if cac_28d(pid) else 0:>7,.0f}")

print(f"\nTop 15 produtos com MENOR CAC (28D, min {MIN_NEW_CUSTOMERS} novos clientes):")
for i, pid in enumerate(top15_low_cac, 1):
    print(f"  {i:2d}. {title_by_product[pid][:55]:55s}  CAC=R${cac_28d(pid):>7,.0f}  newCust={new_cust_by_product[pid]:4d}")


# ─── Summary ──────────────────────────────────────────────────────────────────
total_spend = sum(SPEND_DAILY.get(d, 0) for d in dates)
total_top15u_revenue = sum(revenue_by_product[p] for p in top15_units)
total_top15u_new_customers = sum(new_cust_by_product[p] for p in top15_units)
total_top15u_spend = sum(spend_28d_by_product[p] for p in top15_units)

share_revenue = total_top15u_revenue / sum(revenue_by_product.values()) if revenue_by_product else 0

# Low-CAC group stats
total_lowcac_new = sum(new_cust_by_product[p] for p in top15_low_cac)
total_lowcac_spend = sum(spend_28d_by_product[p] for p in top15_low_cac)
total_lowcac_revenue = sum(revenue_by_product[p] for p in top15_low_cac)

summary = {
    "currency": "BRL",
    "shop": "Larroude BR",
    "window_start": START.isoformat(),
    "window_end": END.isoformat(),
    "total_orders": len(ORDERS),
    "total_marketing_spend_28d": round(total_spend, 2),
    "min_new_customers_lowcac_filter": MIN_NEW_CUSTOMERS,

    "top15_units_ids": top15_units,
    "top15_units_revenue_28d": round(total_top15u_revenue, 2),
    "top15_units_revenue_share_of_total": round(share_revenue, 4),
    "top15_units_allocated_spend_28d": round(total_top15u_spend, 2),
    "top15_units_new_customers_28d": total_top15u_new_customers,
    "top15_units_blended_cac_28d": round(total_top15u_spend / total_top15u_new_customers, 2) if total_top15u_new_customers else None,

    "top15_lowcac_ids": top15_low_cac,
    "top15_lowcac_revenue_28d": round(total_lowcac_revenue, 2),
    "top15_lowcac_allocated_spend_28d": round(total_lowcac_spend, 2),
    "top15_lowcac_new_customers_28d": total_lowcac_new,
    "top15_lowcac_blended_cac_28d": round(total_lowcac_spend / total_lowcac_new, 2) if total_lowcac_new else None,

    "usd_to_brl_rate": 5.10,
}

result = {
    "summary": summary,
    "dates": dates,
    "products": products,
}

OUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

print("\n--- Summary ---")
for k, v in summary.items():
    if isinstance(v, list):
        print(f"  {k}: [{len(v)} ids]")
    else:
        print(f"  {k}: {v}")
print(f"\nOK Saved -> {OUT_PATH}")
