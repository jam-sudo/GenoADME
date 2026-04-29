# Architecture Constraints

This document expands [`CLAUDE.md` §6](../CLAUDE.md#6-architecture-constraints).

These are scope decisions, not preferences. Violating them turns GenoADME from a focused PGx extension into a parallel reimplementation of Sisyphus, which the project does not want.

-----

## 1. GenoADME wraps Sisyphus — wiring strategy

All ODE solving, ADME prediction, Bayesian refinement, and uncertainty propagation routines are imported from `sisyphus.*`. GenoADME adds a single new layer — the PGx layer — that conditions Sisyphus's existing ADME parameter distributions on genotype.

GenoADME is allowed to call Sisyphus's **public lower-level building blocks** (`sisyphus.graph.builder.build_from_yaml`, `sisyphus.predict.phenotype.apply_phenotype_to_graph`, `sisyphus.predict.ivive.build_drug_on_graph`, `sisyphus.engine.compiler.ODECompiler` / `ResolvedParams`, `sisyphus.engine.solver.solve`, `sisyphus.pk.endpoints.compute_endpoints`, `sisyphus.predict.transporter_db.load_oatp1b1_kinetics` / `load_hepatic_ecm_params`). The genotype-conditional pipeline in `genoadme.predict.predict_pk` (with-genotype path) and `genoadme.validate.run_tier1` orchestrates these in the same order Sisyphus's own `tests/integration/test_slco1b1_phenotype.py` does — that integration test is the reference pattern. This is route (b) in the v0.1.0 implementation decision recorded in [`docs/tier-changes.md`](tier-changes.md).

GenoADME is **not** allowed to reimplement what these building blocks already do. If a Sisyphus building block is missing or insufficient (for example, ECM auto-detection from a substrate registry), the response is to **open an issue against Sisyphus** (the user will decide whether to upstream a change) and track the gap in [`docs/validation-tiers.md`](validation-tiers.md) §Deferred. The response is *not* to reimplement the missing capability inside GenoADME.

The no-genotype path of `predict_pk` is the simpler case — it delegates directly to `sisyphus.pipeline.predict.predict`, which is the convenience wrapper Sisyphus exposes for generic SMILES → PK use.

### What lives in `genoadme/`

- `genoadme/pgx/genotype.py` — 1000 Genomes ingest, ADME variant extraction, individual-level genotype dataclass.
- `genoadme/pgx/eqtl.py` — GTEx eQTL ingest, SNP-to-expression effect mapping, LD-aware sampling.
- `genoadme/pgx/phenotype.py` — CPIC star-allele tables, categorical phenotype *caller* (the missing piece — Sisyphus consumes phenotype labels but does not produce them from variant calls).
- `genoadme/pgx/mapping.py` — hybrid (categorical + continuous) function that turns a genotype into a `{gene: phenotype_label}` dict consumed by `sisyphus.predict.phenotype.apply_phenotype_to_graph`.
- `genoadme/audit.py` — query logging, seed verification, report generation.
- `genoadme/validate.py` — validation entry points keyed to tier (`run_tier1`, etc.). The Tier 1 runner is the only place GenoADME orchestrates Sisyphus's lower-level building blocks; that orchestration mirrors `sisyphus/tests/integration/test_slco1b1_phenotype.py` line-for-line in spirit.

### What does not live in `genoadme/`

- ODE solvers, scaffold-stratified holdout splitting, four-track ensemble logic, Bayesian refinement backends, top-level `predict()` orchestration (chemistry → ADME → drug-on-graph → engine → ML → meta-learner). All of these are `sisyphus.*` imports.
- Phenotype label definitions (PM/IM/EM/NM/UM/RM) and activity multipliers — these are re-exported from `sisyphus.predict.phenotype.PHENOTYPE_SCALES` rather than redefined.

-----

## 2. PGx layer is composable and optional

A user calling `genoadme.predict_pk(smiles)` without genotype input must receive a sensible default — namely, the average-patient Sisyphus prediction, unchanged.

```python
# Without genotype: equivalent to Sisyphus
genoadme.predict_pk("CC(=O)Oc1ccccc1C(=O)O")

# With genotype: Sisyphus prediction conditioned on PGx layer
genoadme.predict_pk("CC(=O)Oc1ccccc1C(=O)O", genotype=patient_geno)

# With population: distribution across genotyped individuals
genoadme.predict_pk("CC(=O)Oc1ccccc1C(=O)O", population="1000G_holdout")
```

Genotype is an optional refinement, never a mandatory input. A user without access to genotype data can still use GenoADME as a Sisyphus convenience wrapper.

-----

## 3. Tier 3 genes raise explicit errors

If a user requests a prediction conditional on a Tier 3 gene (CYP2D6, CYP3A4, ABCB1), the function raises `genoadme.errors.UnsupportedGeneError` with a message that points to [`docs/limitations.md`](limitations.md) and to [`docs/scientific-integrity.md`](scientific-integrity.md) §1.

Silent fallback (e.g., returning the average-patient prediction with a warning) is not acceptable. The whole point of pre-specified tiers is to signal to the user *before* they get a number that the number would be unreliable.

-----

## 4. Data licensing constraints

- **1000 Genomes phase 3:** Open data. Variant subsets used by GenoADME are committed in `data/genotype/` as VCF subsets restricted to ADME genes.
- **GTEx eQTL summary statistics (v8 or v10):** Open data. Effect-size tables for ADME genes are committed in `data/eqtl/`.
- **GTEx individual-level data (genotype + tissue RNA-seq):** dbGaP-restricted. **Must not appear** in this repository or any commit. If any module needs individual-level GTEx data, that need must be flagged and resolved (likely by using imputation from public summary statistics, or by accessing Geuvadis as a proxy lymphoblast dataset with public WGS+RNA-seq pairs).
- **PharmGKB / CPIC:** PharmGKB allele definitions are CC-BY licensed; CPIC guidelines are public. Both can be redistributed with citation.

Each module that loads data has a docstring noting the data source and license.

-----

## 5. Repository layout

```
genoadme/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── src/genoadme/
│   ├── __init__.py
│   ├── pgx/
│   │   ├── genotype.py
│   │   ├── eqtl.py
│   │   ├── phenotype.py
│   │   └── mapping.py
│   ├── audit.py
│   ├── validate.py
│   └── errors.py
├── data/
│   ├── genotype/         # 1000G ADME-gene VCF subsets
│   ├── eqtl/             # GTEx eQTL effect tables
│   └── pharmgkb/         # CPIC allele definitions
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
│   ├── scientific-integrity.md
│   ├── architecture.md
│   ├── reporting-standards.md
│   ├── commit-discipline.md
│   ├── validation-tiers.md
│   ├── tier-changes.md
│   ├── holdout-seed.md
│   └── limitations.md
└── reports/
    ├── validation-tier1-YYYYMMDD.md
    ├── validation-tier2-YYYYMMDD.md
    ├── audit-log.jsonl
    └── headline-metrics-YYYYMMDD.json
```
