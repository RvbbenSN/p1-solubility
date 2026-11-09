# Chemical Curation Audit Report

- **Input dataset:** `data/raw/delaney-processed.csv`
- **Output curated dataset:** `data/processed/esol_curated.csv`
- **Pipeline:** RDKit valence check, largest fragment desalting, canonicalization.

## Curation Statistics

| Metric | Count | Percentage |
|---|---|---|
| Total input molecules | 1128 | 100.0% |
| Valid curated molecules | 1128 | 100.0% |
| Rejected molecules | 0 | 0.0% |
| Canonicalized SMILES (notation normalized) | 624 | 55.3% |

## Audit Summary
- All 1,128 molecules were successfully validated and desalted.
- 624 molecules had their SMILES string standardized to canonical universal notation.
- 0 molecules were discarded (ESOL is a historically pre-filtered benchmark).
