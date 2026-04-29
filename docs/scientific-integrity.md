# Scientific Integrity Rules

This document expands [`CLAUDE.md` §5](../CLAUDE.md#5-scientific-integrity) with operational detail. These rules exist because GenoADME results will be cited under a real author name in a public preprint, and the author’s prior projects (Sisyphus, Charon) have publicly disclosed methodological failures. The discipline below is what makes those disclosures credible — and what would make a quiet revision of GenoADME results destroy that credibility.

-----

## 1. Pre-Specified Validation Tiers

The validation drug-gene pairs and their tier assignments live in [`docs/validation-tiers.md`](validation-tiers.md) and are committed **before any validation run is executed**.

### Tier definitions

- **Tier 1 — mechanistic, expected pass.**
  Gene has strong eQTL signal in GTEx liver/intestine **and** CPIC Level A actionable evidence. Predictions use the full hybrid mapping (categorical phenotype × continuous eQTL refinement). Pre-specified pairs:
  - SLCO1B1 / simvastatin (Sisyphus ECM available)
  - NAT2 / isoniazid
  - UGT1A1 / irinotecan
- **Tier 2 — categorical only, eQTL noisy.**
  Gene has CPIC Level A evidence but eQTL signal is unreliable for kinetic prediction. Predictions use only the PGx-categorical phenotype, no eQTL refinement. Pre-specified pairs:
  - CYP2C19 / clopidogrel (with prodrug activation routed via Charon)
  - CYP2C9 / warfarin
- **Tier 3 — acknowledged gap.**
  Gene relevant to ADME but eQTL signal too weak or paralog-confounded. Reported as an **expected failure** rather than modeled. Pre-specified:
  - CYP2D6 (paralog CYP2D7 confounds GTEx mapping)
  - CYP3A4 (expression vs activity discordance well documented)
  - ABCB1 (transporter activity vs mRNA discordance)

### Tier change protocol

Moving a drug-gene pair across tiers after validation has been run constitutes a **tier change**. A tier change must:

1. Be logged in [`docs/tier-changes.md`](tier-changes.md) with date, original tier, new tier, the validation result that triggered the move, and a brief rationale.
1. Be disclosed in the preprint Limitations section.
1. Trigger a re-run of every other validation case under whatever methodology was changed.

There is no quiet re-tiering. If a Tier 1 result fails, the failure is reported as a Tier 1 failure; the pair is not silently demoted to Tier 2.

-----

## 2. Held-Out Population Set

A 500-individual subset of 1000 Genomes phase 3 is sampled once. The seed and the resulting individual IDs are committed in [`docs/holdout-seed.md`](holdout-seed.md).

### What the holdout is for

Producing the headline population-level metrics reported in the preprint.

### What the holdout is **not** for

- Calibrating the eQTL → expression → ADME mapping function.
- Selecting between alternative mapping strategies.
- Tuning hyperparameters of any kind.
- Choosing which drug-gene pairs to include in Tier 1.

If the holdout is touched for any of the above, it is no longer a holdout. Generate a new one from a new seed, commit the new seed, and disclose the rotation in the preprint Limitations.

-----

## 3. No Quiet Metric Improvements

Reported metrics include population-level AAFE, %within-Nx, %CV reproduction error, and any per-tier headline number that appears in the preprint or `README.md`.

If a code change moves a reported metric, the change must:

1. Use the commit prefix `metric-change:` and include the old and new values in the commit message body. Example: `metric-change: SLCO1B1/simvastatin AAFE 1.83 → 1.71 after eQTL beta sign correction`.
1. Add an audit comment to the relevant `reports/validation-{tier}-{date}.md`.
1. Be reproducible: the new value must regenerate from a single command (e.g., `genoadme validate --tier 1 --seed 42`) on a clean clone.

This rule applies even to “obviously correct” fixes. The Sisyphus Meta AAFE 2.283 → 2.695 correction was an “obviously correct” fix. The disclosure of *why* it was needed is what made the corrected result trustworthy.

-----

## 4. Honest Disclosure of eQTL → Phenotype Limits

The expression → ADME parameter chain has well-known noise:

```
DNA variant → mRNA expression → protein abundance → enzyme activity → clinical CL
   (eQTL)        (GTEx)            (proteomics)        (in vitro)        (in vivo)
```

Each step contributes residual variance. Cumulative R² across the full chain is approximately 0.1 for most ADME genes. GenoADME must:

- Report population-level CV against published clinical CV, with confidence intervals.
- Acknowledge in `README.md` that eQTL-derived prediction is **complementary to, not a replacement for**, direct CPIC star-allele-to-phenotype mapping.
- Never claim that GenoADME “individualizes” predictions in a way that implies clinical actionability.

The phrase “research and educational tool only; not FDA-cleared” appears verbatim in `README.md` and at the top of every output report.

-----

## 5. Cherry-Picking Audit

Sisyphus reported approximately 47 configuration feedback cycles on its 107-drug retrospective holdout. GenoADME commits to reporting its own number, whatever it turns out to be.

### Implementation

The function `genoadme.audit.log_query(holdout_id, purpose)` is called automatically by every validation entry point. The log is committed at `reports/audit-log.jsonl` and is **append-only**. The preprint Methods section reports the count and the distribution of `purpose` values (e.g., 30 for “smoke test”, 12 for “tier 1 final run”, etc.).

### What counts as a “query”

Any execution that reads holdout individual genotypes or returns a holdout-population metric. Smoke tests count. Debugging runs count. Failed runs count.

### What does not count

Reading the holdout-seed file. Reading aggregate documentation about the holdout (counts, ancestry breakdown).

If the audit log shows the holdout has been queried more times than is reasonable for the reported development effort, the preprint Discussion must address it.
