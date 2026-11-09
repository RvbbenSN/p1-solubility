# Specification: Chemical Curation Module (`curate.py`)

## 1. Objective

Provide a robust, pure-function chemical curation pipeline using RDKit to clean, validate, desalt, and canonicalize SMILES strings from raw experimental datasets (specifically for the Delaney ESOL benchmark in P1). 

The module must ensure complete scientific traceability: every valid molecule is canonicalized, and every invalid or rejected molecule is logged with an explicit, auditable reason.

---

## 2. Affected Files

- **Specification:** `specs/curate.md` (this file, strictly mirroring module name)
- **Implementation:** `src/p1_solubility/curate.py`
- **Unit & Integration Tests:** `tests/test_curate.py`
- **Package exports:** `src/p1_solubility/__init__.py`

---

## 2.1 Design Rationale & Methodological Notes (Explicación de diseño)

1. **Exact 1-to-1 Naming Traceability:**
   - Spec: `specs/curate.md`
   - Logic: `src/p1_solubility/curate.py`
   - Tests: `tests/test_curate.py`
   This strict 1-to-1 correspondence ensures any developer or AI agent can immediately navigate between contract, implementation, and test suite without cognitive load.

2. **Immutable Result Object (`CurationResult`):**
   - Instead of returning raw strings or tuples that obscure intent, we use an immutable dataclass (`frozen=True`).
   - If curation succeeds: `success=True`, `canonical_smiles="CCO"`, `error_reason=None`.
   - If curation fails: `success=False`, `canonical_smiles=None`, `error_reason="invalid_smiles"`.
   - The original input is preserved in `original_smiles` for full scientific auditability.

3. **Separation of Molecule vs. Table Concerns:**
   - `curate_smiles()` is the **pure atomic function**: receives a string, talks to RDKit, returns a `CurationResult`. Zero side-effects, zero knowledge of pandas or files.
   - `curate_dataset()` is the **table orchestrator**: applies `curate_smiles()` across a pandas DataFrame and cleanly splits the data into two output DataFrames:
     a) `valid_df`: Clean rows with an added `curated_smiles` column, ready for featurization.
     b) `rejected_df`: Discarded rows with their explicit rejection reasons for reporting.

---

## 3. Data Structures & Function Signatures

### 3.1 `CurationResult` (Output Dataclass)

```python
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CurationResult:
    """Immutable result of curating a single chemical structure."""

    success: bool
    canonical_smiles: Optional[str]
    error_reason: Optional[str]
    original_smiles: str
```

### 3.2 Single Structure Curation: `curate_smiles`

```python
def curate_smiles(smiles: str) -> CurationResult:
    """
    Validates, desalts, neutralizes, and canonicalizes a single SMILES string.

    Parameters
    ----------
    smiles : str
        Raw input SMILES string.

    Returns
    -------
    CurationResult
        Structured outcome containing success status, canonical SMILES (if valid),
        rejection reason (if invalid), and original input string.
    """
```

### 3.3 Dataset Batch Curation: `curate_dataset`

```python
import pandas as pd


def curate_dataset(
    df: pd.DataFrame, smiles_col: str, id_col: Optional[str] = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Curates an entire pandas DataFrame of chemical records.

    Parameters
    ----------
    df : pd.DataFrame
        Input table containing raw molecular structures.
    smiles_col : str
        Name of the column containing SMILES strings.
    id_col : Optional[str]
        Optional compound identifier column name.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        A tuple of (valid_df, rejected_df):
        - valid_df: contains original columns + 'curated_smiles', with invalid entries dropped.
        - rejected_df: audit table of discarded rows with 'original_smiles' and 'error_reason'.
    """
```

---

## 4. Pipeline Logic & Rejection Hierarchy

When `curate_smiles(smiles)` evaluates an input, it applies the following sequential steps:

1. **Empty / Non-string Check:**
   - If input is `None`, not a string, or empty/whitespace after `.strip()`:
     $\rightarrow$ `success=False`, `error_reason="empty_smiles"`.
2. **RDKit Parsing & Valence Validation:**
   - Attempt `Chem.MolFromSmiles(smiles.strip())`.
   - If RDKit returns `None` (unclosed rings, invalid valence, unrecognized atoms):
     $\rightarrow$ `success=False`, `error_reason="invalid_smiles"`.
3. **Desalting (Largest Fragment Selection):**
   - If molecule contains disconnected fragments (dot notation `.`):
     Extract fragments using `Chem.GetMolFrags(mol, asMols=True)`.
     Select the fragment with the highest number of heavy atoms (`frag.GetNumHeavyAtoms()`).
     If the largest fragment has 0 heavy atoms (only lone protons/inorganics):
     $\rightarrow$ `success=False`, `error_reason="no_heavy_atoms"`.
4. **Canonicalization:**
   - Convert the cleaned, largest fragment back to SMILES using `Chem.MolToSmiles(cleaned_mol, canonical=True)`.
   - Return `CurationResult(success=True, canonical_smiles=canonical, error_reason=None, original_smiles=smiles)`.

---

## 5. Edge Cases & Test Scenarios

| Test Case Category | Input Example | Expected Output | Expected `error_reason` |
|---|---|---|---|
| **Standard valid SMILES** | `"CCO"` | `success=True`, `canonical_smiles="CCO"` | `None` |
| **Alternative SMILES representations** | `"OCC"`, `"C(O)C"` | `success=True`, `canonical_smiles="CCO"` | `None` (canonicalized) |
| **Empty string** | `""` or `"   "` | `success=False`, `canonical_smiles=None` | `"empty_smiles"` |
| **Corrupted text** | `"not_a_molecule"` | `success=False`, `canonical_smiles=None` | `"invalid_smiles"` |
| **Unclosed ring** | `"C1CCCCC"` | `success=False`, `canonical_smiles=None` | `"invalid_smiles"` |
| **Hypervalent impossible atom** | `"C(C)(C)(C)(C)C"` | `success=False`, `canonical_smiles=None` | `"invalid_smiles"` |
| **Salt mixture** | `"[Na+].[O-]C(=O)c1ccccc1"` | `success=True`, `canonical_smiles="O=C([O-])c1ccccc1"` (benzoate) | `None` (desalted) |
| **Aromatic heterocycle** | `"c1ccncc1"` (pyridine) | `success=True`, `canonical_smiles="c1ccncc1"` | `None` |
| **Lone inorganic ion** | `"[Na+]"` or `"[Cl-]"` | `success=False`, `canonical_smiles=None` (or filtered if non-organic) | Tested in filter rule |

---

## 6. Acceptance Criteria

1. **Pure Core:** `curate.py` must not read from disk, write to disk, call `print()`, or rely on global state.
2. **Type Safety:** Full type annotations on all public functions, classes, and return values.
3. **Error Handling:** Explicit error categories (`empty_smiles`, `invalid_smiles`, etc.) without generic unhandled exceptions.
4. **Test Coverage:** Pytest suite in `tests/test_curation.py` testing every row of the edge cases table.
5. **Code Quality:** Pass `uv run ruff check .` and `uv run ruff format --check .` with zero warnings.
