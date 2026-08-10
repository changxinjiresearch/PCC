# Kaggle current-only dataset transport audit

Dataset version 1 was retained as a pre-forward engineering failure: Kaggle automatically expanded `.nii.gz` files, so mounted bytes no longer represented the locked compressed-file hashes. No kernel was submitted against version 1 and no P0 was generated from it.

Version 2 stores the same locked NIfTI bytes with an opaque `.bin` transport suffix. The kernel copies each current-only file byte-for-byte to a temporary `.nii.gz` path, verifies SHA-256 again, and only then opens it. Version 2 contains 39 current T1ce and 39 current segmentation files, with no preoperative or recurrence files. A fixed remote re-download matched the locked source SHA-256. Version 2 is authoritative.
