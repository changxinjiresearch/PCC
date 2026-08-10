# Locked comparator method definitions

- **Fixed:** `safe_clip_prob(P0)`; no target access and no iteration.
- **Naive:** `sigmoid(2.5 × logit(safe_clip_prob(P0)))`, with logit probability clipping at `1e-5`, logit clipping to `[-30,30]`, and float32 output; no target access and one transformation.
- **EIA-linear:** with `R = distance_transform_edt(~T) <= 26` and `G = normalize01(gaussian_filter(T.float32, sigma=2.0))`, output `clip(P0 + 0.30G(1-P0) - 0.30(1-R)P0)`; one target-accessed transformation.
- **EIA-blend-0.90:** `clip(0.90P0 + 0.10G)`.
- **EIA-blend-0.75:** `clip(0.75P0 + 0.25G)`.
- **EIA-morph (internal only):** threshold P0 at 0.5, intersect with R, one binary closing, hole filling, default SciPy component labelling, and retention of components of at least 20 voxels; binary float32 output.
- **Full PCC:** ten state-propagating logit-space updates with `D_r=(T-P_r)R`, `S_r=GaussianSmooth(D_r,2.0)`, `O_r=P_r(1-R)`, and `logit(P_{r+1})=logit(P_r)+0.30S_r-0.30O_r`; P10 is formal.
- **No-smoothing PCC:** identical to Full PCC except `S_r=D_r`. Outside-support suppression remains unchanged.

EIA methods are oracle-style retrospective controls. Their descriptive results contextualize target access; no new pairwise inferential comparison was run.
