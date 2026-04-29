# Limitations

> Research and educational tool only; not FDA-cleared.

This document is the canonical limitations record for GenoADME. The README cites it; the Tier 3 `UnsupportedGeneError` message points users here. The preprint Discussion section is built from this file.

If a limitation is discovered later, it is **added** to this document with the date discovered. Limitations are not silently removed even if a future version mitigates them — a “Mitigated” annotation is added instead.

-----

## 1. The eQTL → activity → CL chain is noisy

The pipeline is:

```
DNA variant → mRNA expression → protein abundance → enzyme activity → clinical CL
   (eQTL)        (GTEx)            (proteomics)        (in vitro)        (in vivo)
```

Each step contributes residual variance. Across most ADME genes the cumulative R² of the full chain is approximately 0.1. GenoADME exposes this noise as a distribution; it does not pretend to resolve it.

**What this means in practice:**

- Predicted PK distributions for a single individual are wide. Two individuals with the same star-allele assignment can have substantially different predicted CL.
- GenoADME is **not** a clinical decision support tool. The phrase “individualize predictions” does not appear in any GenoADME documentation in a clinically actionable sense.
- Population-level metrics (AAFE, %within-Nx) are the appropriate level of evaluation. Per-individual point predictions are not.

-----

## 2. Tier 3 genes are not modeled

The Tier 3 genes — **CYP2D6, CYP3A4, ABCB1** — are not modeled by GenoADME. Requesting a prediction conditional on any of these genes raises `genoadme.errors.UnsupportedGeneError`.

The reasons are gene-specific and documented in [`docs/validation-tiers.md`](validation-tiers.md):

- **CYP2D6** — paralog CYP2D7 confounds GTEx mRNA mapping; functional variation is dominated by structural variants not reliably called from 1000 Genomes phase 3 short-read WGS.
- **CYP3A4** — well-documented expression-vs-activity discordance; mRNA expression and clinical CL are weakly correlated even with paired data.
- **ABCB1** — transporter activity vs mRNA discordance; clinical impact of common variants has been inconsistent across studies.

This is the most clinically consequential limitation, because CYP2D6 covers a large fraction of clinically actionable pharmacogenomic interventions. GenoADME does not paper over the gap.

-----

## 3. Population diversity is limited to 1000 Genomes phase 3

The holdout and all reported population-level metrics are drawn from 1000 Genomes phase 3, which represents five super-populations (AFR, AMR, EAS, EUR, SAS). This implies:

- Allele-frequency estimates for ADME variants are limited to those super-populations.
- Populations not represented in 1000G (e.g., many indigenous populations, admixed groups outside the AMR samples) are not modeled.
- Rare variants outside the 1000G ascertainment threshold are not represented at all.

The preprint reports per-super-population metrics in addition to the aggregate, so a reader can assess whether a result is driven by one ancestry group.

-----

## 4. Linkage disequilibrium is preserved only via individual-level sampling

LD between ADME variants is preserved by sampling whole individuals from 1000 Genomes — not by modeling an LD matrix explicitly. This means:

- Predictions on a synthetic individual constructed by independently sampling allele frequencies will be unrealistic for genes with strong intragenic LD (e.g., SLCO1B1 haplotypes).
- A user supplying an external genotype must supply phased or genotype-call data, not allele frequencies.

-----

## 5. dbGaP-restricted GTEx data is not used

Individual-level GTEx data (paired genotype + tissue RNA-seq) is dbGaP-restricted and is not available in this public repository ([`architecture.md`](architecture.md) §4). Consequences:

- The eQTL effects used by GenoADME come from **published GTEx v8 summary statistics** (open data), not from re-analyzing individual-level GTEx samples.
- This means GenoADME inherits any residual confounding present in the published summary statistics (e.g., population structure correction choices, RNA-seq QC choices).
- Sensitivity analyses against alternative published eQTL sources (e.g., MAGE for lymphoblastoid, Geuvadis as a proxy with public WGS+RNA-seq) are not performed in v0.1.0.

-----

## 6. CPIC star-allele tables are a versioned dependency

Categorical phenotype assignment (Tier 1 and Tier 2) depends on the CPIC star-allele tables snapshotted in `data/pharmgkb/`. Limitations:

- A CPIC table update may move individuals between phenotype categories. The version of the CPIC tables used for the preprint is committed and referenced by SHA.
- Star-allele definitions sometimes require structural-variant detection (gene duplications, hybrid alleles). When the structural call is unreliable from short-read WGS (notably CYP2D6, hence its Tier 3 status), a categorical assignment is not produced.

-----

## 7. PBPK assumptions inherited from Sisyphus

GenoADME does not relitigate Sisyphus’s PBPK assumptions. Any limitation of Sisyphus’s ODE solver, organ topology, or ADME parameter predictors is also a limitation of GenoADME. The Sisyphus preprint ([10.5281/zenodo.19827332](https://doi.org/10.5281/zenodo.19827332)) documents these.

If a Sisyphus limitation interacts unfavorably with PGx prediction (for example, an ADME parameter whose Sisyphus point estimate has high uncertainty becomes more important in a Tier 1 pair), it is noted in the relevant validation report’s **Audit notes** section.

-----

## 8. What this tool does not claim to do

To make the scope unambiguous:

- GenoADME does **not** recommend doses.
- GenoADME does **not** identify individual patients as “poor metabolizers” for clinical purposes.
- GenoADME does **not** replace CPIC clinical guidelines for any drug.
- GenoADME does **not** model drug-drug interactions beyond what Sisyphus models.
- GenoADME does **not** model paediatric or pregnancy physiology.
- GenoADME does **not** validate against prospective clinical data — all validation is retrospective against published pharmacogenomic phenomena.

-----

## 9. v0.1.0 PK propagation is limited to OATP1B1-mediated substrates

**Discovered:** 2026-04-29 (commit *to be filled at commit time*).

The body-graph enzyme-and-transporter abundance scaling that GenoADME drives via Sisyphus's `apply_phenotype_to_graph` propagates to predicted PK only along Sisyphus's Extended Clearance Model (ECM) pathway, which in v0.1.0 covers OATP1B1-mediated hepatic uptake. Specifically:

- **Generic CYP-cleared drugs**: Sisyphus's CLint comes from an XGBoost predictor on molecular descriptors. Scaling liver enzyme abundance does not change the predicted CLint and therefore does not change the predicted PK. Empirical: caffeine + CYP1A2 PM moved AUC by 8.5×10⁻¹⁰ (floating-point noise).
- **Prodrugs not in Sisyphus's activation registry**: Without a registry entry, the active species is not produced in simulation. Genotype-driven scaling on the activating enzyme therefore has no path to influence active-species PK. The current registry covers BH4, GS-441524, tebipenem, R406 — none of GenoADME's originally-scoped prodrug pairs (clopidogrel, simvastatin, irinotecan→SN-38).
- **Genes absent from `PHENOTYPE_SCALES` or from `reference_man.yaml`**: NAT2 and UGT1A1, both of which appear in the GenoADME deferred-pairs list, are not represented in Sisyphus's current physiology graph or activity-multiplier table.

This is why v0.1.0 reduces the validation scope to a single pair (SLCO1B1/pravastatin) — the only pair for which the full eQTL-→categorical-→graph-scaling-→PK chain can be exercised against the holdout under the pinned Sisyphus build. The original five-pair scope is preserved as a Deferred roadmap in [`docs/validation-tiers.md`](validation-tiers.md), each pair annotated with the specific Sisyphus blocker.

The implication for users: phenotype-conditional predictions from `genoadme.predict_pk(genotype=...)` are reliable only where the underlying Sisyphus pipeline has a propagation path. For drugs outside the supported set, the prediction reduces silently to the average-patient case. This is a real foot-gun and is the reason the v0.1.0 wrapper is intentionally narrow.

-----

## Adding to this document

New limitations are added with the format:

```
## N. <one-line title>
**Discovered:** YYYY-MM-DD (commit <sha>)
<body>
```

Limitations are not removed; mitigations are noted in-line.