"""Step 6. Checks that try to break the result.

  V1  our revenue arithmetic reproduces Inside Airbnb's own revenue estimate
  V2  the 'estimated occupancy' field is exactly reviews x 2 x max(3, minimum nights), capped at 255
  V3  forward calendar: is the estimate plausible next to the nights already booked or blocked? (plausibility only)
  V4  split-sample: segments picked on a random half of listings still lead on the other half
  V5  out of sample in time: the same pipeline on the 17 September 2026 snapshot
  V6  first-year listings: is a 10% first-year haircut too kind?
  V7  how full is a nightly unit outside the peak season?

Writes  outputs/tables/validation.json, outputs/tables/listing_age.csv, outputs/tables/snapshot_retest.csv
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # so the script also runs with python -I
from common import *
from config import SNAPSHOT, SNAP_SEP, PROC, SEED
from assumptions import A, add_costs, nightly

rng = np.random.default_rng(SEED)
prof, S, pb = load_json("data_profile.json"), load_json("seasonality.json"), load_json("price_basis.json")
c = pd.read_csv(PROC / "comps_econ.csv")
V = {"v1_revenue_corr": prof["revenue_is_price_x_occ_corr"], "v2_occupancy_formula_match": prof["occ_formula_match_share"],
     "v2_share_at_cap": prof["occ_at_cap_share"]}

# ---- V3 forward calendar (unavailable = booked OR blocked; the file cannot tell which, and later
#      bookings are not in it yet, so this is a plausibility check and not a ceiling or a floor) ---------
cal = pd.read_csv(RAW / SNAPSHOT / "calendar.csv.gz", usecols=["listing_id", "date", "available"])
cal["date"] = pd.to_datetime(cal.date, format="%Y-%m-%d")
cal = cal[cal.listing_id.isin(set(c.id)) & (cal.date >= "2026-06-15") & (cal.date <= "2026-08-31")]
unavail = cal.assign(u=cal.available.eq("f")).groupby("listing_id").u.mean().rename("summer_unavailable")
m = c.set_index("id").join(unavail, how="inner")
summer_share = S["month_share"]["6"] / 2 + S["month_share"]["7"] + S["month_share"]["8"]       # 15 June - 31 August
m["summer_estimate"] = m.nights * summer_share / 78
V["v3_listings"] = int(len(m))
V["v3_median_estimated_summer_occupancy"] = float(m.summer_estimate.median())
V["v3_median_summer_unavailable"] = float(m.summer_unavailable.median())

# ---- V4 split-sample ranking stability ----------------------------------------------------------------
key = ["neighbourhood_cleansed", "asset"]
corr, edge = [], []
for _ in range(300):
    half = rng.random(len(c)) < 0.5
    a = c[half].groupby(key).agg(noi=("noi", "sum"), cost=("allin", "sum"), n=("id", "count"))
    b = c[~half].groupby(key).agg(noi=("noi", "sum"), cost=("allin", "sum"), n=("id", "count"))
    j = a.join(b, lsuffix="_a", rsuffix="_b", how="inner")
    j = j[(j.n_a >= 8) & (j.n_b >= 8)]
    ya, yb = j.noi_a / j.cost_a, j.noi_b / j.cost_b
    corr.append(ya.rank().corr(yb.rank()))
    edge.append(yb[ya.nlargest(3).index].mean() - yb.mean())
V["v4_rank_correlation"] = float(np.mean(corr))
V["v4_top3_beat_average_share"] = float((np.array(edge) > 0).mean())
V["v4_top3_edge_points"] = float(np.mean(edge))

# ---- V5 same pipeline on the September snapshot --------------------------------------------------------
if has_snapshot(SNAP_SEP):
    s = load_listings(SNAP_SEP)
    s = nightly_priced(s)
    s = s[s.asset.isin(["condo", "townhouse", "house"]) & s.licensed & (s.age_m >= 12) & (s.number_of_reviews_ltm >= 1)].copy()
    s["adr"] = s.price_n * S["annual_price_level_vs_sept"]          # September quotes need no World Cup deflator
    s["nights"] = s.occ
    s = add_costs(s)
    n = nightly(s)
    s["noi"], s["guest_rev"] = n.noi, n.guest_rev

    def py(g):
        return g.noi.sum() / g.allin.sum()

    core1_j = c[c.core & (c.asset == "condo") & (c.bedrooms == 1)]
    core1_s = s[s.core & (s.asset == "condo") & (s.bedrooms == 1)]
    rows = [{"segment": "Core one-bedroom apartments", "june_listings": len(core1_j), "june_yield": py(core1_j),
             "sept_listings": len(core1_s), "sept_yield": py(core1_s), "june_nights": core1_j.nights.median(), "sept_nights": core1_s.nights.median(),
             "june_price": core1_j.adr.median(), "sept_price": core1_s.adr.median()}]
    for asset in ("condo", "townhouse", "house"):
        gj, gs = c[c.asset == asset], s[s.asset == asset]
        rows.append({"segment": f"All {asset}s", "june_listings": len(gj), "june_yield": py(gj), "sept_listings": len(gs), "sept_yield": py(gs),
                     "june_nights": gj.nights.median(), "sept_nights": gs.nights.median(), "june_price": gj.adr.median(), "sept_price": gs.adr.median()})
    pd.DataFrame(rows).to_csv(TAB / "snapshot_retest.csv", index=False)
    sj = c.groupby(key).apply(lambda g: pd.Series({"y": py(g), "n": len(g)}))
    ss = s.groupby(key).apply(lambda g: pd.Series({"y": py(g), "n": len(g)}))
    j = sj.join(ss, lsuffix="_j", rsuffix="_s", how="inner")
    j = j[(j.n_j >= 15) & (j.n_s >= 15)]
    V["v5_segments_compared"] = int(len(j))
    V["v5_rank_correlation_june_vs_sept"] = float(j.y_j.rank().corr(j.y_s.rank()))
    V["v5_core1_yield_june"], V["v5_core1_yield_sept"] = float(py(core1_j)), float(py(core1_s))
    V["v5_house_yield_june"], V["v5_house_yield_sept"] = float(py(c[c.asset == "house"])), float(py(s[s.asset == "house"]))
    V["v5_condo_yield_june"], V["v5_condo_yield_sept"] = float(py(c[c.asset == "condo"])), float(py(s[s.asset == "condo"]))
    V["v5_core1_price_june_basis"], V["v5_core1_price_sept"] = float(core1_j.adr.median()), float(core1_s.adr.median())

# ---- V6 listing age: nights in the last 12 months by months since first review -------------------------
allc = pd.read_csv(PROC / "comps.csv")
k = allc[allc.licensed & allc.core & (allc.asset == "condo") & (allc.number_of_reviews_ltm >= 1)]
age = pd.cut(k.age_m, [0, 3, 6, 9, 12, 24, 600], labels=["0-3", "3-6", "6-9", "9-12", "12-24", "24+"])
tab = k.groupby(age, observed=True).agg(listings=("id", "count"), median_nights=("occ", "median"), mean_nights=("occ", "mean"))
tab.to_csv(TAB / "listing_age.csv")
V["v6_nights_9_12_months"] = float(tab.loc["9-12", "median_nights"])
V["v6_nights_12_plus_months"] = float(k[k.age_m >= 12].occ.median())
V["v6_nights_all_ages"] = float(k.occ.median())
V["v6_share_under_12_months"] = float((k.age_m < 12).mean())

# ---- V7 how full is a nightly unit outside the four peak months? ----------------------------------------
core1 = c[c.core & (c.asset == "condo") & (c.bedrooms == 1)]
off_days = 365 - sum({5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 4: 30, 10: 31}[mth] for mth in S["peak_months"])
V["v7_off_season_days"] = off_days
V["v7_off_season_nightly_occupancy"] = float(core1.nights.median() * 0.9 * (1 - S["peak_share"]) / off_days)
V["v7_peak_nightly_occupancy"] = float(core1.nights.median() * 0.9 * S["peak_share"] / (365 - off_days))
V["v7_off_season_nightly_rate"] = float(core1.adr.median() * (1 - S["peak_share"] * S["peak_adr_uplift"]) / (1 - S["peak_share"]))
V["v7_furnished_rent_per_day"] = A["mid_rent"][1] * 12 / 365

save_json(V, "validation.json")
print(json.dumps(V, indent=1)); print(tab.to_string())
if has_snapshot(SNAP_SEP):
    print(pd.read_csv(TAB / "snapshot_retest.csv").round(4).to_string())
