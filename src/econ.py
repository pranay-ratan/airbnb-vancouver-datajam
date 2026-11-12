"""Shared economics: purchase cost, 2027 NOI per listing. All assumptions live in ASSUME (documented in docs/assumptions.md)."""
import numpy as np, pandas as pd
from config import BENCH
ASSUME=dict(event_haircut=0.05,   # LTM contains FIFA World Cup 2026 (tested in 02_worldcup_check.py: modest)
            adr_realization=0.95, # asking price -> realised average daily rate
            new_listing_penalty=0.10, # first-year ramp-up (no reviews/ranking)
            platform_fee=0.03, mgmt_fee=0.20, opex_pct=0.10,
            insurance=2500, biz_licence=1000,
            strata={'condo':5500,'townhouse':3000,'house':0},
            prop_tax=0.0030, maint={'condo':0.003,'townhouse':0.005,'house':0.008},
            furnish={'condo':20000,'townhouse':30000,'house':40000}, legal_pct=0.005)
def bed_factor(t,b):
    b=0 if pd.isna(b) else b
    if t=='condo': return 0.85 if b<=1 else 1.15 if b==2 else 1.5
    if t=='townhouse': return 0.8 if b<=1 else 0.9 if b==2 else 1.0 if b==3 else 1.2
    return 0.8 if b<=2 else 0.95 if b==3 else 1.05 if b==4 else 1.3
def ptt(p):  # BC Property Transfer Tax (residential)
    t=0.01*min(p,200_000)+0.02*max(0,min(p,2_000_000)-200_000)+0.03*max(0,p-2_000_000)+0.02*max(0,p-3_000_000)
    return t
def add_econ(d,A=ASSUME,price_mult=1.0):
    d=d.copy()
    d["purchase"]=[BENCH[(z,t)]*bed_factor(t,b)*price_mult for z,t,b in zip(d.zone,d.ptype,d.bedrooms)]
    d["allin"]=d.purchase+d.purchase.map(ptt)+d.purchase*A["legal_pct"]+d.ptype.map(A["furnish"])
    d["rev27"]=d.price_n*A["adr_realization"]*d.occ*(1-A["event_haircut"])*(1-A["new_listing_penalty"])
    fixed=A["insurance"]+A["biz_licence"]+d.ptype.map(A["strata"])+d.purchase*A["prop_tax"]+d.purchase*d.ptype.map(A["maint"])
    d["noi27"]=d.rev27*(1-A["platform_fee"]-A["mgmt_fee"]-A["opex_pct"])-fixed
    d["yield27"]=d.noi27/d.allin
    return d
