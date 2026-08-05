# No-smoothing single-difference audit

Authoritative function: `src.analysis.internal_completion.run_variant`. The only branch controlled by `smoothing` is:

```python
signal = gaussian_filter(discrepancy, sigma=SIGMA) if smoothing else discrepancy
```

Full PCC uses the default `smoothing=True`; No-smoothing passes exactly `smoothing=False`. AST/static tests assert one `smoothing` conditional and identical values for rounds, eta, radius, suppression, region, safe logit, sigmoid, clipping, propagation and dtype. A synthetic regression also verifies the Full branch equals `src.models.pcc.apply_pcc` and that only the discrepancy signal differs.
