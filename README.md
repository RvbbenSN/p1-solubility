# Project 1: Aqueous Solubility Prediction (ESOL Benchmark)

## Scientific Context & Motivation

Aqueous solubility ($\log S$, where $S$ is in $\text{mol/L}$) is one of the most critical physicochemical properties in early-stage drug discovery, agrochemistry, and formulation science:
- A bioactive compound with poor aqueous solubility cannot reach sufficient systemic circulation in vivo, precipitates in biological fluids, and fails as a therapeutic candidate (ADMET attrition).
- Measuring aqueous solubility experimentally via shake-flask or potentiometric assays is resource-intensive and low-throughput.
- **The Core Question:** Can we accurately predict the aqueous solubility of small organic molecules directly from their 2D molecular graph representation (SMILES)?

---

## The Delaney ESOL Benchmark (2004)

In 2004, John S. Delaney (AstraZeneca) published a landmark paper:  
> *"ESOL: Estimating Aqueous Solubility Directly from Molecular Structure"*. *J. Chem. Inf. Comput. Sci.* 2004, 44, 3, 1000–1005.

### The Competition Between Crystal Lattice and Solvation
Aqueous solubility of an organic solid is governed by two competing thermodynamic terms:
1. **Crystal lattice energy:** The energy required to break molecular interactions in the solid crystal lattice (favored by molecular planarity, rigidity, and symmetry).
2. **Free energy of hydration:** The favorable electrostatic and hydrogen-bonding interactions between the solute and water molecules.

### Origin of the Dataset Columns
The dataset contains **1,128 small organic molecules** with two fundamentally different types of data:
1. **Experimental Ground Truth:**
   - `measured log solubility in mols per litre`: Experimental aqueous solubility measured at room temperature (25 °C), collected from historical physical chemistry compilations (Yalkowsky, Banerjee) and industrial assays.
2. **Computed 2D Molecular Descriptors:**
   - `Molecular Weight (MW)`: Larger solute cavity required in the hydrogen-bonded water network $\rightarrow$ tends to decrease solubility.
   - `Number of H-Bond Donors`: Hydroxyl ($-\text{OH}$) and amine ($-\text{NH}$) groups forming strong hydrogen bonds with water $\rightarrow$ drastically increases solubility.
   - `Polar Surface Area (PSA / TPSA)`: Area of van der Waals surface associated with oxygen and nitrogen atoms $\rightarrow$ favorable dipole interactions with water $\rightarrow$ increases solubility.
   - `Number of Rings` and `Number of Rotatable Bonds`: Proxies for molecular rigidity and packing entropy. Rigid, planar, polycyclic aromatic compounds pack into stable lattices with high melting points $\rightarrow$ poor solubility.
   - `Minimum Degree`: A topological branching descriptor representing the lowest vertex degree in the heavy-atom graph.

### Delaney's Original Linear Baseline (ESOL Equation)
Delaney performed a multivariate linear regression on these computed descriptors to derive the classical ESOL equation:
$$\log S = 0.16 - 0.63 \cdot \text{cLogP} - 0.0062 \cdot \text{MW} + 0.066 \cdot \text{RB} - 0.74 \cdot \text{Aromatic Proportion}$$
The column `ESOL predicted log solubility in mols per litre` represents the output of this historical formula, which achieved an **RMSE of ~0.55–0.60 $\log S$ units** on training/test splits.

---

## Project Roadmap & Pipeline Architecture

Rather than relying on Delaney's precomputed columns, this project re-implements the full end-to-end modern cheminformatics workflow:

1. **Exploration & Schema Inspection (Week 1):** Raw dataset loading, missing value validation, and extreme case analysis with `pandas`.
2. **Chemical Curation with RDKit (Week 2):** Parse raw SMILES, validate valence, remove salts/solvents, neutralize formal charges, canonicalize, and log rejected structures with provenance.
3. **Featurization (Week 3):** Calculate physical RDKit 2D descriptors vs. Morgan Fingerprints (ECFP4/ECFP6).
4. **Chemically-Aware Splitting (Week 3):** Compare Random Split vs. Bemis-Murcko Scaffold Split to measure true generalization across novel chemical families.
5. **Model Benchmarking (Week 4):**
   - Baseline: Ordinary Least Squares (Linear Regression).
   - Non-linear models: Random Forest and XGBoost.
   - Target benchmark: Compare test set RMSE against literature reference (~0.55–0.70 $\log S$).
6. **Interactive Dashboard:** Deploy a generic Streamlit app to visualize predictions, residual plots, and chemical structures.

---

## Reproducibility

```bash
# Clone and enter project
cd projects/p1-solubility

# Install locked dependencies
uv sync

# Run tests
uv run pytest

# Launch interactive exploration
uv run jupyter lab
```
