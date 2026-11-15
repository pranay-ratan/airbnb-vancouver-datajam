"""Step 1. Data-quality profile of the 15 June 2026 snapshot and the cleaning funnel.

Writes  outputs/tables/data_profile.json   facts about the raw file quoted on the data slide
        outputs/tables/cleaning_funnel.csv every filter with the number of listings left
        data/processed/comps.csv           one row per comparable listing (no names, URLs or licence numbers)
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # so the script also runs with python -I
from common import *
from config import SNAPSHOT, SNAP_DEC, SNAP_MAR, SNAP_SEP, PROC

l = load_listings(SNAPSHOT)
P = {"snapshot": SNAPSHOT, "rows": len(l), "columns": int(l.shape[1] - 18)}   # 18 = tags added by load_listings
P["columns"] = len(pd.read_csv(RAW / SNAPSHOT / "listings.csv.gz", nrows=0).columns)

# ---- 1. when was each row scraped? --------------------------------------------------------------
P["scrape_dates"] = l.last_scraped.value_counts().sort_index().to_dict()
P["rows_previous_scrape"] = int(l.source.eq("previous scrape").sum())

# ---- 2. what is the price field? ----------------------------------------------------------------
e = l[l.entire]
P["entire_homes"] = len(e)
P["price_missing_share_all"] = float(l.price_n.isna().mean())
q = l[l.q_nights.notna()]
P["quote_nights_counts"] = {int(k): int(v) for k, v in q.q_nights.value_counts().head(6).items()}
P["quote_days_ahead_median"] = float((q.q_in - q.scraped).dt.days.median())
P["quote_checkin_by_week"] = {str(k.start_time.date()): int(v) for k, v in q.q_in.dt.to_period("W").value_counts().sort_index().head(8).items()}
# 90-night quotes: the June file divides ONE month's price by 90 nights
raw90 = l[(l.q_nights >= 90) & l.price_quote_raw.notna()].head(600)
ratio = []
for price, raw in zip(raw90.price_n, raw90.price_quote_raw):
    try:
        sub = json.loads(raw)["quote"].get("discounted_subtotal")
        if sub and price:
            ratio.append(float(sub) / price)
    except Exception:
        pass
P["q90_month_price_over_price_field"] = float(np.median(ratio)) if ratio else None   # 90 => price field = month price / 90

# ---- 3. what is 'estimated occupancy'? ----------------------------------------------------------
k = e[(e.stay == "nightly")]
est = np.minimum(255, 2 * k.number_of_reviews_ltm * np.maximum(3, k.minimum_nights))
P["occ_formula_match_share"] = float((est == k.occ).mean())        # reviews x 2 x max(3, min nights), capped at 255
P["occ_at_cap_share"] = float((k.occ >= 255).mean())
P["revenue_is_price_x_occ_corr"] = float((k.price_n * k.occ).corr(k.estimated_revenue_l365d))

# ---- 4. stay-length segments: who is actually on the nightly market? ---------------------------
seg = e[~e.hotel_like].stay.value_counts()
P["stay_segments_entire"] = seg.to_dict()
P["share_90plus_entire"] = float((e.stay == "90+ nights").mean())
apt = e[e.asset == "condo"]
P["apartments_nightly"] = int((apt.stay == "nightly").sum())
P["apartments_90plus"] = int((apt.stay == "90+ nights").sum())
P["core_apartments_nightly"] = int(((apt.stay == "nightly") & apt.core).sum())
P["core_apartments_90plus"] = int(((apt.stay == "90+ nights") & apt.core).sum())
m90 = apt[(apt.stay == "90+ nights") & apt.core & apt.price_n.notna() & (apt.q_nights >= 90)]
P["core_90plus_month_asking_1br"] = float((m90[m90.bedrooms == 1].price_n * 90).median())   # price field x 90 = one month
P["core_90plus_month_asking_2br"] = float((m90[m90.bedrooms == 2].price_n * 90).median())

# ---- 5. licence field (an estimate from imperfect text, never a compliance verdict) ------------
n = e[(e.stay == "nightly") & ~e.hotel_like]
P["nightly_entire"] = len(n)
P["licence_both_numbers_share"] = float(n.licensed.mean())
P["licence_exempt_share"] = float(n.lic_exempt.mean())
P["licence_none_share"] = float((~n.lic_any).mean())
P["licence_year_prefix"] = n.muni_year.value_counts().head(4).to_dict()
P["brief_city_counts"] = {"active_listings": 4969, "licences": 3248, "suspensions": 69}

# ---- 6. how new are the listings? (World Cup surge) --------------------------------------------
P["nightly_no_review_yet"] = int(n.first_review_d.isna().sum())
P["nightly_first_review_within_6m"] = int((n.age_m < 6).sum())
P["nightly_new_share"] = float(((n.age_m < 6) | n.first_review_d.isna()).mean())
supply = {}
for s in (SNAP_DEC, SNAP_MAR, SNAPSHOT, SNAP_SEP):
    if has_snapshot(s):
        x = load_listings(s)
        x = x[x.entire & ~x.hotel_like]
        supply[s] = {"nightly": int((x.stay == "nightly").sum()), "90plus": int((x.stay == "90+ nights").sum())}
P["supply_by_snapshot"] = supply

# ---- cleaning funnel -----------------------------------------------------------------------------
steps = [("All listings in the 15 June 2026 file", len(l))]
d = l


def step(label, mask):
    global d
    d = d[mask]
    steps.append((label, len(d)))


step("Entire homes only (a fund buys whole units)", d.entire)
step("Drop hotel-like listings", ~d.hotel_like)
step("Nightly market: minimum stay under 28 nights", d.stay.eq("nightly"))
step("Has a price quote between $40 and $2,000", d.price_n.between(40, 2000))
step("Buyable asset: apartment, townhouse or 3+ bedroom house", d.asset.isin(["condo", "townhouse", "house"]))
priced = d.copy()
step("Shows both a City licence and a BC registration number", d.licensed)
step("Established: first review 12+ months before the scrape, and reviewed in the last year",
     (d.age_m >= 12) & (d.number_of_reviews_ltm >= 1))
funnel = pd.DataFrame(steps, columns=["step", "listings"])
funnel.to_csv(TAB / "cleaning_funnel.csv", index=False)
P["comps"] = len(d)

keep = ["id", "neighbourhood_cleansed", "zone", "core", "asset", "bedrooms", "accommodates", "price_n", "occ",
        "number_of_reviews_ltm", "minimum_nights", "age_m", "licensed", "lic_exempt", "host_is_superhost",
        "calculated_host_listings_count", "latitude", "longitude", "q_in", "q_nights", "last_scraped"]
priced = priced.assign(established=(priced.age_m >= 12) & (priced.number_of_reviews_ltm >= 1))
priced[keep + ["established"]].to_csv(PROC / "comps.csv", index=False)

save_json(P, "data_profile.json")
print(funnel.to_string(index=False))
for key in ("scrape_dates", "quote_nights_counts", "q90_month_price_over_price_field", "occ_formula_match_share", "occ_at_cap_share",
            "stay_segments_entire", "share_90plus_entire", "core_apartments_nightly", "core_apartments_90plus",
            "core_90plus_month_asking_1br", "licence_both_numbers_share", "licence_year_prefix", "nightly_new_share", "supply_by_snapshot"):
    print(f"{key}: {P[key]}")
