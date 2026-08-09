
# Locked RHUH external mask mapping

Internal MU-Glioma-Post masks use all non-background labels 1–4. RHUH masks are locked as `segmentation > 0`: label 1 necrosis, label 2 peritumoral/non-enhancing abnormality, and label 3 enhancing tumor. This is the closest available pathological-region mapping, not perfect ontology equivalence, because RHUH lacks an independent resection-cavity label.

The mapping cannot be changed after RHUH results to label 3 only, labels 1+3, labels 2+3, or any other combination. The ontology difference is a predeclared limitation.
