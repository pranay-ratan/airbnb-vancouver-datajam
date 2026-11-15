"""Loading and tagging of Inside Airbnb listings. Used by every numbered script."""
import json
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from config import RAW, TAB, ZONE, CORE

APT_TYPES = {"Entire rental unit", "Entire condo", "Entire loft"}
HOUSE_TYPES = {"Entire home", "Entire villa", "Entire bungalow", "Entire cottage", "Entire vacation home", "Entire place"}
SUITE_TYPES = {"Entire guest suite", "Entire guesthouse"}
HOTEL_LIKE = r"hotel|serviced|hostel|resort|bed and breakfast|boat|camper|tent|tower|cave|hut|earthen"


def money(s):
    """Prices are stored as text ('$1,234.00')."""
    return pd.to_numeric(s.astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce")


def has_snapshot(snap, name="listings"):
    return (RAW / snap / f"{name}.csv.gz").exists()


def load_listings(snap):
    """One row per listing with the tags the analysis needs. Licence numbers are reduced to yes/no flags
    and never written out (brief: never show real licence numbers, host names or listing URLs)."""
    l = pd.read_csv(RAW / snap / "listings.csv.gz", low_memory=False)
    l["price_n"] = money(l.price)
    l["scraped"] = pd.to_datetime(l.last_scraped, format="%Y-%m-%d")
    l["entire"] = l.room_type.eq("Entire home/apt")
    l["stay"] = np.select([l.minimum_nights >= 90, l.minimum_nights >= 28], ["90+ nights", "28-89 nights"], "nightly")
    pt = l.property_type.fillna("")
    l["hotel_like"] = pt.str.contains(HOTEL_LIKE, case=False)
    # asset class a fund could actually buy. 'Entire home' with 0-2 bedrooms cannot be told apart from a suite,
    # so only 3+ bedroom homes count as detached houses.
    l["asset"] = np.select(
        [pt.isin(APT_TYPES), pt.eq("Entire townhouse"), pt.isin(HOUSE_TYPES) & (l.bedrooms >= 3),
         pt.isin(HOUSE_TYPES), pt.isin(SUITE_TYPES)],
        ["condo", "townhouse", "house", "small_home", "suite"], "other")
    lic = l.license.fillna("")
    muni = lic.str.extract(r"Municipal registration number:\s*([^<]*)")[0].fillna("").str.strip()
    prov = lic.str.extract(r"Provincial registration number:\s*([^<]*)")[0].fillna("").str.strip()
    l["muni_ok"] = muni.str.contains(r"\d{2}\s?[-–]\s?\d{5,6}|^\d{6,8}$")       # e.g. 26-123456
    l["muni_year"] = muni.str.extract(r"(\d{2})\s?[-–]")[0]
    l["prov_ok"] = prov.str.match(r"^(H|PM)\d{6,}")                                  # host or property-manager registration
    l["lic_exempt"] = muni.str.contains("exempt", case=False) | prov.str.contains("exempt", case=False)
    l["lic_any"] = lic.ne("")
    l["licensed"] = l.muni_ok & l.prov_ok
    l["first_review_d"] = pd.to_datetime(l.first_review, format="%Y-%m-%d", errors="coerce")
    l["age_m"] = (l.scraped - l.first_review_d).dt.days / 30.44
    l["occ"] = l.estimated_occupancy_l365d
    l["zone"] = l.neighbourhood_cleansed.map(ZONE)
    l["core"] = l.neighbourhood_cleansed.isin(CORE)
    if "price_quote_checkin_date" in l.columns:
        l["q_in"] = pd.to_datetime(l.price_quote_checkin_date, format="%Y-%m-%d", errors="coerce")
        l["q_nights"] = (pd.to_datetime(l.price_quote_checkout_date, format="%Y-%m-%d", errors="coerce") - l.q_in).dt.days
    else:
        l["q_in"], l["q_nights"] = pd.NaT, np.nan
    return l.copy()


def nightly_priced(l):
    """Entire homes on the nightly market with a usable price."""
    return l[l.entire & ~l.hotel_like & l.stay.eq("nightly") & l.price_n.between(40, 2000)]


def save_json(obj, name):
    def clean(o):
        if isinstance(o, dict):
            return {str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating, float)):
            return None if (o != o) else round(float(o), 6)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        return o
    (TAB / name).write_text(json.dumps(clean(obj), indent=1))


def load_json(name):
    return json.loads((TAB / name).read_text())
