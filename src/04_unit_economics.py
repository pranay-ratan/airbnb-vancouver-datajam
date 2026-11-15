"""Step 4. 2027 unit economics for every comparable listing, then the segment comparisons.

Return metric: 2027 net operating income / all-in purchase cost ("net yield"), all-cash.
Price basis:   June quote / same-listing June-to-September ratio x annual seasonal level (steps 2-3).
Nights:        Inside Airbnb's estimate for the 12 months to mid-June 2026 (before the World Cup).

Writes  data/processed/comps_econ.csv        per-listing economics (not published)
        outputs/tables/asset_yields.csv       apartment vs townhouse vs house: revenue yield and net yield
        outputs/tables/segment_yields.csv     neighbourhood x asset, with bootstrap 90% interval
        outputs/tables/core_by_bedrooms.csv   core apartments by bedrooms: nightly, lease and hybrid
        outputs/tables/operating_modes.csv    the recommended pool under each way of operating
        outputs/tables/house_tests.csv        the house variants we tested
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # so the script also runs with python -I
from common import *
from config import SNAPSHOT, PROC, SEED, BENCH
from assumptions import A, add_costs, nightly, lease, hybrid, vacancy_tax

pb, S = load_json("price_basis.json"), load_json("seasonality.json")
rng = np.random.default_rng(SEED)


def price_and_nights(d):
    """Annualised guest-facing nightly price and booked nights for each listing."""
    d = d.copy()
    d["adr"] = d.price_n / d.asset.map(pb["june_over_sept"]) * S["annual_price_level_vs_sept"]
    d["nights"] = d.occ
    return d


def economics(d, **kw):
    d = add_costs(price_and_nights(d), **kw)
    n = nightly(d)
    d["guest_rev"], d["payout"], d["noi"] = n.guest_rev, n.payout, n.noi
    d["yield"] = d.noi / d.allin
    return d


allc = pd.read_csv(PROC / "comps.csv")
c = economics(allc[allc.licensed & allc.established])
c.to_csv(PROC / "comps_econ.csv", index=False)


def pooled(g, col="noi", cost="allin"):
    return g[col].sum() / g[cost].sum()


def boot(g, n=1000):
    """90% bootstrap interval for the pooled net yield of a segment."""
    v, k = g[["noi", "allin"]].values, len(g)
    ys = [(lambda s: s[:, 0].sum() / s[:, 1].sum())(v[rng.integers(0, k, k)]) for _ in range(n)]
    return np.percentile(ys, 5), np.percentile(ys, 95)


def summary(g):
    lo, hi = boot(g)
    return pd.Series({"listings": len(g), "median_price": g.adr.median(), "median_nights": g.nights.median(),
                      "median_guest_revenue": g.guest_rev.median(), "median_noi": g.noi.median(), "median_allin_cost": g.allin.median(),
                      "revenue_yield": pooled(g, "guest_rev"), "net_yield": pooled(g), "net_yield_lo": lo, "net_yield_hi": hi,
                      "median_unit_yield": g["yield"].median(), "share_losing_money": (g.noi < 0).mean()})


# ---- apartment vs townhouse vs house --------------------------------------------------------------
asset = c.groupby("asset").apply(summary).reindex(["condo", "townhouse", "house"])
asset.to_csv(TAB / "asset_yields.csv")

# ---- neighbourhood x asset -------------------------------------------------------------------------
seg = c.groupby(["neighbourhood_cleansed", "asset"]).apply(summary).reset_index()
seg = seg[seg.listings >= 15].sort_values("net_yield", ascending=False)
seg.to_csv(TAB / "segment_yields.csv", index=False)

# ---- core apartments by bedrooms: nightly vs lease vs hybrid ---------------------------------------
core = c[c.core & (c.asset == "condo") & c.bedrooms.between(1, 2)].copy()
S5, A5 = {**S, **S["five_month_season"]}, {**A, "mid_months": 7}       # the five-month nightly season we tested
le, hy, hy5 = lease(core), hybrid(core, S), hybrid(core, S5, A5)
core["lease_noi"], core["lease_cost"], core["hybrid_noi"], core["hybrid5_noi"] = le.noi, le.cost, hy.noi, hy5.noi
core["vac_tax"] = vacancy_tax(core)
rows = []
for b, g in core.groupby("bedrooms"):
    rows.append({"bedrooms": int(b), "listings": len(g), "median_price": g.adr.median(), "median_nights": g.nights.median(),
                 "allin_cost": g.allin.median(), "nightly_yield": pooled(g), "lease_yield": pooled(g, "lease_noi", "lease_cost"),
                 "hybrid_yield": pooled(g, "hybrid_noi"), "nightly_noi": g.noi.mean(), "lease_noi": g.lease_noi.mean(),
                 "hybrid_noi": g.hybrid_noi.mean(), "share_nightly_beats_lease": (g["yield"] > g.lease_noi / g.lease_cost).mean(),
                 "share_hybrid_beats_lease": (g.hybrid_noi / g.allin > g.lease_noi / g.lease_cost).mean(),
                 "share_hybrid_beats_nightly": (g.hybrid_noi > g.noi).mean()})
bybed = pd.DataFrame(rows)
bybed.to_csv(TAB / "core_by_bedrooms.csv", index=False)
core.to_csv(PROC / "core_econ.csv", index=False)

# ---- the recommended pool (core one-bedroom apartments) under each operating mode -------------------
p = core[core.bedrooms == 1]
modes = pd.DataFrame([
    {"mode": "Nightly all year, vacancy taxes not applied", "noi_per_unit": p.noi.mean(), "yield": pooled(p)},
    {"mode": "Nightly all year, Empty Homes Tax and Speculation Tax applied", "noi_per_unit": (p.noi - p.vac_tax).mean(),
     "yield": (p.noi - p.vac_tax).sum() / p.allin.sum()},
    {"mode": "Unfurnished 12-month lease", "noi_per_unit": p.lease_noi.mean(), "yield": pooled(p, "lease_noi", "lease_cost")},
    {"mode": "Hybrid: nightly in the four peak months, 30+-night stays in the other eight", "noi_per_unit": p.hybrid_noi.mean(), "yield": pooled(p, "hybrid_noi")},
    {"mode": "Hybrid with a five-month nightly season (tested, not chosen)", "noi_per_unit": p.hybrid5_noi.mean(), "yield": pooled(p, "hybrid5_noi")},
])
modes["vacancy_tax_per_unit"] = [0, p.vac_tax.mean(), 0, 0, 0]
modes.to_csv(TAB / "operating_modes.csv", index=False)

# ---- houses: the variants we tested -----------------------------------------------------------------
h = c[c.asset == "house"]
longer = economics(allc[allc.licensed & allc.established & (allc.asset == "house")].assign(occ=lambda d: np.minimum(d.occ * 1.5, 255)))
# house + basement suite + laneway home on one East-side lot, each let separately
raw = load_listings(SNAPSHOT)
su = raw[raw.entire & (raw.stay == "nightly") & raw.price_n.between(40, 2000) & raw.licensed & (raw.age_m >= 12)
         & (raw.number_of_reviews_ltm >= 1) & (raw.zone == "E")]
unit = {}
for name, mask in (("suite", su.property_type.eq("Entire guest suite")), ("laneway", su.property_type.eq("Entire guesthouse"))):
    g = su[mask]
    adr = g.price_n.median() / pb["june_over_sept"]["house"] * S["annual_price_level_vs_sept"]
    nights = g.occ.median() * (1 - A["first_year_haircut"])
    payout = adr * nights * (1 - A["airbnb_fee"])
    unit[name] = {"n": len(g), "noi_before_fixed": payout * (1 - A["mgmt_fee"] - A["supplies_pct"]) - nights / 3 * 105,
                  "guest_rev": adr * nights}
he = h[h.zone == "E"]
lot_price = BENCH[("E", "house")] * 1.20                      # assumption: 20% premium for a legal suite plus laneway home
stack_cost = lot_price * (1 + A["legal_pct"]) + float(np.asarray(__import__("assumptions").ptt(lot_price))) + 55000
stack_noi = (he.payout.median() * (1 - A["mgmt_fee"] - A["supplies_pct"]) - he.nights.median() * 0.9 / 3 * he.clean.median()
             + unit["suite"]["noi_before_fixed"] + unit["laneway"]["noi_before_fixed"]
             - (A["prop_tax"] + A["maint"]["house"]) * lot_price - 3600 - 2 * 1200 - 3000 - 3 * A["licences"])
tests = pd.DataFrame([
    {"test": "Houses (3+ bedrooms), west side", "listings": int((h.zone == "W").sum()), "revenue_yield": pooled(h[h.zone == "W"], "guest_rev"), "net_yield": pooled(h[h.zone == "W"])},
    {"test": "Houses (3+ bedrooms), east side", "listings": len(he), "revenue_yield": pooled(he, "guest_rev"), "net_yield": pooled(he)},
    {"test": "Houses if stays run 50% longer than Inside Airbnb assumes", "listings": len(longer), "revenue_yield": pooled(longer, "guest_rev"), "net_yield": pooled(longer)},
    {"test": "East-side house + suite + laneway home, three listings on one lot", "listings": int(len(he) + unit["suite"]["n"] + unit["laneway"]["n"]),
     "revenue_yield": (he.guest_rev.median() + unit["suite"]["guest_rev"] + unit["laneway"]["guest_rev"]) / stack_cost, "net_yield": stack_noi / stack_cost},
    {"test": "Core one-bedroom apartments (for comparison)", "listings": len(p), "revenue_yield": pooled(p, "guest_rev"), "net_yield": pooled(p)},
])
tests.to_csv(TAB / "house_tests.csv", index=False)

pd.set_option("display.width", 250)
print("comps:", len(c)); print(asset.round(4).to_string()); print(seg.round(4).head(14).to_string()); print(seg.round(4).tail(6).to_string())
print(bybed.round(4).to_string()); print(modes.round(4).to_string()); print(tests.round(4).to_string())
