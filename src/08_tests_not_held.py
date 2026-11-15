"""Step 8. Ideas we tested that did not hold, so they stayed out of the plan.

  T1  "Run it like a Superhost and earn more."  Superhosts show more estimated nights, but the estimate is
      reviews x 6 nights, so it rewards whoever collects more reviews. The forward calendar shows no gap.
  T2  "Set a one-night minimum and earn more."  Same test, same answer: shorter stays leave more reviews.
  T3  Does the forward calendar agree with the estimate listing by listing?  (rank correlation)

The other rejected options are already in other tables and are only gathered here:
  five-month nightly season (portfolio_modes.csv), house + suite + laneway home (house_tests.csv),
  two-bedroom apartments (core_by_bedrooms.csv), Mount Pleasant (segment_yields.csv).

Writes  outputs/tables/tests_not_held.json
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # so the script also runs with python -I
from common import *
from config import SNAPSHOT, PROC

c = pd.read_csv(PROC / "comps_econ.csv")
cal = pd.read_csv(RAW / SNAPSHOT / "calendar.csv.gz", usecols=["listing_id", "date", "available"])
cal["date"] = pd.to_datetime(cal.date, format="%Y-%m-%d")
cal = cal[cal.listing_id.isin(set(c.id)) & (cal.date >= "2026-06-15") & (cal.date <= "2026-08-31")]
unavail = cal.assign(u=cal.available.eq("f")).groupby("listing_id").u.mean().rename("summer_unavailable")
m = c.set_index("id").join(unavail)
core1 = m[m.core & (m.asset == "condo") & (m.bedrooms == 1)]


def group(d):
    return {"listings": int(len(d)), "estimated_nights": float(d.occ.median()), "reviews_last_year": float(d.number_of_reviews_ltm.median()),
            "summer_nights_unavailable": float(d.summer_unavailable.median()), "net_yield": float(d.noi.sum() / d.allin.sum())}


T = {
    "pool": "core one-bedroom apartments", "pool_listings": int(len(core1)),
    "superhost": group(core1[core1.host_is_superhost == "t"]), "not_superhost": group(core1[core1.host_is_superhost != "t"]),
    "min_one_night": group(core1[core1.minimum_nights == 1]), "min_two_nights": group(core1[core1.minimum_nights == 2]),
    "rank_corr_estimate_vs_calendar": float(m.occ.corr(m.summer_unavailable, method="spearman")),
    "rank_corr_listings": int(m.summer_unavailable.notna().sum()),
}
pm, ht, cb, sg = (pd.read_csv(TAB / f) for f in ("portfolio_modes.csv", "house_tests.csv", "core_by_bedrooms.csv", "segment_yields.csv"))
five = pm[pm.label.str.contains("five-month")].iloc[0]
rec = pm[pm.label == "Hybrid (recommended)"].iloc[0]
T["five_month_season"] = {"noi_p50": float(five.noi_p50), "units_missing_tenancy_test": float(five.units_missing_tenancy_test),
                          "recommended_noi_p50": float(rec.noi_p50), "recommended_units_missing": float(rec.units_missing_tenancy_test)}
stack = ht[ht.test.str.contains("laneway")].iloc[0]
T["house_suite_laneway"] = {"net_yield": float(stack.net_yield), "core_one_bedroom_yield": float(ht[ht.test.str.contains("Core one-bedroom")].net_yield.iloc[0])}
T["two_bedroom"] = {"hybrid_yield": float(cb[cb.bedrooms == 2].hybrid_yield.iloc[0]), "one_bedroom_hybrid_yield": float(cb[cb.bedrooms == 1].hybrid_yield.iloc[0])}
mp = sg[(sg.neighbourhood_cleansed == "Mount Pleasant") & (sg.asset == "condo")].iloc[0]
T["mount_pleasant"] = {"listings": int(mp.listings), "net_yield": float(mp.net_yield), "lo": float(mp.net_yield_lo), "hi": float(mp.net_yield_hi)}
save_json(T, "tests_not_held.json")
print(json.dumps(T, indent=1))
