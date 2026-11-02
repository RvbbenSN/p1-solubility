"""
Tests for chemical curation module (curate.py).

Follows specifications defined in specs/curate.md.
Tests are written first (TDD: Red phase) before implementing logic.
"""

import pandas as pd
import pytest

from p1_solubility.curate import CurationResult, curate_dataset, curate_smiles


class TestCurateSmiles:
    """Unit tests for single-molecule curation function curate_smiles()."""

    def test_curate_valid_standard_smiles(self) -> None:
        """Standard valid SMILES should return success=True and exact canonical SMILES."""
        result = curate_smiles("CCO")
        assert isinstance(result, CurationResult)
        assert result.success is True
        assert result.canonical_smiles == "CCO"
        assert result.error_reason is None
        assert result.original_smiles == "CCO"

    def test_curate_canonicalization_variants(self) -> None:
        """Alternative valid SMILES of the same molecule must produce identical canonical output."""
        result_occ = curate_smiles("OCC")
        result_coc = curate_smiles("C(O)C")

        assert result_occ.success is True
        assert result_coc.success is True
        assert result_occ.canonical_smiles == "CCO"
        assert result_coc.canonical_smiles == "CCO"

    def test_curate_empty_or_whitespace_string(self) -> None:
        """Empty strings, whitespace, or invalid non-string input should be rejected."""
        result_empty = curate_smiles("")
        result_spaces = curate_smiles("   ")

        assert result_empty.success is False
        assert result_empty.canonical_smiles is None
        assert result_empty.error_reason == "empty_smiles"

        assert result_spaces.success is False
        assert result_spaces.canonical_smiles is None
        assert result_spaces.error_reason == "empty_smiles"

    def test_curate_corrupted_text(self) -> None:
        """Arbitrary non-chemical text must be rejected safely with invalid_smiles."""
        result = curate_smiles("not_a_molecule")
        assert result.success is False
        assert result.canonical_smiles is None
        assert result.error_reason == "invalid_smiles"

    def test_curate_unclosed_ring(self) -> None:
        """Syntactically broken rings must be rejected without crashing."""
        result = curate_smiles("C1CCCCC")
        assert result.success is False
        assert result.canonical_smiles is None
        assert result.error_reason == "invalid_smiles"

    def test_curate_impossible_valence(self) -> None:
        """Chemically impossible hypervalent atoms must be rejected."""
        result = curate_smiles("C(C)(C)(C)(C)C")  # Pentavalent carbon
        assert result.success is False
        assert result.canonical_smiles is None
        assert result.error_reason == "invalid_smiles"

    def test_curate_salt_mixture_desalts_largest_fragment(self) -> None:
        """Salts must be desalted, keeping the largest organic active ingredient."""
        # Sodium benzoate: [Na+] + benzoate ion
        result = curate_smiles("[Na+].[O-]C(=O)c1ccccc1")
        assert result.success is True
        assert result.error_reason is None
        assert result.canonical_smiles == "O=C([O-])c1ccccc1"

    def test_curate_aromatic_heterocycle(self) -> None:
        """Pyridine (aromatic heterocycle) must survive curation unchanged."""
        result = curate_smiles("c1ccncc1")
        assert result.success is True
        assert result.canonical_smiles == "c1ccncc1"

    @pytest.mark.parametrize("smiles", ["[Na+]", "[Cl-]"])
    def test_curate_lone_inorganic_ion_is_rejected(self, smiles: str) -> None:
        """A lone inorganic ion (no carbon) is not a molecule we can model."""
        result = curate_smiles(smiles)
        assert result.success is False
        assert result.canonical_smiles is None
        assert result.error_reason == "no_carbon"

    def test_curate_lone_proton_has_no_heavy_atoms(self) -> None:
        """A lone proton has zero heavy atoms and gets its own rejection reason."""
        result = curate_smiles("[H+]")
        assert result.success is False
        assert result.error_reason == "no_heavy_atoms"

    @pytest.mark.parametrize("value", [None, float("nan"), 42])
    def test_curate_non_string_input_is_rejected(self, value: object) -> None:
        """None, NaN or numbers must be rejected as empty_smiles, never raise."""
        result = curate_smiles(value)  # type: ignore[arg-type]
        assert result.success is False
        assert result.error_reason == "empty_smiles"

    def test_curate_strips_surrounding_whitespace(self) -> None:
        """Leading/trailing whitespace is ignored; original input is preserved."""
        result = curate_smiles("  CCO \n")
        assert result.success is True
        assert result.canonical_smiles == "CCO"
        assert result.original_smiles == "  CCO \n"


class TestCurateDataset:
    """Integration tests for batch curation function curate_dataset()."""

    def test_curate_dataset_separates_valid_and_rejected(self) -> None:
        """curate_dataset must split a DataFrame into clean data and an auditable rejected table."""
        raw_data = {
            "Compound ID": ["Ethanol", "Sodium Benzoate", "Broken"],
            "smiles": ["OCC", "[Na+].[O-]C(=O)c1ccccc1", "C1CCCC"],
            "solubility": [-0.3, -1.2, -5.0],
        }
        df = pd.DataFrame(raw_data)

        valid_df, rejected_df = curate_dataset(
            df, smiles_col="smiles", id_col="Compound ID"
        )

        # Check valid dataset
        assert len(valid_df) == 2
        assert "curated_smiles" in valid_df.columns
        assert (
            valid_df.loc[valid_df["Compound ID"] == "Ethanol", "curated_smiles"].iloc[0]
            == "CCO"
        )
        assert (
            valid_df.loc[
                valid_df["Compound ID"] == "Sodium Benzoate", "curated_smiles"
            ].iloc[0]
            == "O=C([O-])c1ccccc1"
        )

        # Check rejected audit table
        assert len(rejected_df) == 1
        assert rejected_df.iloc[0]["Compound ID"] == "Broken"
        assert rejected_df.iloc[0]["error_reason"] == "invalid_smiles"
        assert rejected_df.iloc[0]["original_smiles"] == "C1CCCC"

    def test_curate_dataset_without_id_col(self) -> None:
        """id_col is optional; the audit table still carries original_smiles and error_reason."""
        df = pd.DataFrame({"smiles": ["CCO", ""], "y": [1.0, 2.0]})
        valid_df, rejected_df = curate_dataset(df, smiles_col="smiles")
        assert len(valid_df) == 1
        assert len(rejected_df) == 1
        assert list(rejected_df.columns) == ["original_smiles", "error_reason"]
        assert rejected_df.iloc[0]["error_reason"] == "empty_smiles"

    def test_curate_dataset_empty_dataframe(self) -> None:
        """An empty table yields two empty tables with the expected columns."""
        df = pd.DataFrame({"smiles": pd.Series([], dtype="object")})
        valid_df, rejected_df = curate_dataset(df, smiles_col="smiles")
        assert valid_df.empty
        assert rejected_df.empty
        assert "curated_smiles" in valid_df.columns
        assert "error_reason" in rejected_df.columns

    def test_curate_dataset_missing_column_raises(self) -> None:
        """A missing SMILES or id column must fail with a clear ValueError."""
        df = pd.DataFrame({"smiles": ["CCO"]})
        with pytest.raises(ValueError, match="nope"):
            curate_dataset(df, smiles_col="nope")
        with pytest.raises(ValueError, match="missing_id"):
            curate_dataset(df, smiles_col="smiles", id_col="missing_id")

    def test_curate_dataset_does_not_mutate_input(self) -> None:
        """The input DataFrame must be left untouched (pure function)."""
        df = pd.DataFrame({"smiles": ["OCC"]})
        before = df.copy(deep=True)
        curate_dataset(df, smiles_col="smiles")
        pd.testing.assert_frame_equal(df, before)
