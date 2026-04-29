# Validation Tiers (Pre-Specification)

This document is the **commitment record** for GenoADME’s validation strategy. The drug-gene pairs and tier assignments below are committed before any validation run is executed against the 500-individual holdout subset of 1000 Genomes phase 3 ([`docs/holdout-seed.md`](holdout-seed.md)).

If a tier assignment changes after validation has run, the change is logged in [`docs/tier-changes.md`](tier-changes.md) and disclosed in the preprint Limitations section. There is no quiet re-tiering. The full protocol is in [`docs/scientific-integrity.md`](scientific-integrity.md) §1.

**Date of initial commitment:** 2026-04-29
**git commit at time of commitment:** *to be filled at first commit of this file*

-----

## Tier 1 — Mechanistic, Expected Pass

Genes with strong eQTL signal in GTEx liver/intestine **and** CPIC Level A actionable evidence. Predictions use the full hybrid mapping: categorical phenotype (from CPIC star-allele tables) for inter-phenotype variation, plus continuous eQTL refinement for intra-phenotype variation.

### Tier 1 pairs

|Gene   |Drug              |Phenotype                              |Expected effect                             |Tier 1 pass criterion                                                        |
|-------|------------------|---------------------------------------|--------------------------------------------|-----------------------------------------------------------------------------|
|SLCO1B1|simvastatin       |rs4149056 (*5) carriers vs non-carriers|2.4-fold AUC increase in homozygous carriers|Population AAFE ≤ 2.0; carrier vs non-carrier predicted ratio within 1.5–3.5×|
|NAT2   |isoniazid         |slow vs rapid acetylator               |~2-fold CL difference                       |Population AAFE ≤ 2.0; slow vs rapid predicted CL ratio within 0.4–0.7       |
|UGT1A1 |irinotecan        |*28/*28 vs *1/*1                       |Increased SN-38 (active metabolite) exposure, neutropenia risk|Population AAFE ≤ 2.5 for SN-38 AUC; *28/*28 vs *1/*1 ratio ≥ 1.4            |

### Why these were selected

- **SLCO1B1**: Sisyphus already implements the OATP1B1 extended clearance model. The PGx layer here adds genotype-conditional `Vmax` modulation. This is the cleanest test case because the mechanistic framework already exists in the dependency.
- **NAT2**: Slow/rapid acetylator phenotypes are categorical and well-quantified in clinical literature. Binary phenotype is the simplest possible test of the categorical-mapping pathway.
- **UGT1A1**: *28 promoter polymorphism is the canonical example of a TA-repeat variant affecting transcription. Tests whether the eQTL pathway can capture promoter-level regulatory variation.

### Why not other Tier 1 candidates

- **DPYD / 5-fluorouracil**: CPIC Level A, but the active variants are largely loss-of-function point mutations whose effect on enzyme activity is non-linear and not well-captured by tissue eQTL summary statistics. Better suited to a categorical-only model — would belong in Tier 2 if added.
- **TPMT / thiopurines**: Phenotype is typically inferred by enzyme assay rather than genotype + expression in clinical practice. The eQTL → activity chain has been studied but adds noise relative to direct phenotype measurement.

-----

## Tier 2 — Categorical Only, eQTL Noisy

Genes with CPIC Level A actionable evidence but unreliable eQTL signal for kinetic prediction. Predictions use the PGx-categorical phenotype only — no eQTL refinement is applied. The continuous mapping function is bypassed for these genes.

### Tier 2 pairs

|Gene   |Drug                           |Phenotype                               |Expected effect                                 |Tier 2 pass criterion                                                                                                         |
|-------|-------------------------------|----------------------------------------|------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
|CYP2C19|clopidogrel       |PM / IM / NM / RM / UM                  |Reduced active metabolite exposure in PM (species observed: active metabolite, routed via Sisyphus prodrug v2)|Categorical phenotype assignment matches CPIC table for ≥ 95% of holdout individuals; predicted PM/NM AUC ratio within 0.3–0.7|
|CYP2C9 |warfarin          |*1/*1, *1/*2, *1/*3, *2/*2, *2/*3, *3/*3|Reduced S-warfarin clearance in variant carriers (species observed: S-warfarin enantiomer)|Categorical phenotype assignment matches CPIC table; *3/*3 vs *1/*1 predicted CL ratio within 0.1–0.3                         |

### Why categorical only

- **CYP2C19**: The actionable pharmacogenomic information is captured almost entirely by star-allele assignment, and clopidogrel’s active metabolite requires routing through Charon’s prodrug activation layer. Adding eQTL noise on top would degrade rather than improve prediction.
- **CYP2C9**: Effect sizes for clinical CL are dominated by *2 and *3 missense variants (reduced enzyme activity). Tissue mRNA expression eQTLs explain only a small fraction of inter-individual CL variance. Categorical-only is the more honest model.

### What “Tier 2 pass” excludes

A Tier 2 pass demonstrates that the categorical phenotype pathway is correctly implemented. It does **not** demonstrate that eQTL-derived continuous refinement adds value for these genes. That separate question is not addressed by Tier 2 validation.

-----

## Tier 3 — Acknowledged Gap, Not Modeled

Genes relevant to ADME but for which neither eQTL nor categorical phenotype provides a reliable prediction within GenoADME’s current architecture. Requesting these genes from `genoadme.predict_pk` raises `genoadme.errors.UnsupportedGeneError`.

### Tier 3 genes

|Gene  |Why excluded                                                                                                                                                                                                               |
|------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|CYP2D6|Paralog CYP2D7 confounds GTEx mRNA mapping. Functional variation is dominated by structural variants (gene duplications, deletions, hybrid alleles) that are not reliably called from 1000 Genomes phase 3 short-read WGS. |
|CYP3A4|Well-documented expression-activity discordance. mRNA expression and clinical CL are weakly correlated even when paired data is available; tissue eQTLs explain a small fraction of inter-individual midazolam CL variance.|
|ABCB1 |Transporter activity vs mRNA discordance. The clinical impact of common variants (3435C>T, 2677G>T/A) on substrate disposition has been inconsistent across studies, and tissue eQTL signal is weak.                       |

### Why these are reported, not silently skipped

The honest reporting of acknowledged gaps is what makes Tier 1 results credible. Silently returning the average-patient prediction for CYP2D6 (the most clinically actionable gene in pharmacogenomics) would be a methodological failure disguised as a feature.

-----

## Tier-Change Protocol

If a validation result suggests a tier change after the fact:

1. The change must be logged in [`docs/tier-changes.md`](tier-changes.md) with date, original tier, new tier, the validation result that triggered the move, and a rationale.
1. The change must be disclosed in the preprint Limitations section.
1. All other validation cases must be re-run under the new methodology to demonstrate that the tier change does not retroactively alter other reported results.

A “Tier 1 fail” stays a Tier 1 fail. The pair is not silently demoted to Tier 2 to make Tier 1 look better.

-----

## Validation Drug List Final?

This file is committed to `main` before validation runs. Subsequent additions to the list (e.g., extending Tier 1 to TPMT/thiopurines) require:

1. A separate commit with prefix `tier-change:`.
1. A note in this section explaining what changed and why.
1. A re-run of all prior tier validations to confirm no methodological coupling.

The version of this file used for the first preprint is the version committed at git tag `v0.1.0`.
