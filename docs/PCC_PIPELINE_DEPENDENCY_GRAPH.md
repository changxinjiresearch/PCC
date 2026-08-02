# PCC pipeline dependency graph

```text
locked patient/timepoint manifest
        |
        +--> raw current MRI + current mask --------------------+
        |                                                       |
        |                 leakage-free held-out predictor       |
        |                 [NOT EXECUTABLE LOCALLY]              +--> P0
        |                                                       |
        +--> raw future mask --> T = future & ~current ---------+----+
                                                                 |   |
P0 --------------------------------------------------------------+   |
 |                                                                   |
 +--> Fixed (unchanged)                                              |
 +--> Naive (target-free)                                            |
 +--> PCC: compare(P_r,T) --> correct logits --> P_(r+1) --repeat----+
 +--> EIA controls (same P0 and T) ----------------------------------+
                                                                     |
all maps + clean T --> case metrics --> paired tables --> statistics
```

The historical Formal EIA case-specific trainer instead connects T directly to predictor training and checkpoint selection. That edge is historically faithful but disqualifies its output as leakage-free P0 under the new contract.
