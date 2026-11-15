"""Step 7. The decision log in numbers: for each choice, what the alternative would have given.

Headline used for comparison: pooled 2027 net yield of core one-bedroom apartments.

Writes  outputs/tables/decisions.json
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # so the script also runs with python -I
import copy
from common import *
from config import PROC, BENCH
from assumptions import A, add_costs, nightly, hybrid

pb, S = load_json("price_basis.json"), load_json("seasonality.json")
raw = pd.read_csv(PROC / "comps.csv")
is_core1 = raw.core & (raw.asset == "condo") & (raw.bedrooms == 1)


def run(d, deflate=True, Am=A, zone_fix=None):
    d = d.copy()
    if zone_fix:
        d.loc[d.neighbourhood_cleansed.eq(zone_fix[0]), "zone"] = zone_fix[1]
    d["adr"] = d.price_n / (d.asset.map(pb["june_over_sept"]) if deflate else 1.0) * (S["annual_price_level_vs_sept"] if deflate else 1.0)
    d["nights"] = d.occ
    d = add_costs(d, Am)
    n, h = nightly(d, Am), hybrid(d, S, Am)
    return {"listings": int(len(d)), "nightly_yield": float(n.noi.sum() / d.allin.sum()), "hybrid_yield": float(h.noi.sum() / d.allin.sum()),
            "median_nights": float(d.nights.median()), "median_price": float(d.adr.median()), "guest_rev_per_unit": float(n.guest_rev.mean())}


base = run(raw[is_core1 & raw.licensed & raw.established])
D = {"base": base}

# D1 price basis: take the June quotes at face value
D["price_as_quoted"] = run(raw[is_core1 & raw.licensed & raw.established], deflate=False)
# D2 comparable set
D["all_ages"] = run(raw[is_core1 & raw.licensed & (raw.number_of_reviews_ltm >= 1)])            # include listings under 12 months old
D["no_licence_filter"] = run(raw[is_core1 & raw.established])
D["all_ages_any_licence"] = run(raw[is_core1 & (raw.number_of_reviews_ltm >= 1)])
D["every_priced_listing"] = run(raw[is_core1])
# D6 platform fee: the old 3% host fee
a3 = copy.deepcopy(A); a3["airbnb_fee"] = 0.03
D["fee_3pct"] = run(raw[is_core1 & raw.licensed & raw.established], Am=a3)
# D7 Downtown Eastside priced at the East benchmark instead of West
dt = raw[(raw.neighbourhood_cleansed == "Downtown Eastside") & (raw.asset == "condo") & raw.licensed & raw.established]
D["dtes_west_price"], D["dtes_east_price"] = run(dt), run(dt, zone_fix=("Downtown Eastside", "E"))
# D8 houses: counting every 'Entire home' as a detached house (0-2 bedroom ones included)
l = load_listings("2026-06-15")
alt = nightly_priced(l)
alt = alt[alt.asset.isin(["house", "small_home"]) & alt.licensed & (alt.age_m >= 12) & (alt.number_of_reviews_ltm >= 1)].copy()
D["houses_3plus_bedrooms"] = run(raw[(raw.asset == "house") & raw.licensed & raw.established])
alt["asset"] = "house"
alt["bedrooms"] = alt.bedrooms.clip(lower=3)
D["houses_all_entire_homes"] = run(alt)
D["small_entire_homes_dropped"] = int((nightly_priced(l).asset == "small_home").sum())
D["suites_dropped"] = int((nightly_priced(l).asset == "suite").sum())

save_json(D, "decisions.json")
for k, v in D.items():
    print(k, v if not isinstance(v, dict) else {a: round(b, 4) for a, b in v.items()})
