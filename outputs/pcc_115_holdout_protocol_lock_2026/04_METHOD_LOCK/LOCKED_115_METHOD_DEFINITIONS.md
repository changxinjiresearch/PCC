# Complete locked method definitions

Let `P0` be the frozen Stage A probability map and `T = (future_mask > 0.5) AND NOT (current_mask > 0.5)`. All arrays are aligned and no registration/resampling is allowed. `safe_clip_prob` converts to float32, maps NaN/−Inf/+Inf to 0/0/1 and clips to [0,1].

Fixed is `safe_clip_prob(P0)`. Naive is `sigmoid(2.5 × logit(Fixed))` with probability clipping to `[1e-5,1−1e-5]`, logit clipping to `[-30,30]`, then float32 clipping.

For EIA, `R = distance_transform_edt(~T) <= 26`; `S = normalize01(gaussian_filter(T.float32, sigma=2.0))` with SciPy default boundary mode. Linear is `clip(P0 + 0.30 S(1−P0) − 0.30(1−R)P0)`. Blends are `clip(0.90P0+0.10S)` and `clip(0.75P0+0.25S)`. Morph thresholds P0 at 0.5, intersects with R, performs one SciPy binary closing, fills holes, labels with SciPy default connectivity and retains components of at least 20 voxels.

Full PCC initializes `P_0=safe_clip_prob(P0)`. At round r: `P_r` is clipped; `D_r=(T−P_r)R`; `S_r=gaussian_filter(D_r,sigma=2.0)`; `O_r=P_r(1−R)`; `L_r=logit(P_r,eps=1e-5)`; `P_{r+1}=clip(sigmoid(clip(L_r+0.30S_r−0.30O_r,−30,30)))`. Ten rounds propagate state. Float32 conversion/clipping occurs at every round. SciPy Gaussian defaults define boundary handling. When trajectory capture is enabled P1–P10 and locked round summaries are saved; otherwise only P10 is returned.

No-smoothing executes the same loop, region, target, state, suppression, eta, rounds, clipping, logit/sigmoid order, dtype and boundary policy. Its sole difference is `S_r=D_r`; the `gaussian_filter(D_r,sigma=2.0)` call is bypassed. The authoritative implementation is `run_variant(..., smoothing=False)` in `src/analysis/internal_completion.py`; Full-PCC identity is `smoothing=True`. No-smoothing remains a posthoc 40-case finding prelocked here as an independent-validation candidate, not the canonical primary.
