"""Every economic assumption in one place, with its source, plus the unit-economics functions.

Three ways to operate the same unit are modelled:
  nightly  stays under 28 nights all year (the classic short-term rental)
  lease    one unfurnished 12-month tenancy (the benchmark any short-term plan has to beat)
  hybrid   nightly stays in the four peak months, furnished stays of 30+ nights for the other eight
"""
import numpy as np
import pandas as pd
from config import BENCH

A = dict(
    # ---- revenue ----
    airbnb_fee=0.155,         # Airbnb host-only service fee on the guest-facing price (Airbnb, from 27 Oct 2025)
    first_year_haircut=0.10,  # new listing with no reviews. Data shows first-year listings do no worse (06_validation); kept as caution
    stay_nights=3.0,          # Inside Airbnb's own average-stay assumption; used only to count cleans
    # ---- nightly operating costs ----
    mgmt_fee=0.20,            # full-service manager, share of host payout (market range 15-25%)
    clean_base=70.0, clean_per_bed=35.0,   # $ per stay: 1BR $105, 2BR $140, 3BR $175
    supplies_pct=0.02,        # consumables, share of host payout
    utilities={"condo": 1800, "townhouse": 2700, "house": 3600},   # $/yr including internet
    insurance={"condo": 1500, "townhouse": 2200, "house": 3000},   # $/yr short-term-rental policy
    licences=1108 + 450,      # City of Vancouver STR licence $1,108 + BC registry $450 (host does not live in the unit)
    strata={0: 3900, 1: 5400, 2: 7600, 3: 10000},                  # condo $/yr by bedrooms (about $0.75/sq ft/month)
    strata_townhouse=4200,
    prop_tax=0.00336,         # City of Vancouver 2026 all-in residential rate, about $3.36 per $1,000
    maint={"condo": 0.003, "townhouse": 0.005, "house": 0.008},    # share of purchase price per year
    # ---- purchase ----
    legal_pct=0.005,
    furnish_base={"condo": 12000, "townhouse": 20000, "house": 25000}, furnish_per_bed=6000,
    # ---- vacancy taxes: owed on a home that is nobody's principal residence and is not rented for
    #      six months of the year in periods of 30+ days. Nightly stays do not count. ----
    eht=0.03,                 # City of Vancouver Empty Homes Tax, share of assessed value
    svt=0.01,                 # BC Speculation and Vacancy Tax, Canadian owners, 2026 rate
    # ---- unfurnished 12-month lease benchmark ----
    lease_rent={1: 2400, 2: 2900},  # $/month. 1BR: liv.rent asking, Aug 2026 (Downtown $2,460, West End $2,320). 2BR: CMHC 2025 rented-condo average
    lease_vacancy=0.015,      # CMHC 2025 rented-condo vacancy, Vancouver
    lease_mgmt=0.06, lease_insurance=800,
    # ---- furnished stays of 30+ nights (the hybrid's off-season) ----
    mid_rent={1: 2900, 2: 3500},    # $/month. 1BR: liv.rent furnished asking, Aug 2026 (Downtown $2,882, West End $2,928). 2BR scaled by 2,900/2,400
    mid_months=8,             # October-May (243 days); nightly stays June-September
    mid_occupancy=0.88,       # share of the off-season actually let. 0.88 x 243 = 214 days
    tenancy_days_required=180,  # six months in periods of 30+ days keeps a unit clear of both vacancy taxes
    mid_mgmt=0.10, mid_turnovers=4, mid_turn_cost=150,
)


def bed_factor(asset, beds):
    """Scale the area benchmark (a 'typical' home) to the unit's size. Our assumption; price is stress-tested +/-20%."""
    b = 0 if pd.isna(beds) else int(beds)
    if asset == "condo":
        return {0: 0.70, 1: 0.85, 2: 1.15}.get(b, 1.50)
    if asset == "townhouse":
        return 0.90 if b <= 2 else 1.00 if b == 3 else 1.15
    return {3: 0.90, 4: 1.00, 5: 1.10}.get(b, 1.25)        # house (3+ bedrooms only)


def ptt(p):
    """BC Property Transfer Tax, residential: 1% to $200K, 2% to $2M, 3% above, plus 2% above $3M."""
    p = np.asarray(p, dtype=float)
    return (0.01 * np.minimum(p, 200_000) + 0.02 * np.clip(p - 200_000, 0, 1_800_000)
            + 0.03 * np.maximum(p - 2_000_000, 0) + 0.02 * np.maximum(p - 3_000_000, 0))


def add_costs(d, A=A, price_mult=1.0):
    """Purchase price, all-in cost and annual fixed costs for each listing (needs zone, asset, bedrooms)."""
    d = d.copy()
    beds = d.bedrooms.fillna(1).clip(upper=6).astype(int)
    d["purchase"] = [BENCH[(z, a)] * bed_factor(a, b) * price_mult for z, a, b in zip(d.zone, d.asset, beds)]
    d["furnish"] = d.asset.map(A["furnish_base"]) + A["furnish_per_bed"] * beds
    d["allin"] = d.purchase + ptt(d.purchase) + A["legal_pct"] * d.purchase + d.furnish
    strata = np.where(d.asset.eq("condo"), beds.clip(upper=3).map(A["strata"]),
                      np.where(d.asset.eq("townhouse"), A["strata_townhouse"], 0))
    d["holding"] = strata + A["prop_tax"] * d.purchase + d.asset.map(A["maint"]) * d.purchase   # same in every mode
    d["fixed_str"] = d.holding + d.asset.map(A["utilities"]) + d.asset.map(A["insurance"]) + A["licences"]
    d["clean"] = A["clean_base"] + A["clean_per_bed"] * beds
    return d


def nightly(d, A=A, occ_mult=1.0, adr_mult=1.0):
    """2027 net operating income if the unit is let by the night all year.
    d needs adr (annualised, guest-facing nightly price) and nights (booked nights per year)."""
    nights = np.minimum(d.nights * occ_mult, 330) * (1 - A["first_year_haircut"])
    guest = d.adr * adr_mult * nights
    payout = guest * (1 - A["airbnb_fee"])
    var = payout * (A["mgmt_fee"] + A["supplies_pct"]) + nights / A["stay_nights"] * d.clean
    return pd.DataFrame({"guest_rev": guest, "payout": payout, "var_cost": var, "noi": payout - var - d.fixed_str},
                        index=d.index)


def lease(d, A=A, rent_mult=1.0):
    """Unfurnished 12-month lease on the same unit (no furnishing in the capital cost)."""
    beds = d.bedrooms.fillna(1).clip(1, 2).astype(int)
    rent = beds.map(A["lease_rent"]) * rent_mult
    noi = rent * 12 * (1 - A["lease_vacancy"]) * (1 - A["lease_mgmt"]) - d.holding - A["lease_insurance"]
    return pd.DataFrame({"rent": rent, "noi": noi, "cost": d.allin - d.furnish}, index=d.index)


def hybrid(d, S, A=A, occ_mult=1.0, adr_mult=1.0, mid_rent_mult=1.0, mid_occ=None):
    """Nightly in the peak season, furnished 30+-night stays for the other A['mid_months'] months.
    S['peak_share'] = share of a year's nightly stays that fall in the peak season,
    S['peak_adr_uplift'] = peak-season price relative to the annual average."""
    nights = np.minimum(d.nights * occ_mult, 330) * S["peak_share"] * (1 - A["first_year_haircut"])
    payout = d.adr * adr_mult * S["peak_adr_uplift"] * nights * (1 - A["airbnb_fee"])
    var = payout * (A["mgmt_fee"] + A["supplies_pct"]) + nights / A["stay_nights"] * d.clean
    beds = d.bedrooms.fillna(1).clip(1, 2).astype(int)
    mo = A["mid_occupancy"] if mid_occ is None else mid_occ
    mid = beds.map(A["mid_rent"]) * mid_rent_mult * A["mid_months"] * mo
    mid_net = mid * (1 - A["mid_mgmt"]) - A["mid_turnovers"] * A["mid_turn_cost"]
    return pd.DataFrame({"str_payout": payout, "str_var": var, "mid_rev": mid, "mid_net": mid_net,
                         "noi": payout - var + mid_net - d.fixed_str}, index=d.index)


def vacancy_tax(d, A=A):
    """Annual Empty Homes Tax + Speculation and Vacancy Tax owed if the unit is let only by the night."""
    return (A["eht"] + A["svt"]) * d.purchase
