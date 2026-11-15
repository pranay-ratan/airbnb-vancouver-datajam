"""Step 9. One file of headline numbers, and the map/dashboard data.

Writes  outputs/metrics.json            every number quoted in the deck and the dashboard, with the table it came from
        outputs/map/neighbourhoods.json  simplified neighbourhood outlines (projected) with summary statistics
        outputs/dashboard_data.json      anonymised listing-level data for the interactive dashboard
                                         (no ids, names, URLs or licence numbers; positions snapped to a ~30 m grid)
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # so the script also runs with python -I
import math
from common import *
from config import SNAPSHOT, PROC, OUT, BENCH, BENCH_SOURCE, BUDGET, CORE, ZONE
from assumptions import A

prof, pb, S = load_json("data_profile.json"), load_json("price_basis.json"), load_json("seasonality.json")
V, D, T = load_json("validation.json"), load_json("decisions.json"), load_json("tests_not_held.json")
t = lambda n: pd.read_csv(TAB / n)
funnel, asset, seg = t("cleaning_funnel.csv"), t("asset_yields.csv"), t("segment_yields.csv")
bybed, modes_u, house = t("core_by_bedrooms.csv"), t("operating_modes.csv"), t("house_tests.csv")
strat, pmodes, sens = t("strategies.csv"), t("portfolio_modes.csv"), t("sensitivity.csv")
age, retest, ratios, monthly = t("listing_age.csv"), t("snapshot_retest.csv"), t("price_ratios.csv"), t("monthly_stays.csv")
c = pd.read_csv(PROC / "comps_econ.csv")
core1 = c[c.core & (c.asset == "condo") & (c.bedrooms == 1)]

rec = pmodes[pmodes.label == "Hybrid (recommended)"].iloc[0]
units = int(rec.units)
mix = (core1.neighbourhood_cleansed.value_counts(normalize=True) * units)
alloc = mix.round().astype(int)
alloc.iloc[0] += units - alloc.sum()                      # rounding remainder goes to the largest neighbourhood
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
pk = S["peak_months"]

M = {
    "credit": "Data: Inside Airbnb, Vancouver, 15 June 2026, CC BY 4.0.",
    "snapshot": SNAPSHOT, "budget": BUDGET,
    "recommendation": {
        "units": units, "deployed": float(rec.deployed), "reserve": float(BUDGET - rec.deployed),
        "noi_p10": float(rec.noi_p10), "noi_p50": float(rec.noi_p50), "noi_p90": float(rec.noi_p90),
        "yield_p10": float(rec.yield_p10), "yield_p50": float(rec.yield_p50), "yield_p90": float(rec.yield_p90),
        "prob_yield_below_1pct": float(rec.prob_yield_below_1pct), "units_missing_tenancy_test": float(rec.units_missing_tenancy_test),
        "allocation": alloc.to_dict(), "pool_listings": int(len(core1)),
        "nightly_months": f"{MONTHS[pk[0] - 1]}-{MONTHS[pk[-1] - 1]}", "furnished_months": f"{MONTHS[pk[-1] % 12]}-{MONTHS[pk[0] - 2]}",
        "unit_allin_cost": float(core1.allin.median()), "unit_purchase": float(core1.purchase.median()),
        "unit_price": float(core1.adr.median()), "unit_nights": float(core1.nights.median())},
    "profile": prof, "price_basis": pb, "seasonality": S, "validation": V, "decisions": D, "tested": T,
    "funnel": funnel.to_dict("records"),
    "assets": asset.set_index("asset").to_dict("index"),
    "segments": seg.to_dict("records"),
    "core_by_bedrooms": bybed.to_dict("records"),
    "modes_unit": modes_u.to_dict("records"),
    "house_tests": house.to_dict("records"),
    "strategies": strat.to_dict("records"),
    "portfolio_modes": pmodes.to_dict("records"),
    "sensitivity": sens.to_dict("records"),
    "listing_age": age.to_dict("records"), "snapshot_retest": retest.to_dict("records"),
    "price_ratios": ratios.to_dict("records"), "monthly_stays": monthly.to_dict("records"),
    "assumptions": {k: v for k, v in A.items()},
    "benchmarks": {f"{z}_{a}": v for (z, a), v in BENCH.items()}, "benchmark_source": BENCH_SOURCE,
}
(OUT / "metrics.json").write_text(json.dumps(json.loads(json.dumps(M, default=float)), indent=1))

# ---------------------------------------------------------------------------------------------------
# Map: project to a flat plane (equirectangular at Vancouver's latitude), simplify outlines
# ---------------------------------------------------------------------------------------------------
gj = json.loads((RAW / "neighbourhoods.geojson").read_text())
lat0 = 49.25
W = 1000.0


def rdp(pts, eps):
    """Douglas-Peucker line simplification (pure Python; shapely is not required)."""
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    norm = math.hypot(dx, dy) or 1e-12
    dmax, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / norm
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]


rings = []
for f in gj["features"]:
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for poly in polys:
        rings.append((f["properties"]["neighbourhood"], poly[0]))
lons = [p[0] for _, r in rings for p in r]
lats = [p[1] for _, r in rings for p in r]
kx = math.cos(math.radians(lat0))
scale = W / ((max(lons) - min(lons)) * kx)
H = (max(lats) - min(lats)) * scale


def proj(lon, lat):
    return (lon - min(lons)) * kx * scale, (max(lats) - lat) * scale


def path(ring, eps):
    pts = [proj(*p) for p in ring]
    far = max(range(len(pts)), key=lambda i: math.hypot(pts[i][0] - pts[0][0], pts[i][1] - pts[0][1]))
    pts = rdp(pts[:far + 1], eps)[:-1] + rdp(pts[far:], eps)       # a closed ring is simplified as two open halves
    return "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"


raw = load_listings(SNAPSHOT)
ent = raw[raw.entire & ~raw.hotel_like]
names = sorted({n for n, _ in rings})
hoods = []
for n in names:
    rs = [r for nm, r in rings if nm == n]
    big = max(rs, key=len)
    px = [proj(*p) for p in big]
    cross = [px[i][0] * px[i + 1][1] - px[i + 1][0] * px[i][1] for i in range(len(px) - 1)]
    area = sum(cross) / 2 or 1e-9
    cx = sum((px[i][0] + px[i + 1][0]) * cross[i] for i in range(len(px) - 1)) / (6 * area)       # area-weighted centroid
    cy = sum((px[i][1] + px[i + 1][1]) * cross[i] for i in range(len(px) - 1)) / (6 * area)
    e = ent[ent.neighbourhood_cleansed == n]
    cc = c[c.neighbourhood_cleansed == n]
    con, hou = cc[cc.asset == "condo"], cc[cc.asset == "house"]
    hoods.append({
        "name": n, "core": n in CORE, "zone": ZONE[n],
        "path": " ".join(path(r, 1.2) for r in rs), "path_small": " ".join(path(r, 3.0) for r in rs),
        "cx": round(cx, 1), "cy": round(cy, 1), "area": round(abs(area)),
        "listings": int((raw.neighbourhood_cleansed == n).sum()),
        "nightly": int((e.stay == "nightly").sum()), "long90": int((e.stay == "90+ nights").sum()),
        "comps": int(len(cc)), "condo_comps": int(len(con)), "house_comps": int(len(hou)),
        "condo_yield": float(con.noi.sum() / con.allin.sum()) if len(con) >= 15 else None,
        "house_yield": float(hou.noi.sum() / hou.allin.sum()) if len(hou) >= 15 else None,
        "median_nights": float(cc.nights.median()) if len(cc) >= 15 else None,
        "median_price": float(cc.adr.median()) if len(cc) >= 15 else None})
(OUT / "map" / "neighbourhoods.json").write_text(json.dumps({"width": W, "height": round(H, 1), "hoods": hoods}))

# ---------------------------------------------------------------------------------------------------
# Dashboard data: listing-level, anonymised
# ---------------------------------------------------------------------------------------------------
hid = {n: i for i, n in enumerate(names)}
aid = {"condo": 0, "townhouse": 1, "house": 2}
pr = pd.read_csv(PROC / "comps.csv")


def snap(lon, lat):
    x, y = proj(lon, lat)
    return round(x / 2) * 2, round(y / 2) * 2              # 2 map units is roughly 30 m


L = []
for r in pr.itertuples():
    x, y = snap(r.longitude, r.latitude)
    L.append([x, y, hid[r.neighbourhood_cleansed], aid[r.asset], int(r.bedrooms) if r.bedrooms == r.bedrooms else -1,     # -1 = bedrooms missing
              int(round(r.price_n)), int(r.occ), int(bool(r.licensed)), int(bool(r.established)), int(r.number_of_reviews_ltm >= 1)])
long90 = ent[ent.stay == "90+ nights"]
L90 = []
for r in long90.itertuples():
    x, y = snap(r.longitude, r.latitude)
    month = int(round(r.price_n * 90)) if (r.price_n == r.price_n and r.q_nights >= 90) else 0
    L90.append([x, y, hid[r.neighbourhood_cleansed], 1 if r.asset == "condo" else 0, month])

DD = {"width": W, "height": round(H, 1), "hoods": [{k: v for k, v in h.items() if k != "path_small"} for h in hoods],
      "listings": L, "listing_fields": ["x", "y", "hood", "asset", "bedrooms", "june_price", "nights", "licensed", "established", "reviewed_last_year"],
      "long90": L90, "long90_fields": ["x", "y", "hood", "is_apartment", "month_asking"],
      "assets": ["condo", "townhouse", "house"], "metrics": json.loads((OUT / "metrics.json").read_text())}
(OUT / "dashboard_data.json").write_text(json.dumps(DD, separators=(",", ":")))

print("metrics.json", (OUT / "metrics.json").stat().st_size, "bytes | dashboard_data.json", (OUT / "dashboard_data.json").stat().st_size,
      "| neighbourhoods.json", (OUT / "map" / "neighbourhoods.json").stat().st_size)
print("map", W, "x", round(H, 1), "| hoods", len(hoods), "| listings", len(L), "| 90-night", len(L90))
print("recommendation:", json.dumps(M["recommendation"], indent=1))
print("path sizes:", sum(len(h["path"]) for h in hoods), sum(len(h["path_small"]) for h in hoods))
