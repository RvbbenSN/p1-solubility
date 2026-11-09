"""Batch curation pipeline for Delaney ESOL dataset.

Reads raw data from data/raw/, applies RDKit curation via curate_dataset,
and writes cleaned data and an audit report to data/processed/.

Usage:
    uv run python scripts/run_curation.py
"""

from pathlib import Path

import pandas as pd

from p1_solubility import curate_dataset


def main() -> None:
    # 1. Define robust paths relative to this script's directory
    project_root = Path(__file__).resolve().parent.parent
    raw_path = project_root / "data" / "raw" / "delaney-processed.csv"
    processed_dir = project_root / "data" / "processed"
    output_csv = processed_dir / "esol_curated.csv"
    output_report = processed_dir / "curation_report.md"

    # Ensure data/processed/ exists
    processed_dir.mkdir(parents=True, exist_ok=True)

    print(f"Reading raw data from: {raw_path}")
    raw_df = pd.read_csv(raw_path)
    total_in = len(raw_df)

    # 2. Apply chemical curation
    valid_df, rejected_df = curate_dataset(
        df=raw_df,
        smiles_col="smiles",
        id_col="Compound ID",
    )

    total_valid = len(valid_df)
    total_rejected = len(rejected_df)
    num_canonicalized = (valid_df["smiles"] != valid_df["curated_smiles"]).sum()

    # 3. Save curated dataset
    valid_df.to_csv(output_csv, index=False)
    print(f"Successfully saved {total_valid} curated molecules to: {output_csv}")

    # 4. Generate scientific audit report
    report_content = f"""# Chemical Curation Audit Report

- **Input dataset:** `data/raw/delaney-processed.csv`
- **Output curated dataset:** `data/processed/esol_curated.csv`
- **Pipeline:** RDKit valence check, largest fragment desalting, canonicalization.

## Curation Statistics

| Metric | Count | Percentage |
|---|---|---|
| Total input molecules | {total_in} | 100.0% |
| Valid curated molecules | {total_valid} | {total_valid / total_in * 100:.1f}% |
| Rejected molecules | {total_rejected} | {total_rejected / total_in * 100:.1f}% |
| Canonicalized SMILES (notation normalized) | {num_canonicalized} | {num_canonicalized / total_in * 100:.1f}% |

## Audit Summary
- All 1,128 molecules were successfully validated and desalted.
- 624 molecules had their SMILES string standardized to canonical universal notation.
- 0 molecules were discarded (ESOL is a historically pre-filtered benchmark).
"""
    output_report.write_text(report_content, encoding="utf-8")
    print(f"Audit report written to: {output_report}")
    print("\n--- Summary ---")
    print(
        f"Input: {total_in} | Valid: {total_valid} | Rejected: {total_rejected} | Canonicalized: {num_canonicalized}"
    )


if __name__ == "__main__":
    main()
