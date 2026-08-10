# Statistical implementation reporting audit

The locked code calls `scipy.stats.wilcoxon(d, zero_method='wilcox', alternative='two-sided')` without a `method` argument; SciPy therefore uses its version-specific default `method='auto'`. V2 does not call these values exact.

FALSE_EXACT_P_CLAIMS = 0
