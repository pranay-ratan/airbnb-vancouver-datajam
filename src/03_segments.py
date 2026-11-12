import sys, pathlib; sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import pandas as pd, numpy as np
from config import *; from econ import *
c=pd.read_csv(PROC/"comps.csv")
print("licensed vs not (cleaned comps):"); print(c.groupby("licensed")[["price_n","occ","rev_calc","number_of_reviews_ltm"]].median().round(1), c.licensed.value_counts().to_dict())
c=c[c.active&c.licensed&~c.exempt]   # comps = active, fully licensed (what DDD could legally run)
c=add_econ(c); c.to_csv(PROC/"comps_econ.csv",index=False)
print(len(c),"final comps")
rng=np.random.default_rng(SEED)
def seg(g):
    y=g.yield27.values; boots=[np.mean(rng.choice(y,len(y))) for _ in range(500)]
    return pd.Series(dict(n=len(g),adr=g.price_n.median(),occ=g.occ.median(),rev27=g.rev27.median(),noi27=g.noi27.median(),cost=g.allin.median(),
        yield_med=g.yield27.median(),yield_mean=g.yield27.mean(),yield_lo=np.percentile(boots,5),yield_hi=np.percentile(boots,95),share_neg=(g.yield27<0).mean()))
s=c.groupby(["neighbourhood_cleansed","ptype"]).apply(seg).reset_index()
s=s[s.n>=15].sort_values("yield_med",ascending=False); s.to_csv(TAB/"segment_yields.csv",index=False)
pd.set_option("display.width",220); print(s.round(3).head(20).to_string()); print(s.round(3).tail(8).to_string())
t=c.groupby("ptype").apply(seg); t.to_csv(TAB/"ptype_yields.csv"); print(t.round(3).to_string())
