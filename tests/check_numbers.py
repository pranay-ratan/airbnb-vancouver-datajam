"""Checks that the deck, the dashboard and the outputs agree with outputs/metrics.json, and that nothing private leaks.
Run after run_all.sh:  python3 -I tests/check_numbers.py
"""
import json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
M = json.loads((ROOT / "outputs/metrics.json").read_text())
R = M["recommendation"]; fails = []
def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg)
    if not ok: fails.append(msg)

K = lambda x: f"${x/1000:,.0f}K"
deck = "".join(p.read_text(encoding="utf-8") for p in sorted((ROOT / "deliverables/deck/project/slides").glob("*.html")))
dash = (ROOT / "outputs/dashboard/index.html").read_text(encoding="utf-8")
for label, val in [("median 2027 income", K(R["noi_p50"])), ("P10", K(R["noi_p10"])), ("P90", K(R["noi_p90"])), ("units", f'Buy {R["units"]} one-bedroom')]:
    check(val in deck, f"deck shows {label}: {val}")
check(M["credit"] in deck, "every deck page carries the Inside Airbnb credit line")
check(deck.count(M["credit"]) >= len(list((ROOT / "deliverables/deck/project/slides").glob("*.html"))), "credit line on all slides")
check('"p50"' in dash or "noi_p50" in dash, "dashboard embeds the recommendation numbers")
check(abs(R["noi_p50"] - 269952.73) < 1000, f"headline NOI near the published figure ({R['noi_p50']:.0f})")
check(R["units"] == 14 and R["deployed"] <= 10_000_000, "units and budget respected")
check(R["noi_p10"] < R["noi_p50"] < R["noi_p90"], "range brackets the median")
check(M["validation"]["v1_revenue_corr"] > 0.99 and M["validation"]["v2_occupancy_formula_match"] > 0.99, "Inside Airbnb revenue and occupancy formulas reproduced")
for name in ["listing_url", "host_name", "host_url", "picture_url", '"license"']:
    check(name not in dash and name not in (ROOT / "outputs/dashboard_data.json").read_text(), f"no '{name}' field in dashboard or its data")
check(not re.search(r"\b\d{2}-\d{5,6}\b", deck), "no licence numbers on slides")
sys.exit(1 if fails else 0)
