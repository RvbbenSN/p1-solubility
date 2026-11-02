"""Chemical curation: validate, desalt and canonicalize SMILES (see specs/curate.md)."""

from dataclasses import dataclass

import pandas as pd
from rdkit import Chem, RDLogger

EMPTY_SMILES = "empty_smiles"
INVALID_SMILES = "invalid_smiles"
NO_HEAVY_ATOMS = "no_heavy_atoms"
NO_CARBON = "no_carbon"

CURATED_COLUMN = "curated_smiles"
ORIGINAL_COLUMN = "original_smiles"
REASON_COLUMN = "error_reason"

_CARBON_ATOMIC_NUMBER = 6

# RDKit prints a parse error to stderr for every invalid SMILES; the reason is
# already reported through CurationResult, so keep the output clean.
RDLogger.DisableLog("rdApp.*")


@dataclass(frozen=True)
class CurationResult:
    """Immutable result of curating a single chemical structure."""

    success: bool
    canonical_smiles: str | None
    error_reason: str | None
    original_smiles: str


def _reject(original: object, reason: str) -> CurationResult:
    return CurationResult(
        success=False,
        canonical_smiles=None,
        error_reason=reason,
        original_smiles=original if isinstance(original, str) else str(original),
    )


def _largest_fragment(mol: Chem.Mol) -> Chem.Mol:
    """Return the fragment with the most heavy atoms (the first one wins a tie)."""
    fragments = Chem.GetMolFrags(mol, asMols=True)
    return max(fragments, key=lambda frag: frag.GetNumHeavyAtoms())


def curate_smiles(smiles: str) -> CurationResult:
    """Validate, desalt (keep largest fragment) and canonicalize one SMILES.

    Args:
        smiles: Raw SMILES string. Non-string values (None, NaN, numbers) are
            treated as empty.

    Returns:
        A CurationResult. On failure, ``error_reason`` is one of
        ``empty_smiles``, ``invalid_smiles``, ``no_heavy_atoms`` or ``no_carbon``.
        This function does not raise for bad chemical input.
    """
    if not isinstance(smiles, str) or not smiles.strip():
        return _reject(smiles, EMPTY_SMILES)

    mol = Chem.MolFromSmiles(smiles.strip())
    if mol is None:
        return _reject(smiles, INVALID_SMILES)

    largest = _largest_fragment(mol)
    if largest.GetNumHeavyAtoms() == 0:
        return _reject(smiles, NO_HEAVY_ATOMS)
    if not any(
        atom.GetAtomicNum() == _CARBON_ATOMIC_NUMBER for atom in largest.GetAtoms()
    ):
        return _reject(smiles, NO_CARBON)

    return CurationResult(
        success=True,
        canonical_smiles=Chem.MolToSmiles(largest, canonical=True),
        error_reason=None,
        original_smiles=smiles,
    )


def _check_columns(df: pd.DataFrame, columns: list[str]) -> None:
    missing = [name for name in columns if name not in df.columns]
    if missing:
        raise ValueError(
            f"Columns not found in DataFrame: {missing}. Available: {list(df.columns)}"
        )


def curate_dataset(
    df: pd.DataFrame,
    smiles_col: str,
    id_col: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Curate every row of a table and split it into valid and rejected rows.

    Args:
        df: Table with raw structures. It is not modified.
        smiles_col: Name of the column holding the SMILES strings.
        id_col: Optional compound identifier column, kept in the rejected table.

    Returns:
        ``(valid_df, rejected_df)``. ``valid_df`` has all original columns plus
        ``curated_smiles``. ``rejected_df`` has ``[id_col,] original_smiles,
        error_reason``, one row per discarded molecule.

    Raises:
        ValueError: If ``smiles_col`` or ``id_col`` is not a column of ``df``.
    """
    required = [smiles_col] if id_col is None else [smiles_col, id_col]
    _check_columns(df, required)

    results = [curate_smiles(value) for value in df[smiles_col]]
    ok = pd.Series([r.success for r in results], index=df.index, dtype=bool)

    valid_df = df.loc[ok].copy()
    valid_df[CURATED_COLUMN] = [r.canonical_smiles for r in results if r.success]

    rejected_df = pd.DataFrame(
        {
            ORIGINAL_COLUMN: [r.original_smiles for r in results if not r.success],
            REASON_COLUMN: [r.error_reason for r in results if not r.success],
        },
        index=df.index[~ok],
    )
    if id_col is not None:
        rejected_df.insert(0, id_col, df.loc[~ok, id_col])

    return valid_df, rejected_df
