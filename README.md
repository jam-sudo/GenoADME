# GenoADME

**Genotype-conditional ADME prediction for PBPK simulation.**

Status: pre-release (v0.1.0). Tier 1 validation re-run 2026-05-03 under Sisyphus pin `9f1680d` (issue #8 closing state, includes PR #22 OATP1B1/ECM reconciliation + PR #25 pravastatin SMILES fix + PR #28 digoxin SMILES fix) — **result: PARTIAL**. The 2026-05-03 run [supersedes](reports/validation-tier1-20260501.md) the 2026-05-01 numbers (the earlier pin `aef6f8e` is no longer reachable from `origin/main`). The current canonical report is [`reports/validation-tier1-20260503.md`](reports/validation-tier1-20260503.md) / [`reports/headline-metrics-20260503.json`](reports/headline-metrics-20260503.json). Population AAFE (AUC) **passes** comfortably (1.152 ≤ 2.0; up from 1.438 under the prior Sisyphus calibration). The failing criterion is the PM/EM AUC ratio (4.482, target band [1.4, 2.5]) — *more pronounced* under the post-Sisyphus-#8 calibration. Sisyphus #8 closing comment attributes the over-shoot to "CPIC PM activity scaling (0.10×) may be too aggressive for AUC", explicitly identifying it as community-standard rather than a Sisyphus-specific defect. A `tier-change:` commit will follow to (a) re-anchor the population-mean Cmax reference to FDA Pravachol per Sisyphus #8 closing recommendation, and (b) document the PM/EM AUC over-shoot as a known limitation pending v0.3 CPIC PM scale investigation. All three Tier 1 runs are part of the audit chain ([`reports/audit-log.jsonl`](reports/audit-log.jsonl)); the 2026-05-03 entry includes the new `worktree_clean` + `deps.sisyphus` fields enforced by the [`audit.log_query` gate](src/genoadme/audit.py) (GenoADME issue #1).

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

The full tier specification lives in [`docs/validation-tiers.md`](docs/validation-tiers.md), committed before any validation run. v0.1.0 commits to validating exactly **one drug-gene pair end-to-end**, with five additional pairs deferred to v0.2+ pending specific Sisyphus capability extensions:

- **Tier 1** — strong eQTL signal + CPIC Level A. Hybrid mapping (categorical phenotype × continuous eQTL refinement). v0.1.0 pair: **SLCO1B1 / pravastatin** (OATP1B1-mediated, validated against Niemi 2006 / Pasanen 2007 clinical data).
- **Tier 2** — CPIC Level A but eQTL noisy. Categorical-only mapping. **Empty in v0.1.0** — pre-specified pairs (CYP2C19/clopidogrel, CYP2C9/warfarin) are deferred because Sisyphus's pipeline does not propagate phenotype scaling to PK for prodrugs not in the activation registry or for non-ECM CYP-cleared drugs whose CLint is ML-predicted.
- **Tier 3** — acknowledged gap (paralog-confounded or expression-activity discordance). Reported as expected failure, not modeled. Pre-specified: CYP2D6, CYP3A4, ABCB1.
- **Deferred** — see [`docs/validation-tiers.md`](docs/validation-tiers.md) §Deferred for the five originally-scoped pairs (SLCO1B1/simvastatin, NAT2/isoniazid, UGT1A1/irinotecan, CYP2C19/clopidogrel, CYP2C9/warfarin) and the specific Sisyphus blocker for each.

The reduction from six pairs to one was a pre-validation spec correction logged in [`docs/tier-changes.md`](docs/tier-changes.md) — driven by empirical findings during v0.1.0 skeleton work, not by validation results. Tier changes after validation has run require an audit log entry and a Limitations disclosure. There is no quiet re-tiering. The full discipline is in [`docs/scientific-integrity.md`](docs/scientific-integrity.md).

-----

## Roadmap

Active versions track via GitHub milestones, each paired with the upstream Sisyphus dependency that gates it:

|Milestone                           |GenoADME                                                                 |Sisyphus dependency                                                            |Closing condition                                                                                                                                                                                                                                |
|------------------------------------|-------------------------------------------------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|**v0.2 — Tier 1 PASS**              |[milestone/1](https://github.com/jam-sudo/GenoADME/milestone/1)          |[Sisyphus milestone/1](https://github.com/jam-sudo/Sisyphus/milestone/1) (issue [#8](https://github.com/jam-sudo/Sisyphus/issues/8))             |Re-run `run_tier1()` against the SHA-pinned holdout produces population AAFE (AUC) ≤ 2.0 while PM/EM ratios stay in the v0.1.0 pre-spec band. Closes with a `metric-change:` commit per [`docs/commit-discipline.md`](docs/commit-discipline.md) §3. |
|**v0.3 — Activate Deferred pairs**  |[milestone/2](https://github.com/jam-sudo/GenoADME/milestone/2)          |[Sisyphus milestone/2](https://github.com/jam-sudo/Sisyphus/milestone/2) (issues [#9](https://github.com/jam-sudo/Sisyphus/issues/9), [#10](https://github.com/jam-sudo/Sisyphus/issues/10), [#11](https://github.com/jam-sudo/Sisyphus/issues/11)) |Promote at least one pair from [`docs/validation-tiers.md`](docs/validation-tiers.md) §Deferred back to an active tier under a `tier-change:` commit per [`docs/commit-discipline.md`](docs/commit-discipline.md) §4.                                |

Milestones intentionally separate **calibration** (v0.2 — moves the v0.1.0 PARTIAL number) from **capability** (v0.3 — extends Sisyphus to support drugs / genes the current build cannot represent at all). Either can be picked up independently of the other.

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
