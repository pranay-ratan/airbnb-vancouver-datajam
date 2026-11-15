"""Paths, snapshot choice and public price inputs.

Everything a judge might want to change lives here or in assumptions.py.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/insideairbnb"      # one sub-folder per Inside Airbnb snapshot date
PROC = ROOT / "data/processed"
OUT = ROOT / "outputs"
TAB = OUT / "tables"
for p in (PROC, TAB, OUT / "map"):
    p.mkdir(parents=True, exist_ok=True)

# The common DataJam dataset (brief, section 4). The other snapshots are public archive files from the
# same Inside Airbnb page. They are used only to measure seasonal prices and to re-test the result.
SNAPSHOT = "2026-06-15"
SNAP_DEC, SNAP_MAR, SNAP_SEP = "2025-12-14", "2026-03-21", "2026-09-17"

BUDGET = 10_000_000
SEED = 2026
NSIM = 5000

# Inside Airbnb's "Downtown Eastside" polygon includes Gastown and Chinatown.
CORE = ["Downtown", "West End", "Downtown Eastside"]

# Neighbourhood -> Greater Vancouver REALTORS price area. Downtown Eastside is priced at the West
# benchmark because its listings sit in Gastown/Chinatown buildings that trade like downtown (decision log).
WEST = ["Downtown", "West End", "Downtown Eastside", "Fairview", "Kitsilano", "Shaughnessy", "Arbutus Ridge",
        "Dunbar Southlands", "West Point Grey", "Kerrisdale", "South Cambie", "Oakridge", "Marpole"]
EAST = ["Mount Pleasant", "Strathcona", "Grandview-Woodland", "Hastings-Sunrise", "Kensington-Cedar Cottage",
        "Killarney", "Renfrew-Collingwood", "Riley Park", "Sunset", "Victoria-Fraserview"]
ZONE = {**{n: "W" for n in WEST}, **{n: "E" for n in EAST}}

# MLS HPI benchmark prices, Greater Vancouver REALTORS monthly statistics package, August 2026
# https://members.gvrealtors.ca/news/GVR-Stats-Package-August-2026.pdf  (public, free)
BENCH = {("W", "house"): 2_932_700, ("E", "house"): 1_621_400,
         ("W", "townhouse"): 1_334_900, ("E", "townhouse"): 985_400,
         ("W", "condo"): 774_900, ("E", "condo"): 628_600}
BENCH_SOURCE = "Greater Vancouver REALTORS, MLS HPI benchmark prices, August 2026"
