import sys, pathlib; sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import pandas as pd, numpy as np
from config import *
c=pd.read_csv(PROC/"comps_econ.csv")
# V1: our revenue arithmetic vs Inside Airbnb's own estimate
v=c.dropna(subset=["estimated_revenue_l365d"]); 
print("V1 corr(price*occ, IA est revenue)=",round(v.rev_calc.corr(v.estimated_revenue_l365d),4),"| median ratio",round((v.rev_calc/v.estimated_revenue_l365d.replace(0,np.nan)).median(),3))
# V2: estimated occupancy vs reviews (IA's estimate is review-driven; check it is not saturated by the 255 cap)
print("V2 share at occupancy cap(>=255):",round((c.occ>=255).mean(),4),"| corr(occ, reviews_ltm)=",round(c.occ.corr(c.number_of_reviews_ltm),3))
# V3: forward calendar (Sep-26..Sep-27): booked-or-blocked share must be >= estimated booked share
cal=pd.read_csv(RAW/"calendar.csv.gz",usecols=["listing_id","date","available"],parse_dates=["date"])
cal=cal[cal.listing_id.isin(set(c.id))]; cal["unavail"]=(cal.available=="f")
f=cal.groupby("listing_id").unavail.mean().rename("fwd_unavail")
m=c.set_index("id").join(f).dropna(subset=["fwd_unavail"]); m["est_occ_share"]=m.occ/365
print("V3 median est. occupancy share",round(m.est_occ_share.median(),3),"| median forward unavailable share",round(m.fwd_unavail.median(),3),
      "| listings where est occ > forward unavailable:",round((m.est_occ_share>m.fwd_unavail+0.02).mean(),3))
q=cal[cal.date.dt.year==2027]; print("2027-only (Jan-Sep) unavailable share by month:"); print(q.groupby(q.date.dt.month).unavail.mean().round(3).to_string())
# V4: bedroom view for top condo neighbourhoods
t=c[(c.ptype=="condo")&c.neighbourhood_cleansed.isin(["Downtown","West End","Downtown Eastside"])].copy()
t["bed"]=t.bedrooms.clip(upper=3).fillna(1).astype(int)
print(t.groupby(["neighbourhood_cleansed","bed"]).agg(n=("id","count"),adr=("price_n","median"),occ=("occ","median"),noi=("noi27","median"),cost=("allin","median"),y=("yield27","median")).round(3).to_string())
