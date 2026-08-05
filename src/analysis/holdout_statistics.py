"""Prelocked patient-level statistics for the 115-patient holdout."""
from __future__ import annotations
import hashlib
import numpy as np
from scipy.stats import rankdata, wilcoxon

BOOTSTRAP_REPLICATES=10_000
BOOTSTRAP_SEED=20260803

def paired_summary(differences: np.ndarray) -> dict[str, float | int | str]:
    d=np.asarray(differences,dtype=float)
    if d.ndim!=1 or len(d)==0 or not np.isfinite(d).all(): raise ValueError("finite nonempty patient-level vector required")
    nonzero=d[d!=0]
    if len(nonzero)==0: p=1.0; status="ALL_ZERO"; rb=0.0
    else:
        p=float(wilcoxon(d,zero_method="wilcox",alternative="two-sided").pvalue); status="AVAILABLE"
        ranks=rankdata(np.abs(nonzero),method="average"); pos=float(ranks[nonzero>0].sum()); neg=float(ranks[nonzero<0].sum()); rb=(pos-neg)/(pos+neg)
    sd=float(d.std(ddof=1)) if len(d)>1 else float("nan")
    dz=float(d.mean()/sd) if np.isfinite(sd) and sd>0 else float("nan")
    rng=np.random.default_rng(BOOTSTRAP_SEED); means=np.empty(BOOTSTRAP_REPLICATES)
    for i in range(BOOTSTRAP_REPLICATES): means[i]=rng.choice(d,size=len(d),replace=True).mean()
    low,high=np.quantile(means,[0.025,0.975])
    return {"n":len(d),"mean_difference":float(d.mean()),"median_difference":float(np.median(d)),"wilcoxon_p_two_sided":p,"wilcoxon_status":status,"rank_biserial":float(rb),"cohens_dz":dz,"cohens_dz_status":"AVAILABLE" if np.isfinite(dz) else "SD_ZERO","bootstrap_low":float(low),"bootstrap_high":float(high),"wins":int((d>0).sum()),"ties":int((d==0).sum()),"losses":int((d<0).sum())}

def holm_two(p_values: tuple[float,float]) -> tuple[float,float]:
    p=np.asarray(p_values,dtype=float)
    if p.shape!=(2,) or not np.isfinite(p).all() or np.any((p<0)|(p>1)): raise ValueError("exactly two valid p-values required")
    order=np.argsort(p,kind="stable"); adjusted=np.empty(2); adjusted[order[0]]=min(1.0,2*p[order[0]]); adjusted[order[1]]=max(adjusted[order[0]],p[order[1]])
    return float(adjusted[0]),float(adjusted[1])
