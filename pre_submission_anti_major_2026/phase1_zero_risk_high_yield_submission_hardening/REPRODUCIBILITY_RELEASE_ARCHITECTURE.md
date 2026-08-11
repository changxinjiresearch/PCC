# Reproducibility release architecture

The local staging tree separates code, locked configs, environment evidence, fold references, inference, PCC, evaluation, figure generation, derived-metric references, protocol locks, figure-source references, hashes, documentation and data-access information. Original authorities were never moved or modified. Small releasable files are byte-identical copies; identifier-bearing case/fold tables and raw/source arrays are hash references only.

Classification is explicit: `CURRENT_AUTHORITY`, `SUPPORTIVE`, `HISTORICAL_SUPERSEDED`, or `NOT_FOR_RELEASE`. Distribution status is independently recorded. This is local staging only; no GitHub, Zenodo or other public upload occurred.
