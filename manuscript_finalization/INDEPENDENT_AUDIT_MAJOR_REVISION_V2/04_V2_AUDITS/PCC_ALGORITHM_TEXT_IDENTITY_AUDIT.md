# PCC algorithm text identity audit

Canonical identity was checked against `src/models/pcc.py`, the locked method definitions and the Stage B embedded source. V2 defines D_r, S_r and O_r, provides the complete logit update, and states that O_r is explicitly suppressed. No statement says outside-support probability is preserved. No-smoothing changes only S_r=D_r.

ALGORITHM_DESCRIPTION_MISMATCHES = 0
