"""Step 5. From units to a $10M portfolio: few large assets or many small ones, and how to operate them.

Each simulated portfolio is filled by drawing real comparable listings at random until the next one
no longer fits in $10M. Every draw then gets a market-wide demand shock, a market-wide price shock,
unit-level noise and the observed licence-suspension rate.

Writes  outputs/tables/strategies.csv        asset strategies, nightly operation, vacancy taxes not applied
        outputs/tables/portfolio_modes.csv   the recommended pool under each operating mode and opt-out scenario
        outputs/tables/sensitivity.csv       one-at-a-time stress of the recommended plan
        outputs/tables/sim_draws.csv         simulated NOI draws for the recommended plan (for the dashboard histogram)
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # so the script also runs with python -I
import copy
from common import *
from config import PROC, BUDGET, SEED, NSIM
from assumptions import A, add_costs, nightly, lease, hybrid, vacancy_tax

S, prof = load_json("seasonality.json"), load_json("data_profile.json")
c = pd.read_csv(PROC / "comps_econ.csv")
rng = np.random.default_rng(SEED)

P_SUSPEND = prof["brief_city_counts"]["suspensions"] / prof["brief_city_counts"]["licences"]   # 69 / 3,248 (brief, p.3)
SD_DEMAND, SD_PRICE, SD_UNIT = 0.10, 0.05, 0.15      # market-wide nights, market-wide price, unit-level noise (log sd)
VAR_SHARE = A["mgmt_fee"] + A["supplies_pct"]


def simulate(pool, mode="nightly", erosion=0.0, nsim=NSIM, tax=False, season=None, mid_months=None):
    """Return an array (nsim x 4): NOI, capital deployed, number of units, units that miss the six-month tenancy test."""
    Sx = S if season is None else {**S, **season}
    mm = A["mid_months"] if mid_months is None else mid_months
    pool = pool.reset_index(drop=True)
    k = len(pool)
    cost = pool.allin.values
    if mode == "lease":
        cost = (pool.allin - pool.furnish).values
    base_pay = pool.payout.values                                  # nightly payout, full year, before shocks
    cleans = (pool.nights * (1 - A["first_year_haircut"]) / A["stay_nights"] * pool.clean).values
    fixed = pool.fixed_str.values
    out = np.zeros((nsim, 4))
    if mode in ("hybrid", "lease"):
        beds = pool.bedrooms.clip(1, 2).astype(int)
        mid_rent, lease_rent = beds.map(A["mid_rent"]).values, beds.map(A["lease_rent"]).values
        holding = pool.holding.values
    vt = vacancy_tax(pool).values
    for s in range(nsim):
        sel, spent = [], 0.0
        while True:
            i = rng.integers(k)
            if spent + cost[i] > BUDGET:
                break
            sel.append(i); spent += cost[i]
        sel = np.array(sel); n = len(sel)
        demand = np.exp(rng.normal(0, SD_DEMAND)) * np.exp(rng.normal(0, SD_UNIT, n))
        price = np.exp(rng.normal(0, SD_PRICE))
        suspended = rng.random(n) < P_SUSPEND
        if mode == "nightly":
            share_hit = S["jun_dec_share"]                          # share of the year's stays after a 1 June opt-out
            pay = base_pay[sel] * demand * price * (1 - erosion * share_hit) * np.where(suspended, 0.5, 1.0)
            cl = cleans[sel] * demand * np.where(suspended, 0.5, 1.0)
            noi = pay * (1 - VAR_SHARE) - cl - fixed[sel] - (vt[sel] if tax else 0)
        elif mode == "hybrid":
            pay = (base_pay[sel] * Sx["peak_share"] * Sx["peak_adr_uplift"] * demand * price
                   * (1 - erosion * Sx["peak_after_june_share"]) * np.where(suspended, 0.5, 1.0))
            cl = cleans[sel] * Sx["peak_share"] * demand * np.where(suspended, 0.5, 1.0)
            occ = np.clip(rng.normal(A["mid_occupancy"], 0.06, n), 0.5, 1.0)
            mid = mid_rent[sel] * np.exp(rng.normal(0, 0.05)) * mm * occ
            missed = occ * mm * 30.44 < A["tenancy_days_required"]        # unit fails the six-month test and owes both taxes
            noi = (pay * (1 - VAR_SHARE) - cl + mid * (1 - A["mid_mgmt"]) - A["mid_turnovers"] * A["mid_turn_cost"]
                   - fixed[sel] - np.where(missed, vt[sel], 0))
            out[s, 3] = missed.sum()
        else:                                                       # unfurnished 12-month lease
            rent = lease_rent[sel] * np.exp(rng.normal(0, 0.05))
            noi = rent * 12 * (1 - A["lease_vacancy"]) * (1 - A["lease_mgmt"]) - holding[sel] - A["lease_insurance"]
        out[s, :3] = noi.sum(), spent, n
    return out


def describe(o, label, **extra):
    y = o[:, 0] / o[:, 1]
    return {"label": label, **extra, "units": int(np.median(o[:, 2])), "deployed": float(np.median(o[:, 1])),
            "noi_p10": np.percentile(o[:, 0], 10), "noi_p50": np.percentile(o[:, 0], 50), "noi_p90": np.percentile(o[:, 0], 90),
            "yield_p10": np.percentile(y, 10), "yield_p50": np.percentile(y, 50), "yield_p90": np.percentile(y, 90),
            "prob_yield_below_1pct": float((y < 0.01).mean()), "prob_loss": float((o[:, 0] < 0).mean()),
            "units_missing_tenancy_test": float(o[:, 3].mean())}


condo, house = c[c.asset == "condo"], c[c.asset == "house"]
core12 = condo[condo.core & condo.bedrooms.between(1, 2)]
core1 = condo[condo.core & (condo.bedrooms == 1)]
pools = [("Few large: west-side houses", house[house.zone == "W"]),
         ("Houses, east side", house[house.zone == "E"]),
         ("Many small: apartments city-wide", condo),
         ("Core 1-2 bedroom apartments", core12),
         ("Core one-bedroom apartments", core1)]
strat = pd.DataFrame([describe(simulate(p), name, pool_listings=len(p)) for name, p in pools])
strat.to_csv(TAB / "strategies.csv", index=False)

# ---- the recommended pool under each operating mode, and under a Vancouver opt-out -------------------
ratio = prof["core_apartments_90plus"] / prof["core_apartments_nightly"]      # supply that could switch to nightly
worst = 1 - 1 / (1 + ratio)                                                    # revenue loss if all of it does and demand is flat
runs = [("Nightly all year (vacancy taxes not applied)", dict(mode="nightly")),
        ("Nightly all year, with Empty Homes Tax and Speculation Tax", dict(mode="nightly", tax=True)),
        ("Unfurnished 12-month lease", dict(mode="lease")),
        ("Hybrid (recommended)", dict(mode="hybrid")),
        ("Hybrid with a five-month nightly season (tested, not chosen)", dict(mode="hybrid", season=S["five_month_season"], mid_months=7)),
        ("Hybrid, opt-out from 1 June cuts nightly revenue 10%", dict(mode="hybrid", erosion=0.10)),
        ("Hybrid, opt-out cuts nightly revenue 20%", dict(mode="hybrid", erosion=0.20)),
        (f"Hybrid, opt-out worst case ({worst:.0%}: every 90-night apartment switches)", dict(mode="hybrid", erosion=worst)),
        ("Nightly, opt-out cuts nightly revenue 20%", dict(mode="nightly", erosion=0.20))]
modes, draws = [], None
for name, kw in runs:
    o = simulate(core1, **kw)
    modes.append(describe(o, name))
    if name == "Hybrid (recommended)":
        draws = o
modes = pd.DataFrame(modes)
modes["optout_supply_ratio"], modes["optout_worst_erosion"] = ratio, worst
modes.to_csv(TAB / "portfolio_modes.csv", index=False)
pd.DataFrame(draws[:, :3], columns=["noi", "deployed", "units"]).round(0).to_csv(TAB / "sim_draws.csv", index=False)

# ---- one-at-a-time sensitivity of the recommended plan (pooled yield, no simulation noise) -----------
raw = pd.read_csv(PROC / "comps.csv")
base = raw[raw.licensed & raw.established & raw.core & (raw.asset == "condo") & (raw.bedrooms == 1)]
pb = load_json("price_basis.json")


def plan_yield(Am=A, price_mult=1.0, occ_mult=1.0, adr_mult=1.0, mid_rent_mult=1.0, mid_occ=None, mode="hybrid"):
    d = base.copy()
    d["adr"] = d.price_n / pb["june_over_sept"]["condo"] * S["annual_price_level_vs_sept"]
    d["nights"] = d.occ
    d = add_costs(d, Am, price_mult)
    if mode == "hybrid":
        noi = hybrid(d, S, Am, occ_mult, adr_mult, mid_rent_mult, mid_occ).noi
    else:
        noi = nightly(d, Am, occ_mult, adr_mult).noi
    return noi.sum() / d.allin.sum()


def mod(**kw):
    a = copy.deepcopy(A); a.update(kw); return a


b = plan_yield()
sens = [("Purchase price 20% higher / lower", plan_yield(price_mult=1.2), plan_yield(price_mult=0.8)),
        ("Booked nights 20% lower / higher", plan_yield(occ_mult=0.8), plan_yield(occ_mult=1.2)),
        ("Nightly price 10% lower / higher", plan_yield(adr_mult=0.9), plan_yield(adr_mult=1.1)),
        ("Furnished monthly rent 15% lower / higher", plan_yield(mid_rent_mult=0.85), plan_yield(mid_rent_mult=1.15)),
        ("Off-season let 75% / 95% of the time", plan_yield(mid_occ=0.75), plan_yield(mid_occ=0.95)),
        ("Manager fee 25% / 15%", plan_yield(mod(mgmt_fee=0.25)), plan_yield(mod(mgmt_fee=0.15))),
        ("Strata fees 30% higher / lower", plan_yield(mod(strata={k: v * 1.3 for k, v in A["strata"].items()})),
         plan_yield(mod(strata={k: v * 0.7 for k, v in A["strata"].items()}))),
        ("First-year haircut 20% / none", plan_yield(mod(first_year_haircut=0.20)), plan_yield(mod(first_year_haircut=0.0)))]
sens = pd.DataFrame(sens, columns=["driver", "downside_yield", "upside_yield"])
sens["base_yield"] = b
sens["swing"] = sens.upside_yield - sens.downside_yield
sens = sens.sort_values("swing", ascending=False)
sens.to_csv(TAB / "sensitivity.csv", index=False)

pd.set_option("display.width", 260)
print(strat.round(4).to_string()); print(modes.round(4).to_string()); print(sens.round(4).to_string())
print("nightly pooled yield check", round(plan_yield(mode="nightly"), 4), "| hybrid", round(b, 4), "| suspension p", round(P_SUSPEND, 4))
