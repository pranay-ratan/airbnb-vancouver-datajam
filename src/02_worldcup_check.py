"""Does the trailing-12-month window contain a one-off demand spike (FIFA World Cup, Vancouver matches Jun 13-Jul 7 2026)?
Uses review dates of cleaned comps as a stay proxy. Output: outputs/tables/monthly_reviews.csv"""
import sys, pathlib; sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import pandas as pd
from config import *
c=pd.read_csv(PROC/"comps.csv",usecols=["id","active"]); ids=set(c.id[c.active])
r=pd.read_csv(RAW.parent.parent/"raw/insideairbnb/reviews.csv.gz",usecols=["listing_id","date"],parse_dates=["date"])
r=r[r.listing_id.isin(ids)]
m=r.groupby(r.date.dt.to_period("M")).size().rename("reviews").to_frame()
m=m.loc["2023-01":"2026-09"]; m["listings"]=len(ids)
m.to_csv(TAB/"monthly_reviews.csv"); 
m["yoy"]=m.reviews/m.reviews.shift(12)-1
print(m.loc["2025-06":"2026-09"].round(3).to_string())
