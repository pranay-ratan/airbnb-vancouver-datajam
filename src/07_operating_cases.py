"""Operating-standard cases for the recommended 14x 1BR core condo portfolio + long-term-rent stress. Writes outputs/tables/operating_cases.csv"""
import sys, pathlib; sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import pandas as pd, numpy as np
from config import *; from econ import *
exec(open(pathlib.Path(__file__).resolve().parent/"06_ltr_and_scenarios.py").read().split("# portfolio candidates")[0].split('rng=np.random')[0]) if False else None
rng=np.random.default_rng(SEED); A=ASSUME
c=pd.read_csv(PROC/"comps_econ.csv")
k=c[(c.ptype=="condo")&c.neighbourhood_cleansed.isin(["Downtown","West End","Downtown Eastside"])&(c.bedrooms==1)].copy()
k["ltr_noi"]=2400*12*0.985*0.94-A["strata"]["condo"]-k.purchase*(A["prop_tax"]+A["maint"]["condo"])-800; k["ltr_cost"]=k.allin-A["furnish"]["condo"]
def sim(pool,n=4000):
    idx=np.arange(len(pool));cost=pool.allin.values;rev=pool.rev27.values;var=1-A["platform_fee"]-A["mgmt_fee"]-A["opex_pct"];fixed=rev*var-pool.noi27.values;o=[];ns=[]
    for _ in range(n):
        s=[];sp=0
        while True:
            i=rng.choice(idx)
            if sp+cost[i]>BUDGET:break
            s.append(i);sp+=cost[i]
        s=np.array(s);sh=np.exp(rng.normal(0,.08))*np.exp(rng.normal(0,.05));r=rev[s]*sh*np.exp(rng.normal(0,.10,len(s)))
        noi=r*var-fixed[s];noi=np.where(rng.random(len(s))<69/3248,noi*0.5,noi);o.append((noi.sum(),noi.sum()/sp));ns.append(len(s))
    o=np.array(o);return o,int(np.median(ns))
cases={"Market-median operator (all active licensed 1BR comps)":k,"Superhost-standard operator":k[k.host_is_superhost=="t"],"Non-Superhost operator":k[k.host_is_superhost!="t"],
       "1-night minimum stay only":k[k.minimum_nights<=1],"Superhost + 1-night minimum":k[(k.host_is_superhost=="t")&(k.minimum_nights<=1)]}
rows=[]
for nme,p in cases.items():
    o,u=sim(p);y=o[:,1];rows.append(dict(case=nme,comps=len(p),units=u,noi_p10=np.percentile(o[:,0],10),noi_p50=np.percentile(o[:,0],50),noi_p90=np.percentile(o[:,0],90),yield_p10=np.percentile(y,10),yield_p50=np.percentile(y,50),yield_p90=np.percentile(y,90)))
R=pd.DataFrame(rows);R.to_csv(TAB/"operating_cases.csv",index=False);pd.set_option("display.width",250);print(R.round(3).to_string())
# long-term rent stress (rents fell 7-14% y/y in Downtown/West End per liv.rent)
for d in (0,-0.10,-0.15):
    r=2400*(1+d);noi=r*12*0.985*0.94-A["strata"]["condo"]-k.purchase*(A["prop_tax"]+A["maint"]["condo"])-800;print("LTR rent",round(r),"yield",round(noi.sum()/k.ltr_cost.sum(),4),"NOI/unit",round(noi.mean()))

# ---- sensitivity of the recommended 1BR portfolio (ratio-of-sums yield) ----
import copy
base=pd.read_csv(PROC/"comps.csv"); base=base[base.active&base.licensed&~base.exempt]
b1=base[(base.ptype=="condo")&base.neighbourhood_cleansed.isin(["Downtown","West End","Downtown Eastside"])&(base.bedrooms==1)]
def py(Am=ASSUME,pm=1.0,om=1.0):
    d=b1.copy();d["occ"]=d.occ*om;d=add_econ(d,Am,pm);return d.noi27.sum()/d.allin.sum()
def mod(**kw):
    a=copy.deepcopy(ASSUME);a.update(kw);return a
S=[("Base",py(),py()),("Occupancy -20% / +20%",py(om=.8),py(om=1.2)),("Purchase price +20% / -20%",py(pm=1.2),py(pm=.8)),("Event haircut 15% / 0%",py(mod(event_haircut=.15)),py(mod(event_haircut=0))),
   ("Ramp-up 20% / 0%",py(mod(new_listing_penalty=.2)),py(mod(new_listing_penalty=0))),("Mgmt fee 25% / 15%",py(mod(mgmt_fee=.25)),py(mod(mgmt_fee=.15))),("ADR realisation 90% / 100%",py(mod(adr_realization=.9)),py(mod(adr_realization=1.0)))]
T=pd.DataFrame(S,columns=["driver","downside_yield","upside_yield"]);T.to_csv(TAB/"sensitivity_1br.csv",index=False);print(T.round(4).to_string())
