# Raw Data Provenance

## ESOL (Delaney, 2004)

- **File name:** `delaney-processed.csv`
- **Original reference:** Delaney, J. S. *"ESOL: Estimating Aqueous Solubility Directly from Molecular Structure"*. *J. Chem. Inf. Comput. Sci.* 2004, 44, 3, 1000–1005. DOI: [10.1021/ci034243x](https://doi.org/10.1021/ci034243x).
- **Download source:** Curated MoleculeNet / DeepChem distribution:
  `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv`
- **Download date:** 2026-10-26
- **Size:** 1,128 molecules (1,129 lines with header), ~95 KB.
- **License:** Open scientific benchmark data for public access.
- **Target variable ($y$):** `measured log solubility in mols per litre` ($\log S$, in mol/L).
- **Structural input ($X$):** `smiles` column.

> **Immutability rule:** This file must never be manually modified, filtered, or overwritten. Any curation, standardization, or feature extraction must be performed programmatically via reproducible code producing outputs in `data/processed/`.
