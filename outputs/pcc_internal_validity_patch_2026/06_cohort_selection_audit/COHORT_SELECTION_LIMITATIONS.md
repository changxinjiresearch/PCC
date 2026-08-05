# Cohort Selection Limitations

- Historical counts before the 2026 leakage-free discovery implementation are `UNKNOWN / NOT RECOVERABLE`.
- Shape, affine, orientation, and non-empty-mask counts were exhaustively verified for the 40 locked pairs, but not for all 391 descriptive candidate pairs; full-candidate compatibility counts are therefore `UNKNOWN`.
- The implementation used a hard limit of 40 eligible patients. It did not document a scientific sample-size derivation for choosing 40.
- The implementation's docstring says “consecutive,” while the code selects the first two usable timepoints without requiring consecutive numeric indices. The code is the executed authority.
- Patients after the first 40 eligible lexical IDs were not excluded for imaging quality or outcome; they were excluded because the fixed limit had been reached.
