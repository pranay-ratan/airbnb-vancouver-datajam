"""Step 3. When do stays happen, and what does that do to price and to a seasonal operating plan?

Reviews are a proxy for stays (brief, data notes). We count review dates by month for the established
comparables only, so that growth in the number of listings does not distort the shape.

Writes  outputs/tables/monthly_stays.csv   reviews per month, established comparables, last two years
        outputs/tables/seasonality.json    month shares, seasonal price index, peak-season share and uplift
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # so the script also runs with python -I
from common import *
from config import SNAPSHOT, SNAP_DEC, SNAP_MAR, SNAP_SEP, PROC

comps = pd.read_csv(PROC / "comps.csv")
est = comps[comps.licensed & comps.established]
pb = load_json("price_basis.json")

r = pd.read_csv(RAW / SNAPSHOT / "reviews.csv.gz", usecols=["listing_id", "date"])
r["date"] = pd.to_datetime(r.date, format="%Y-%m-%d")
r = r[r.listing_id.isin(set(est.id))]

# last 12 complete months before the scrape; every established comparable was live for all of them
win = r[(r.date >= "2025-06-01") & (r.date <= "2026-05-31")]
prev = r[(r.date >= "2024-06-01") & (r.date <= "2025-05-31")]
share = (win.groupby(win.date.dt.month).size() / len(win)).reindex(range(1, 13)).fillna(0)
share_core = win[win.listing_id.isin(set(est[est.core & (est.asset == "condo")].id))]
share_core = (share_core.groupby(share_core.date.dt.month).size() / len(share_core)).reindex(range(1, 13)).fillna(0)
monthly = pd.DataFrame({"reviews_jun25_may26": win.groupby(win.date.dt.month).size(),
                        "reviews_jun24_may25": prev.groupby(prev.date.dt.month).size(),
                        "share_jun25_may26": share.round(4), "share_core_apartments": share_core.round(4)})
monthly.index.name = "month"
monthly.to_csv(TAB / "monthly_stays.csv")

# Seasonal price index, September = 1.00. Three points are measured on the same listings (02_price_basis):
# March, the first June week and late-July/August quotes. The rest is interpolated and winter is held at the
# March level because the December 2025 file has no prices at all.
mar, summer = pb["march_over_sept"], pb.get("post_cup_summer_ratio", 1.14)
idx = pd.Series({1: mar, 2: mar, 3: mar, 4: (2 * mar + 1) / 3 + 0.01, 5: (mar + 2) / 3 + 0.02, 6: 1.08,
                 7: max(summer, 1.14), 8: max(summer, 1.14), 9: 1.00, 10: (1 + mar) / 2 + 0.01, 11: mar, 12: mar})
annual_mean = float((share * idx).sum())        # stay-weighted annual price level relative to September

# best consecutive months for nightly stays, for a four-month and a five-month season
def season(length):
    best = max(range(1, 13), key=lambda s: sum(share[(s + i - 1) % 12 + 1] for i in range(length)))
    months = [(best + i - 1) % 12 + 1 for i in range(length)]
    sh = float(share[months].sum())
    return {"peak_months": months, "peak_share": sh,
            "peak_adr_uplift": float((share[months] * idx[months]).sum() / share[months].sum() / annual_mean),
            "peak_after_june_share": float(share[[m for m in months if m >= 6]].sum() / sh)}


four, five = season(4), season(5)

S = {"month_share": {int(m): float(v) for m, v in share.items()},
     "month_share_core_apartments": {int(m): float(v) for m, v in share_core.items()},
     "price_index_sept_100": {int(m): float(v) for m, v in idx.items()},
     "annual_price_level_vs_sept": annual_mean,
     **four,                                   # the recommended plan: nightly in the four peak months
     "five_month_season": five,                # the alternative we tested (decision log)
     "off_season_share": 1 - four["peak_share"],
     "jun_dec_share": float(share[[6, 7, 8, 9, 10, 11, 12]].sum()),          # months after a 1 June opt-out
     "reviews_in_window": int(len(win)), "established_comps": int(len(est))}

# Did the World Cup summer lift stays for hosts who were already established? (September reviews file)
if has_snapshot(SNAP_SEP, "reviews"):
    rs = pd.read_csv(RAW / SNAP_SEP / "reviews.csv.gz", usecols=["listing_id", "date"])
    rs["date"] = pd.to_datetime(rs.date, format="%Y-%m-%d")
    old = set(comps[comps.age_m >= 24].id)                 # live for both summers
    rs = rs[rs.listing_id.isin(old)]
    cup26 = int(((rs.date >= "2026-06-13") & (rs.date <= "2026-08-31")).sum())
    cup25 = int(((rs.date >= "2025-06-13") & (rs.date <= "2025-08-31")).sum())
    S["summer_reviews_2026_vs_2025_same_listings"] = cup26 / cup25
    S["summer_listings_compared"] = int(rs.listing_id.nunique())

# Rolling 12-month stays for listings that were established in every snapshot (supply dilution check)
snaps = [s for s in (SNAP_DEC, SNAP_MAR, SNAPSHOT, SNAP_SEP) if has_snapshot(s)]
if len(snaps) == 4:
    L = {s: load_listings(s) for s in snaps}
    ids = None
    for s in snaps:
        x = L[s]
        x = set(x[x.entire & (x.stay == "nightly")].id)
        ids = x if ids is None else ids & x
    d0 = L[SNAP_DEC]
    ids &= set(d0[d0.first_review_d < "2024-12-14"].id)
    tot = {s: int(L[s][L[s].id.isin(ids)].number_of_reviews_ltm.sum()) for s in snaps}
    S["rolling_stays_index"] = {s: tot[s] / tot[SNAP_DEC] for s in snaps}
    S["rolling_stays_listings"] = len(ids)

save_json(S, "seasonality.json")
print(monthly.to_string())
print(json.dumps({k: v for k, v in S.items() if not k.startswith("month_share")}, indent=1, default=float))
