"""Clean Inside Airbnb Vancouver listings -> data/processed/comps.csv  (every filter is counted: outputs/tables/cleaning_funnel.csv)"""
import sys, pathlib; sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import pandas as pd, numpy as np, re
from config import *
l=pd.read_csv(RAW/"listings.csv.gz",low_memory=False)
f=[("raw listings",len(l))]
def step(name,mask):
    global l; l=l[mask].copy(); f.append((name,len(l)))
l["price_n"]=pd.to_numeric(l.price.astype(str).str.replace(r"[$,]","",regex=True),errors="coerce")
step("entire home/apt only (investable whole units)",l.room_type.eq("Entire home/apt"))
step("drop hotel-like / serviced / hostel property types",~l.property_type.str.contains("hotel|serviced|hostel|resort|bed and breakfast|boat|camper|tent",case=False,na=False))
step("minimum stay < 28 nights (true short-term)",l.minimum_nights<28)
step("has a valid nightly price",l.price_n.notna())
step("price $40-$2,000 per night (outlier trim)",l.price_n.between(40,2000))
def typ(p):
    p=str(p).lower()
    if "townhouse" in p: return "townhouse"
    if any(k in p for k in ["condo","rental unit","loft","apartment"]): return "condo"
    if p in ("entire home","entire cottage","entire villa","entire bungalow","entire cabin","tiny home"): return "house"
    return "other"   # guest suite / guesthouse: cannot be bought as a standalone asset
l["ptype"]=l.property_type.map(typ)
step("purchasable asset class (condo/townhouse/house; drop suites & guesthouses)",l.ptype.ne("other"))
lic=l.license.fillna("")
l["muni_lic"]=lic.str.contains(r"Municipal registration number:\s*[\d\- ]{6,}",regex=True)
l["prov_lic"]=lic.str.contains(r"Provincial registration number:\s*H\d+",regex=True)
l["exempt"]=lic.str.contains("Exempt",case=False)
l["licensed"]=l.muni_lic&l.prov_lic
l["zone"]=l.neighbourhood_cleansed.map(ZONE)
l["occ"]=l.estimated_occupancy_l365d
l["active"]=(l.number_of_reviews_ltm>=1)&(l.occ>0)
l["rev_calc"]=l.price_n*l.occ
keep=["id","neighbourhood_cleansed","zone","ptype","property_type","bedrooms","accommodates","price_n","occ","estimated_revenue_l365d","rev_calc",
      "number_of_reviews_ltm","reviews_per_month","review_scores_rating","availability_365","availability_30","availability_90","minimum_nights",
      "licensed","muni_lic","prov_lic","exempt","active","calculated_host_listings_count","host_is_superhost","latitude","longitude","first_review","last_review"]
l[keep].to_csv(PROC/"comps.csv",index=False)
pd.DataFrame(f,columns=["step","listings_remaining"]).to_csv(TAB/"cleaning_funnel.csv",index=False)
print(pd.DataFrame(f,columns=["step","n"]).to_string())
print("\nlicensed share (est.) of cleaned set:",l.licensed.mean().round(3),"| exempt:",l.exempt.mean().round(3),"| active:",l.active.mean().round(3))
print(l.ptype.value_counts()); print(l.groupby("ptype")[["price_n","occ","rev_calc"]].median())
