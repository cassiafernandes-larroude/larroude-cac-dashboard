#!/usr/bin/env python3
"""
Orquestrador diário do dashboard CAC por produto (BR + US).
Executa em ordem os pipelines BR e US e regenera os 2 dashboards.

Uso:
  python run_daily.py            # BR e US
  python run_daily.py br         # só BR
  python run_daily.py us         # só US

Sai com exit code != 0 se qualquer passo falhar.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent

PIPELINES = {
    "br": [
        ("1_fetch_shopify.py",     "[BR] Pull Shopify (28D)",       []),
        ("2_fetch_meta_spend.py",  "[BR] Pull Meta daily spend",    []),
        ("3_compute_cac.py",       "[BR] Compute CAC matrix",       []),
        ("4_build_dashboard.py",   "[BR] Build HTML dashboard",     ["--country", "br"]),
    ],
    "us": [
        ("1_fetch_shopify_us.py",     "[US] Pull Shopify (28D)",    []),
        ("2_fetch_meta_spend_us.py",  "[US] Pull Meta daily spend", []),
        ("3_compute_cac_us.py",       "[US] Compute CAC matrix",    []),
        ("4_build_dashboard.py",      "[US] Build HTML dashboard",  ["--country", "us"]),
    ],
}


def run_pipeline(country):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    for script, label, extra in PIPELINES[country]:
        print(f"--> {label}  ({script} {' '.join(extra)})")
        r = subprocess.run([sys.executable, str(ROOT / script), *extra], cwd=str(ROOT), env=env)
        if r.returncode != 0:
            print(f"FAIL step '{script}' (exit {r.returncode})", file=sys.stderr)
            sys.exit(r.returncode)
        print()


def main():
    args = sys.argv[1:]
    targets = args if args else ["br", "us"]
    for c in targets:
        if c not in PIPELINES:
            print(f"FAIL unknown country: {c} (use br or us)", file=sys.stderr)
            sys.exit(2)

    print(f"=== Daily CAC refresh — {datetime.now().isoformat(timespec='seconds')} ===")
    print(f"   targets: {', '.join(targets)}\n")

    for c in targets:
        run_pipeline(c)
        out = ROOT / f"dashboard_cac_{c}.html"
        if out.exists():
            mtime = datetime.fromtimestamp(out.stat().st_mtime).isoformat(timespec="seconds")
            print(f"OK [{c.upper()}] {out.name} regenerado em {mtime}\n")

    print(f"OK Pipeline completo: {', '.join(targets)}")


if __name__ == "__main__":
    main()
