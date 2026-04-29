# GenoADME

**Genotype-conditional ADME prediction for PBPK simulation.**

Status: pre-release (v0.1.0). The first preprint deposit is targeted; this README will be updated with results when validation completes against the pre-specified tiers documented in [`docs/validation-tiers.md`](docs/validation-tiers.md).

-----

## What this does

GenoADME is a pharmacogenomic extension of [Sisyphus](https://github.com/jam-sudo/Sisyphus). It takes:

- A SMILES string (the drug)
- A genotype — either an individual variant call set or a population sampled from 1000 Genomes phase 3

and returns a distribution of plasma pharmacokinetic (PK) trajectories conditional on that genotype, by routing genotype information through tissue eQTL effects (GTEx v8) into Sisyphus’s existing ADME parameter predictors.

Without genotype input, GenoADME reduces to Sisyphus’s average-patient prediction. Genotype is an optional refinement, not a mandatory input.

```python
import genoadme

# Average-patient prediction (equivalent to Sisyphus)
genoadme.predict_pk("CC(=O)Oc1ccccc1C(=O)O", dose_mg=100)

# Single-individual prediction conditioned on genotype
genoadme.predict_pk(
    "CC(=O)Oc1ccccc1C(=O)O",
    dose_mg=100,
    genotype=patient_geno,
)

# Population-level distribution
genoadme.predict_pk(
    "CC(=O)Oc1ccccc1C(=O)O",
    dose_mg=100,
    population="1000G_holdout500",
)
```

-----

## Why this exists

Sisyphus’s preprint ([10.5281/zenodo.19827332](https://doi.org/10.5281/zenodo.19827332)) and Charon’s README both identify a specific architectural gap: the Bayesian refinement module conditions on observed plasma concentrations but cannot use a patient’s genotype as a prior, because there is no principled way to translate variant calls into the model’s parameter space. GenoADME is that translation layer.

The route is intentional and narrow:

```
DNA variant
  ↓ (eQTL effect from GTEx v8)
mRNA expression
  ↓ (categorical phenotype from CPIC star-allele tables, where applicable)
ADME parameter distribution
  ↓ (Sisyphus engine)
Plasma PK trajectory
```

Each arrow has known noise. The cumulative R² across the full chain is approximately 0.1 for most ADME genes. **GenoADME does not claim to “individualize” predictions in any clinically actionable sense.** It claims to reproduce known pharmacogenomic phenomena at the population level, with pre-specified tiers documenting what is expected to work and what is not.

-----

## Validation strategy (pre-specified)

The full tier specification lives in [`docs/validation-tiers.md`](docs/validation-tiers.md), committed before any validation run. Summary:

- **Tier 1** — strong eQTL signal + CPIC Level A. Hybrid mapping (categorical phenotype × continuous eQTL refinement). Pre-specified pairs: SLCO1B1/simvastatin, NAT2/isoniazid, UGT1A1/irinotecan.
- **Tier 2** — CPIC Level A but eQTL noisy. Categorical-only mapping. Pre-specified pairs: CYP2C19/clopidogrel, CYP2C9/warfarin.
- **Tier 3** — acknowledged gap (paralog-confounded or expression-activity discordance). Reported as expected failure, not modeled. Pre-specified: CYP2D6, CYP3A4, ABCB1.

Tier changes after validation has run require an audit log entry and a Limitations disclosure. There is no quiet re-tiering. The full discipline is in [`docs/scientific-integrity.md`](docs/scientific-integrity.md).

-----

## Reproducibility

Every reported metric regenerates from a single command on a clean clone:

```bash
git clone https://github.com/jam-sudo/GenoADME
cd GenoADME
pip install -e .
genoadme validate --tier all --seed 42
```

The seed used to draw the 500-individual holdout subset of 1000 Genomes is committed in [`docs/holdout-seed.md`](docs/holdout-seed.md). The holdout is generated once and is not used for any methodological choice — only for producing the headline metrics reported in the preprint.

A cherry-picking audit is recorded automatically. Sisyphus reported approximately 47 configuration feedback cycles on its 107-drug holdout; GenoADME commits to reporting its own number, whatever it turns out to be.

-----

## Architecture

GenoADME wraps Sisyphus rather than reimplementing it. All ODE solving, ADME prediction, and Bayesian refinement go through `sisyphus.*`. The new code in `src/genoadme/` is restricted to the PGx layer:

- `genoadme.pgx.genotype` — 1000 Genomes ingest, ADME variant extraction
- `genoadme.pgx.eqtl` — GTEx eQTL ingest, SNP-to-expression mapping
- `genoadme.pgx.phenotype` — CPIC star-allele tables, categorical phenotype assignment
- `genoadme.pgx.mapping` — hybrid (categorical + continuous) function returning a Sisyphus-compatible ADME parameter distribution
- `genoadme.audit` — query logging for the cherry-picking audit
- `genoadme.validate` — validation entry points keyed to tier

Full constraints in [`docs/architecture.md`](docs/architecture.md).

-----

## Data sources

- **1000 Genomes phase 3** — open data, ADME-gene VCF subsets committed in `data/genotype/`.
- **GTEx v8 eQTL summary statistics** — open data, ADME-gene effect tables committed in `data/eqtl/`.
- **PharmGKB / CPIC star-allele definitions** — CC-BY licensed, committed in `data/pharmgkb/`.
- **dbGaP-restricted GTEx individual-level data** — never appears in this repository. If imputation from public summary statistics is insufficient for a given module, that limitation is disclosed.

-----

## Limitations

GenoADME is a **research and educational tool only; not FDA-cleared.** Specific known limitations are tracked in [`docs/limitations.md`](docs/limitations.md). Headline items:

- The eQTL → mRNA → protein → activity → clinical-CL chain is noisy. GenoADME exposes this noise as a distribution; it does not pretend to resolve it.
- Tier 3 genes (CYP2D6, CYP3A4, ABCB1) are not modeled. Requesting them raises an explicit error.
- Linkage disequilibrium between ADME variants is preserved through individual-level 1000 Genomes sampling, but rare variants outside the 1000G ascertainment are not represented.
- Population diversity is limited to the five super-populations represented in 1000 Genomes phase 3.

-----

## Citation

This work has not yet been deposited as a preprint. The first preprint will be deposited on Zenodo when Tier 1 validation completes; this section will be updated with the DOI at that point.

The predecessor work is:

> Yoon, J. M. (2026). *Sisyphus: A Topology-Compiled Physiologically Based Pharmacokinetic Platform with Structure-Only Input and Bayesian Parameter Refinement.* Zenodo. https://doi.org/10.5281/zenodo.19827332

-----

## License

MIT.

-----

## Contact

Jae Min Yoon — jaemin6013@gmail.com — github.com/jam-sudo
