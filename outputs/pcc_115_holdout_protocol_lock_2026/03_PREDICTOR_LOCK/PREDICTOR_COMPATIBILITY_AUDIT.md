# Predictor compatibility audit

The CPU-only preflight found all five expected frozen checkpoint files and verified their SHA-256 values. Predictor architecture and current-only preprocessing are locked to the repository code hashes recorded in `PREDICTOR_CODE_HASHES.csv`. No checkpoint was loaded into a model and no real-case forward was executed.
