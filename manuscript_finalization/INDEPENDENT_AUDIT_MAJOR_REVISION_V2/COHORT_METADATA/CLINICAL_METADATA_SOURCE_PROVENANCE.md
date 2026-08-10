# Clinical metadata source provenance

- MU-Glioma-Post official TCIA clinical workbook: https://www.cancerimagingarchive.net/wp-content/uploads/MU-Glioma-Post_ClinicalData-July2025.xlsx; SHA-256 `4341badf954511d67fc52b82b3b488ed7323f7e46d249a354ff9b3a62269c79b`. All 40 development and 113 amended internal IDs matched exactly.
- RHUH-GBM official TCIA clinical CSV: https://www.cancerimagingarchive.net/wp-content/uploads/clinical_data_TCIA_RHUH-GBM.csv; SHA-256 `32d638906d34aaf8f66f5ec41c53c044216aed73bac22c776fb399bf2f741728`. All 39 locked external IDs matched exactly; RHUH-0008 was not included.

No patient was added, excluded or reclassified. No significance test was performed. Non-positive or nonnumeric MRI-date differences were retained as source-metadata anomalies and treated as missing; they were not repaired or imputed.
