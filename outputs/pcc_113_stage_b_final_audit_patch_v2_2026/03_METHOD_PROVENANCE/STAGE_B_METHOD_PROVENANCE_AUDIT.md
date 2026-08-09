# Method provenance audit

The mapping follows the actual Stage B runner imports and calls. Effective provenance is SHA-256 over sorted `relative_path\tSHA256` entries for the method sources plus the canonical manifest hash of all four executed shard wrappers. The generic V1 `locked_method_sources` label is retained only in V1.
