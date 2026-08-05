# Future-access guard

Stage A accepts only current T1c, current mask, current-only p1/p99 normalization, and locked checkpoint inputs. Manifest columns and runner signatures containing `future`, `target`, or `later` are rejected. The future mask is reserved for Stage B and is not present in the P0 manifest. These guards are static/synthetic only; no model forward is run here.
