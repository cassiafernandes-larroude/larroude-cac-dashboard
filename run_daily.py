#!/usr/bin/env python3
"""
Orquestrador diário do dashboard CAC por produto (Larroude BR).
Executa em ordem os 4 passos do pipeline e regenera o dashboard.

Uso: python run_daily.py
Sai com exit code != 0 se qualquer passo falhar.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
STEPS = [
    ("1_fetch_shopify.py",      "Pull Shopify BR (28D)"),
    ("2_fetch_meta_spend.py",   "Pull Meta BR daily spend"),
    ("3_compute_cac.py",        "Compute CAC matrix"),
    ("4_build_dashboard.py",    "Build HTML dashboard"),
]

env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"

print(f"=== Daily CAC refresh — {datetime.now().isoformat(timespec='seconds')} ===\n")

for script, label in STEPS:
    print(f"--> {label}  ({script})")
    r = subprocess.run([sys.executable, str(ROOT / script)], cwd=str(ROOT), env=env)
    if r.returncode != 0:
        print(f"FAIL step '{script}' (exit {r.returncode})", file=sys.stderr)
        sys.exit(r.returncode)
    print()

dash = ROOT / "dashboard_cac_br.html"
mtime = datetime.fromtimestamp(dash.stat().st_mtime).isoformat(timespec="seconds")
print(f"OK Pipeline completo. Dashboard regenerado em {mtime}")
print(f"   {dash}")
