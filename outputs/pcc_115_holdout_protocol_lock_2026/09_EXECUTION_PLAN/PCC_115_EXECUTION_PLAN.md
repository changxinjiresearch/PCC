# Execution plan

GPU Stage A (future-blind, not authorized in this package): load the five locked checkpoints once, create only P0, atomically save and hash each map, then close the accelerator. CPU Stage B (not authorized in this package): read frozen P0 and future masks, run the eight locked methods and four deterministic patient shards. This package submits neither job and contains no P0 or result.
