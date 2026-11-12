"""(1) Short-term vs long-term-rental benchmark for core condos. (2) Regulatory scenarios incl. a Vancouver opt-out effective 1 Jun 2027.
LTR inputs (public): unfurnished 1BR asking rent Downtown $2,460 / West End $2,320 (liv.rent, Aug 2026 via Daily Hive) -> $2,400 used;
2BR rented-condo average $2,900 (CMHC 2025 Rental Market Report, Vancouver); rented-condo vacancy 1.5% (CMHC 2025)."""
import sys, pathlib; sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import pandas as pd, numpy as np
from config import *; from econ import *
rng=np.random.default_rng(SEED)
RENT={1:2400,2:2900}; VAC=0.015; PM=0.06
c=pd.read_csv(PROC/"comps_econ.csv")
core=c[(c.ptype=="condo")&c.neighbourhood_cleansed.isin(["Downtown","West End","Downtown Eastside"])&c.bedrooms.isin([1,2])].copy()
A=ASSUME
core["ltr_noi"]=[RENT[int(b)]*12*(1-VAC)*(1-PM)-A["strata"]["condo"]-p*A["prop_tax"]-p*A["maint"]["condo"]-800 for b,p in zip(core.bedrooms,core.purchase)]
core["ltr_cost"]=core.allin-A["furnish"]["condo"]       # no furnishing for an unfurnished rental
core["ltr_yield"]=core.ltr_noi/core.ltr_cost
g=core.groupby("bedrooms").apply(lambda d:pd.Series(dict(n=len(d),str_yield=d.noi27.sum()/d.allin.sum(),ltr_yield=d.ltr_noi.sum()/d.ltr_cost.sum(),
   str_noi=d.noi27.mean(),ltr_noi=d.ltr_noi.mean(),str_p10_yield=d.yield27.quantile(.1),share_str_beats_ltr=(d.noi27/d.allin>d.ltr_noi/d.ltr_cost).mean())))
print(g.round(4).to_string()); g.to_csv(TAB/"str_vs_ltr.csv")
# portfolio candidates (fill $10M by sampling comps)
def sim(pool,nsim=4000,rev_mult=1.0,susp=69/3248,fallback=False):
    idx=np.arange(len(pool)); cost=pool.allin.values; rev=pool.rev27.values; var=1-A["platform_fee"]-A["mgmt_fee"]-A["opex_pct"]
    fixed=rev*var-pool.noi27.values; ltr=pool.ltr_noi.values; out=[];ns=[]
    for _ in range(nsim):
        sel=[];sp=0
        while True:
            i=rng.choice(idx)
            if sp+cost[i]>BUDGET: break
            sel.append(i);sp+=cost[i]
        sel=np.array(sel);n=len(sel)
        sh=np.exp(rng.normal(0,.08))*np.exp(rng.normal(0,.05))
        sus=rng.random(n)<susp
        r=rev[sel]*sh*rev_mult*np.exp(rng.normal(0,.10,n))
        noi=r*var-fixed[sel]
        noi=np.where(sus,(0.5*noi+0.5*ltr[sel]) if fallback else (noi*0.5),noi)     # suspended half-year: lost, or re-let long-term
        out.append((noi.sum(),noi.sum()/sp));ns.append(n)
    o=np.array(out);return o,np.array(ns)
pools={"1BR core condos":core[core.bedrooms==1],"1-2BR core condos (previous rec.)":core}
rows=[]
for k,p in pools.items():
    for sc,kw in {"Base":{}, "Opt-out 1 Jun 2027: supply erodes revenue 10% for 7 months":dict(rev_mult=1-0.10*7/12),"Opt-out, 20% erosion":dict(rev_mult=1-0.20*7/12),"Base + long-term fallback on suspension":dict(fallback=True)}.items():
        o,ns=sim(p,**kw);y=o[:,1]
        rows.append(dict(pool=k,scenario=sc,units=int(np.median(ns)),noi_p10=np.percentile(o[:,0],10),noi_p50=np.percentile(o[:,0],50),noi_p90=np.percentile(o[:,0],90),yield_p10=np.percentile(y,10),yield_p50=np.percentile(y,50),yield_p90=np.percentile(y,90),p_below_1pct=(y<0.01).mean()))
R=pd.DataFrame(rows);R.to_csv(TAB/"scenarios.csv",index=False);pd.set_option("display.width",250);print(R.round(3).to_string())
# all-long-term floor for 1BR portfolio
p=pools["1BR core condos"]; n=int(BUDGET//p.ltr_cost.median()); print("LTR floor 1BR: units",n,"yield",round(p.ltr_noi.sum()/p.ltr_cost.sum(),4),"NOI",round(n*p.ltr_noi.mean()))
# vacancy opt-out test timeline (CMHC Vancouver purpose-built vacancy): 2024 2.1%, 2025 3.7%
