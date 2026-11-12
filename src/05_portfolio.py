import sys, pathlib; sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import pandas as pd, numpy as np, copy
from config import *; from econ import *
rng=np.random.default_rng(SEED)
base=pd.read_csv(PROC/"comps.csv"); base=base[base.active&base.licensed&~base.exempt]
c=add_econ(base)
CORE=["Downtown","West End","Downtown Eastside"]
pools={
 "A. Few high-value: detached houses (Kitsilano/Dunbar/Kerrisdale/Shaughnessy)": c[(c.ptype=="house")&c.neighbourhood_cleansed.isin(["Kitsilano","Dunbar Southlands","Kerrisdale","Shaughnessy"])],
 "B. Mid: all detached houses city-wide": c[c.ptype=="house"],
 "C. Many modest: all condos city-wide": c[c.ptype=="condo"],
 "D. Core condos: Downtown/West End/DTES (1-3BR)": c[(c.ptype=="condo")&c.neighbourhood_cleansed.isin(CORE)&(c.bedrooms.between(1,3))],
 "E. Core 1-2BR condos (RECOMMENDED)": c[(c.ptype=="condo")&c.neighbourhood_cleansed.isin(CORE)&(c.bedrooms.between(1,2))],
}
P_SUSP=69/3248   # Vancouver Apr-2026 licence suspensions / licences (brief, p.3)
def sim(pool,nsim=4000,occ_sd=0.08,adr_sd=0.05,susp=P_SUSP,susp_loss=0.5):
    out=[];ns=[]
    idx=np.arange(len(pool)); cost=pool.allin.values; noi_fixed=None
    A=ASSUME; var=(1-A["platform_fee"]-A["mgmt_fee"]-A["opex_pct"]); rev=pool.rev27.values
    fixed=(rev*var-pool.noi27.values)     # fixed costs per listing
    for _ in range(nsim):
        sel=[];spent=0
        while True:
            i=rng.choice(idx)
            if spent+cost[i]>BUDGET: break
            sel.append(i);spent+=cost[i]
        sel=np.array(sel); n=len(sel)
        shock=np.exp(rng.normal(0,occ_sd))*np.exp(rng.normal(0,adr_sd))          # market-wide shock
        r=rev[sel]*shock*np.where(rng.random(n)<susp,1-susp_loss,1.0)*np.exp(rng.normal(0,0.10,n))  # per-unit noise + licence suspensions
        noi=(r*var-fixed[sel]).sum(); out.append((noi,noi/spent)); ns.append(n)
    o=np.array(out); return o,np.array(ns)
rows=[]
for k,p in pools.items():
    o,ns=sim(p); y=o[:,1]
    rows.append(dict(strategy=k,pool_n=len(p),properties=int(np.median(ns)),noi_p10=np.percentile(o[:,0],10),noi_p50=np.percentile(o[:,0],50),noi_p90=np.percentile(o[:,0],90),
        yield_p10=np.percentile(y,10),yield_p50=np.percentile(y,50),yield_p90=np.percentile(y,90),prob_yield_below_1pct=(y<0.01).mean(),prob_noi_negative=(o[:,0]<0).mean()))
R=pd.DataFrame(rows); R.to_csv(TAB/"portfolio_strategies.csv",index=False)
pd.set_option("display.width",250); print(R.round(3).to_string())
# --- optimise unit mix within core: weights for 1BR vs 2BR; and add Mount Pleasant diversifier
core=pools["E. Core 1-2BR condos (RECOMMENDED)"]
mix=core.groupby(["neighbourhood_cleansed",core.bedrooms.clip(upper=2).astype(int)]).agg(n=("id","count"),yield_med=("yield27","median"),noi=("noi27","median"),cost=("allin","median")).round(3)
print(mix.to_string()); mix.to_csv(TAB/"recommended_mix_segments.csv")
# --- split-sample validation of segment ranking (guards against winner's curse)
seg=["neighbourhood_cleansed","ptype"]; hits=[];rc=[]
for s in range(300):
    m=rng.random(len(c))<0.5; A_=c[m].groupby(seg).yield27.agg(["median","count"]); B_=c[~m].groupby(seg).yield27.agg(["median","count"])
    j=A_.join(B_,lsuffix="A",rsuffix="B",how="inner"); j=j[(j.countA>=8)&(j.countB>=8)]
    rc.append(j.medianA.rank().corr(j.medianB.rank())); top=j.medianA.nlargest(3).index
    hits.append(j.loc[top,"medianB"].mean()-j.medianB.mean())
print("\nSplit-sample: mean rank corr between halves",round(np.mean(rc),3),"| top-3 (picked on half A) beat the all-segment average on half B in",round(np.mean(np.array(hits)>0),3),"of 300 splits; mean edge",round(np.mean(hits),4))
pd.DataFrame(dict(rank_corr=rc,top3_edge=hits)).to_csv(TAB/"split_sample_validation.csv",index=False)
# --- sensitivity of recommended portfolio yield (median-listing basis, ratio of sums)
def pyield(A=ASSUME,pm=1.0,occm=1.0):
    d=base[(base.ptype=="condo")&base.neighbourhood_cleansed.isin(CORE)&base.bedrooms.between(1,2)].copy(); d["occ"]=d.occ*occm
    d=add_econ(d,A,pm); return d.noi27.sum()/d.allin.sum()
b=pyield(); S=[("Base case",b,b)]
def mod(**kw): A=copy.deepcopy(ASSUME); A.update(kw); return A
S+= [("Purchase price -20% / +20%",pyield(pm=0.8),pyield(pm=1.2)),("Occupancy +20% / -20%",pyield(occm=1.2),pyield(occm=0.8)),
 ("Mgmt fee 15% / 25%",pyield(mod(mgmt_fee=0.15)),pyield(mod(mgmt_fee=0.25))),("ADR realisation 100% / 90%",pyield(mod(adr_realization=1.0)),pyield(mod(adr_realization=0.9))),
 ("Event haircut 0% / 15%",pyield(mod(event_haircut=0.0)),pyield(mod(event_haircut=0.15))),("Ramp-up penalty 0% / 20%",pyield(mod(new_listing_penalty=0.0)),pyield(mod(new_listing_penalty=0.2))),
 ("Strata fees -30% / +30%",pyield(mod(strata={'condo':3850,'townhouse':2100,'house':0})),pyield(mod(strata={'condo':7150,'townhouse':3900,'house':0})))]
T=pd.DataFrame(S,columns=["driver","upside_yield","downside_yield"]); T.to_csv(TAB/"sensitivity.csv",index=False); print(T.round(4).to_string())
