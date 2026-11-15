"""Step 2. What is a fair 2027 nightly price?

The price field is a quote for one specific stay, usually within days of the scrape. The 15 June 2026
scrape therefore quoted stays during the FIFA World Cup (Vancouver matches 13 June - 7 July 2026).
We measure the same listings in the March and September 2026 snapshots (same public source) and
build an annual price basis from the three measured points.

Writes  outputs/tables/price_ratios.csv   same-listing price ratios, by segment and by quote week
        outputs/tables/price_basis.json   deflator from June quotes to September level, by asset class
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # so the script also runs with python -I
from common import *
from config import SNAPSHOT, SNAP_MAR, SNAP_SEP

# Fallback if the September/March archive files are not in data/raw (values measured in this repo, see README)
FALLBACK = {"june_over_sept": {"condo": 1.142, "townhouse": 1.17, "house": 1.17}, "march_over_sept": 0.879, "measured": False}

jun = nightly_priced(load_listings(SNAPSHOT))
rows, basis = [], dict(FALLBACK)

if has_snapshot(SNAP_SEP):
    sep = nightly_priced(load_listings(SNAP_SEP)).set_index("id").price_n.rename("sep")
    j = jun.join(sep, on="id", how="inner")
    j["r"] = j.price_n / j.sep
    j["group"] = np.where(j.asset.eq("condo"), "condo", "house and other")

    def add(label, g):
        rows.append({"comparison": "June / September", "segment": label, "listings": len(g), "median_ratio": g.r.median(),
                     "p25": g.r.quantile(.25), "p75": g.r.quantile(.75)})

    add("all nightly entire homes", j)
    add("apartments", j[j.asset == "condo"])
    add("core apartments", j[(j.asset == "condo") & j.core])
    add("townhouses and houses", j[j.asset.isin(["townhouse", "house"])])
    add("same quote length in both files", j[j.q_nights == j.join(nightly_priced(load_listings(SNAP_SEP)).set_index("id").q_nights.rename("qs"), on="id").qs])
    for wk, g in j.groupby(j.q_in.dt.to_period("W")):
        if len(g) >= 25:
            rows.append({"comparison": "June / September", "segment": f"June quote for the week of {wk.start_time.date()}",
                         "listings": len(g), "median_ratio": g.r.median(), "p25": g.r.quantile(.25), "p75": g.r.quantile(.75)})
    basis = {"measured": True,
             "june_over_sept": {"condo": float(j[j.asset == "condo"].r.median()),
                                "townhouse": float(j[j.asset.isin(["townhouse", "house"])].r.median()),
                                "house": float(j[j.asset.isin(["townhouse", "house"])].r.median())},
             "june_over_sept_all": float(j.r.median()), "june_over_sept_core_condo": float(j[(j.asset == "condo") & j.core].r.median()),
             "n_same_listing": int(len(j)),
             "peak_week_ratio": float(max(r["median_ratio"] for r in rows if r["segment"].startswith("June quote"))),
             "first_week_ratio": float(next(r["median_ratio"] for r in rows if r["segment"].startswith("June quote")))}
    late = j[j.q_in >= "2026-07-20"]                       # quotes made in June for stays after the tournament
    basis["post_cup_summer_ratio"] = float(late.r.median()); basis["post_cup_summer_n"] = int(len(late))
    if has_snapshot(SNAP_MAR):
        mar = nightly_priced(load_listings(SNAP_MAR))
        m = mar[(mar.asset == "condo") & mar.core].join(sep, on="id", how="inner")
        m["r"] = m.price_n / m.sep
        rows.append({"comparison": "March / September", "segment": "core apartments", "listings": len(m), "median_ratio": m.r.median(),
                     "p25": m.r.quantile(.25), "p75": m.r.quantile(.75)})
        basis["march_over_sept"] = float(m.r.median()); basis["n_march"] = int(len(m))
    basis["median_price_june_nightly"] = float(jun.price_n.median())
    basis["median_price_sept_nightly"] = float(nightly_priced(load_listings(SNAP_SEP)).price_n.median())

pd.DataFrame(rows).round(3).to_csv(TAB / "price_ratios.csv", index=False)
save_json(basis, "price_basis.json")
print(pd.DataFrame(rows).round(3).to_string(index=False))
print(json.dumps(basis, indent=1))
