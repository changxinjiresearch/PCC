# Checkpoint model compatibility

All five checkpoint files were rehashed and loaded on CPU. Each state dict was strictly loaded into the frozen `CrossCaseSmallUNet(2,1,16)` architecture. No model forward was called and no P0 was generated. These hashes are first formally locked by this 115-patient protocol supplement; the audit does not claim historical ZIP checkpoint verification.

- fold_1: hash PASS; CPU load PASS; missing 0; unexpected 0; shape mismatch 0; strict load PASS.
- fold_2: hash PASS; CPU load PASS; missing 0; unexpected 0; shape mismatch 0; strict load PASS.
- fold_3: hash PASS; CPU load PASS; missing 0; unexpected 0; shape mismatch 0; strict load PASS.
- fold_4: hash PASS; CPU load PASS; missing 0; unexpected 0; shape mismatch 0; strict load PASS.
- fold_5: hash PASS; CPU load PASS; missing 0; unexpected 0; shape mismatch 0; strict load PASS.
