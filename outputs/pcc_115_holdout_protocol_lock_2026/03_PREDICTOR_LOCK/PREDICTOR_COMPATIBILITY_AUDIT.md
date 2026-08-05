# Predictor compatibility audit

The CPU-only supplement v2 rehashed all five checkpoint files, loaded each state dict on CPU and strictly loaded it into `CrossCaseSmallUNet(in_channels=2, out_channels=1, base=16)`. Every fold has 106 checkpoint keys and 106 model keys, missing keys 0, unexpected keys 0 and parameter-shape mismatch 0. Fold identity is also present in each source path.

No model forward was called, no patient tensor was created and no P0 was generated. These checkpoint hashes are first formally locked by this 115-patient protocol supplement; this report does not claim that the historical 40-case ZIP independently loaded or verified these checkpoint state dicts.
