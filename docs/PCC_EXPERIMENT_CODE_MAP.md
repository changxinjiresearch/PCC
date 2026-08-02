# PCC experiment code map

| Experiment | Scientific question | Repository entry/evidence | Dependency and status |
|---|---|---|---|
| Formal Layer2R historical EIA | Does target-conditioned iterative correction differ from controls? | `experiments/run_formal_layer2r.py`; `src/pipelines/formal_layer2r.py`; notebook 109–110 | Historical pipeline READY on Kaggle, but P0 is target-trained and therefore incompatible with the new leakage-free definition. |
| Fixed | Performance of supplied starting map | `run_case` / `eval_prob_map` | READY once a scientifically admissible P0 exists. |
| Naive | Target-free self-tightening control | `src/models/naive_self_tightening.py` | READY. |
| PCC | Multi-round target-conditioned map refinement | `src/models/pcc.py::apply_pcc` | READY; final state only, trajectory persistence missing. |
| EIA | Equal target information with alternate update | `src/models/eia.py::apply_eia` | READY. |
| One-round / mechanism ablation | Marginal role of rounds/mechanisms | Notebook/report evidence; no registered migrated entry | PARTIALLY_MIGRATED. Parameters can be varied, but named, locked ablation runner/output contract is absent. |
| Independent five-fold direct prediction | Leakage-free held-out P0 | notebook cells 14–19 and later Model A cells | PARTIALLY_MIGRATED; data/folds/checkpoints absent. |
| Cross-case P0 robustness | Does PCC work from held-out P0? | notebook experiments and B2 report | HARD_DATA_BLOCKER / artifacts absent. |
| Target robustness | Dependence on target construction | report and notebook history | NOT_FOUND as a complete migrated runner. |
| Imperfect guidance | Robustness to degraded target guidance | dedicated report | NOT_FOUND as a complete migrated runner; source artifacts absent. |
| Layer 1 | Static current-lesion segmentation | notebook historical cells | PARTIALLY_MIGRATED; checkpoints/data absent. |
| Layer 3 occlusion/localization | Pathology-reliance audit | notebook cells 81–84 | PARTIALLY_MIGRATED; Layer 1 checkpoints/data absent. |
| LUMIERE | External retrospective feasibility | report/notebook history | HARD_DATA_BLOCKER. |

## Dependency order decision

The requested order is halted before full training at leakage-free P0 generation. Safe CPU checks of target construction, Fixed, Naive, PCC, EIA, state propagation, metrics, failures, and artifact replay can proceed independently. Cohort training must not proceed until a held-out P0 route and its locked data/folds are made authoritative and accessible.
