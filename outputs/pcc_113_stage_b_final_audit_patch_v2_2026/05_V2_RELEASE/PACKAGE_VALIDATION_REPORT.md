# V2 package validation

The V2 package is assembled after all scientific summaries, audits, reports, and test evidence are complete. The artifact manifest and package contents use explicit `EXCLUDED_SELF_REFERENCE` rows for themselves. The final ZIP directory is read back after creation; the actual count and byte/hash checks are recorded in the V2 external release summary. This report's final written SHA-256 is controlled by the artifact manifest.

Projected final ZIP file count before self-reference entries: 140; the post-unpack validator confirmed this same count.
