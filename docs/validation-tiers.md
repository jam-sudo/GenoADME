# Validation Tiers (Pre-Specification)

This document is the **commitment record** for GenoADME’s validation strategy. The drug-gene pairs and tier assignments below are committed before any validation run is executed against the 500-individual holdout subset of 1000 Genomes phase 3 ([`docs/holdout-seed.md`](holdout-seed.md)).

If a tier assignment changes after validation has run, the change is logged in [`docs/tier-changes.md`](tier-changes.md) and disclosed in the preprint Limitations section. There is no quiet re-tiering. The full protocol is in [`docs/scientific-integrity.md`](scientific-integrity.md) §1.

**Date of initial commitment:** 2026-04-29
**v0.1.0 spec correction:** 2026-04-29 — see [`docs/tier-changes.md`](tier-changes.md) entry "Pre-validation spec correction (v0.1.0 scope)".
**v0.2 spec re-anchor:** 2026-05-03 — Tier 1 reference anchoring made explicit per Sisyphus issue #8 closing recommendation. Population-mean Cmax anchored to **FDA Pravachol label** (large-cohort regulatory dataset); PM/EM ratios + population-mean AUC retained against **Niemi 2006** (the phenotype-effect reference). See [`docs/tier-changes.md`](tier-changes.md) entry "Tier 1 reference re-anchor (v0.2)" and [`docs/limitations.md`](limitations.md) §11.

-----

## Scope of v0.1.0

**v0.1.0 commits to validating exactly one drug-gene pair end-to-end: SLCO1B1 / pravastatin.** Five additional pairs that appeared in the initial scoping commit (SLCO1B1/simvastatin, NAT2/isoniazid, UGT1A1/irinotecan, CYP2C19/clopidogrel, CYP2C9/warfarin) have been moved to the [Deferred](#deferred--pre-specified-for-v02) section of this document because each requires a Sisyphus capability extension that is out of scope for v0.1.0. The reasoning for the reduction is recorded in [`docs/tier-changes.md`](tier-changes.md); the per-pair blockers are documented below.

The intent of this reduction is to make the v0.1.0 preprint defensible at the level of a single, fully-validated pair rather than partially-validated against five.

-----

## Tier 1 — Mechanistic, Expected Pass

Genes with strong eQTL signal in GTEx liver/intestine **and** CPIC Level A actionable evidence. Predictions use the full hybrid mapping: categorical phenotype (from CPIC star-allele tables) for inter-phenotype variation, plus continuous eQTL refinement for intra-phenotype variation.

### Tier 1 pairs

|Gene   |Drug       |Phenotype                              |Expected effect                                                |Tier 1 pass criterion                                                                            |
|-------|-----------|---------------------------------------|---------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
|SLCO1B1|pravastatin|rs4149056 (*5) carriers vs non-carriers|+60–100% AUC in homozygous Poor Function carriers (Niemi 2006) |Population AAFE (AUC) ≤ 2.0; PM vs EM predicted AUC ratio within 1.4–2.5×; PM vs EM Cmax ratio ≥ 1.3×  |

### Reference anchoring (v0.2 explicit)

|Metric                            |Anchor                                            |Value                                  |Why this anchor                                                                                                                                                                                                                |
|----------------------------------|--------------------------------------------------|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|Population-mean Cmax (gating)     |**FDA Pravachol label** (large-cohort regulatory) |0.045 mg/L                             |Sisyphus issue #8 closing comment recommendation. The FDA value is anchored on a large-cohort regulatory dataset; Sisyphus's pravastatin pipeline (`scripts/calibrate_oatp_abundance_ecm.py`) is anchored against this and passes at FE 1.066. |
|Population-mean AUC (gating)      |**Niemi 2006**                                    |0.250 mg·h/L                           |Niemi 2006 is the canonical SLCO1B1/pravastatin pharmacogenomic reference. The FDA Pravachol label does not publish AUC; Niemi 2006's value is consistent with Pasanen 2007.                                                  |
|PM/EM AUC ratio (gating)          |**Niemi 2006**                                    |~2.0 (PM AUC 0.500 / EM AUC 0.250)     |Niemi 2006 was specifically designed to characterize the SLCO1B1 phenotype effect; its PM/EM ratio is the most direct clinical reference.                                                                                       |
|PM/EM Cmax ratio (gating)         |**Niemi 2006**                                    |~2.6 (PM Cmax 0.195 / EM Cmax 0.075)   |Same as above.                                                                                                                                                                                                                  |
|Population-mean Cmax (secondary)  |Niemi 2006                                        |0.075 mg/L                             |Reported as a secondary calibration check alongside the FDA-gated value, for transparency about the 1.67× Niemi/FDA gap (Niemi 2006 N=6, single study; FDA Pravachol large-cohort).                                            |

**Why two anchors?** The FDA Pravachol Cmax (0.045 mg/L) and Niemi 2006 Cmax (0.075 mg/L) differ by 1.67× at the same dose. No single-knob calibration of Sisyphus can satisfy both. Sisyphus is anchored on FDA, so the population-mean Cmax gate uses FDA; the phenotype-effect references (PM/EM ratios) are pharmacogenomic studies and use Niemi 2006. Both anchors are reported in every validation result for transparency. The 1.67× gap is itself a documented limitation of single-study clinical references — neither anchor is "more correct"; they characterize different things.

### Why pravastatin (and not simvastatin) for v0.1.0

Pravastatin is an **OATP1B1 substrate** that is *not* a prodrug — it is administered and observed as the same chemical species. Sisyphus's existing Extended Clearance Model (ECM) for OATP1B1, validated in `tests/integration/test_slco1b1_phenotype.py` (Sisyphus dependency), correctly propagates SLCO1B1 transporter abundance scaling through hepatic uptake to plasma Cmax/AUC.

Simvastatin, which appeared in the initial scoping, requires routing through a lactone → simvastatin-acid prodrug step that is **not currently registered in Sisyphus's prodrug activation registry**. Without the registry entry, the active species (simvastatin acid, the OATP1B1 substrate) is not produced in the simulation and SLCO1B1 phenotype scaling has no path to influence the predicted PK. Adding simvastatin to the registry is a Sisyphus-side change tracked under [Deferred](#deferred--pre-specified-for-v02).

The pharmacogenomic principle (SLCO1B1 *5 / Poor Function → reduced hepatic uptake → increased plasma exposure) is the same for both statins. v0.1.0 validates the principle on the statin Sisyphus can simulate today.

### Pass criterion rationale

The Tier 1 pass criterion is split into two thresholds to separate *direction* from *magnitude*:

- **PM vs EM Cmax ratio ≥ 1.3×** is the direction gate. It mirrors the gate already in Sisyphus's `tests/integration/test_slco1b1_phenotype.py::test_slco1b1_pm_increases_pravastatin_cmax`. Falling below this means the SLCO1B1-→OATP1B1-→hepatic-uptake-→plasma chain is broken end-to-end; this is a categorical Tier 1 failure.
- **PM vs EM AUC ratio within 1.4–2.5×** is the magnitude gate, sourced from Niemi 2006 and Pasanen 2007 clinical observations of 1.6–2.0× in homozygous Poor Function carriers. The ±0.4× tolerance reflects (a) the published study-to-study variance and (b) the eQTL → mRNA → protein → activity → CL chain noise documented in [`docs/limitations.md`](limitations.md) §1. **Currently exceeded** under the v0.2 (post-Sisyphus #8) calibration — see [`docs/limitations.md`](limitations.md) §11. The band is *not* widened post-hoc; the over-shoot is reported as a known limitation pending v0.3 investigation of CPIC PM=0.10× scale appropriateness for graph-based PBPK models.
- **Population AAFE (AUC) ≤ 2.0** is the population-level fit gate against the Niemi 2006 AUC reference (0.250 mg·h/L). The Cmax AAFE is reported as a secondary check against the FDA Pravachol Cmax reference (0.045 mg/L) but is *not* gated, because Sisyphus's calibration is itself anchored on the FDA Cmax (Sisyphus passes its own ECM gate at FE 1.066) and double-counting that anchor as a GenoADME gate would test Sisyphus's calibration rather than GenoADME's PGx layer.

A run that meets the direction gate but fails the magnitude gate is a Tier 1 partial result — reported as such in the preprint, not silently demoted.

-----

## Tier 2 — Categorical Only, eQTL Noisy

**Empty in v0.1.0.** Both pairs that appeared in the initial scoping (CYP2C19/clopidogrel, CYP2C9/warfarin) have been moved to [Deferred](#deferred--pre-specified-for-v02) because Sisyphus's current pipeline does not propagate phenotype-induced enzyme abundance scaling to PK for either drug type:

- **Generic CYP-cleared drugs (e.g., CYP2C9/warfarin)**: Sisyphus's CLint comes from an XGBoost predictor on molecular descriptors, not from `enzyme abundance × intrinsic activity`. Empirically verified during v0.1.0 skeleton work (caffeine + CYP1A2 PM moved AUC by 8.5×10⁻¹⁰ — pure floating-point noise).
- **Prodrug-activated drugs (e.g., CYP2C19/clopidogrel)**: Clopidogrel is not registered in Sisyphus's prodrug activation registry (which currently contains BH4, GS-441524, tebipenem, R406). Without the registry entry, the active metabolite is not produced and CYP2C19 phenotype scaling has no path to influence active-species PK.

The Tier 2 *methodology* (categorical-only mapping; no eQTL refinement) is preserved in [`src/genoadme/pgx/mapping.py`](../src/genoadme/pgx/mapping.py) and is exercised at the unit-test level. What is deferred is the *end-to-end PK validation* against the holdout, pending the Sisyphus extensions tracked below.

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

## Deferred — Pre-specified for v0.3+

The pairs below were scoped for v0.1.0 but are deferred because each requires a specific Sisyphus capability extension that is itself a multi-commit project. They are listed here (rather than removed) so the public commitment record carries the full roadmap. Promotion of any deferred pair to an active tier requires (a) the listed Sisyphus blocker to be resolved, (b) a `tier-change:` commit per [`docs/commit-discipline.md`](commit-discipline.md) §4, and (c) a re-run of the Tier 1 pravastatin validation to verify no methodological coupling.

The Sisyphus blockers below are tracked under the [Sisyphus v0.3 milestone](https://github.com/jam-sudo/Sisyphus/milestone/2); promotion to active tier here is tracked under the [GenoADME v0.3 milestone](https://github.com/jam-sudo/GenoADME/milestone/2).

|Pair                       |Original tier|Sisyphus blocker for v0.1.0                                                                                                            |Tracking issue                                                                                                                          |
|---------------------------|-------------|---------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
|SLCO1B1 / simvastatin      |Tier 1       |Simvastatin (lactone) → simvastatin acid prodrug routing not in `data/sbi/prodrug_activation_registry.json`. The OATP1B1 substrate is the acid form. |[Sisyphus#11](https://github.com/jam-sudo/Sisyphus/issues/11)                                                                           |
|NAT2 / isoniazid           |Tier 1       |NAT2 not in `sisyphus.predict.phenotype.PHENOTYPE_SCALES`; NAT2 not represented in `data/physiology/reference_man.yaml` liver enzymes; isoniazid CLint not routed through NAT2 abundance.|[Sisyphus#10](https://github.com/jam-sudo/Sisyphus/issues/10)                                                                           |
|UGT1A1 / irinotecan        |Tier 1       |UGT1A1 not in `PHENOTYPE_SCALES` / `reference_man.yaml`. Irinotecan → SN-38 prodrug routing (carboxylesterase-mediated activation) not in the prodrug registry. SN-38 → glucuronide elimination via UGT1A1 not modeled. |[Sisyphus#10](https://github.com/jam-sudo/Sisyphus/issues/10) + [Sisyphus#11](https://github.com/jam-sudo/Sisyphus/issues/11)            |
|CYP2C19 / clopidogrel      |Tier 2       |Clopidogrel not in the prodrug activation registry. Active metabolite generation requires CYP2C19-mediated activation routing.        |[Sisyphus#11](https://github.com/jam-sudo/Sisyphus/issues/11)                                                                           |
|CYP2C9 / warfarin          |Tier 2       |Sisyphus's CLint is XGBoost-predicted from molecular descriptors and does not read enzyme abundance for non-ECM substrates; phenotype scaling has no PK propagation path.|*no tracking issue yet — generic CYP-cleared substrates require an architectural change beyond v0.3 scope*                            |

These blockers are specific Sisyphus issues, not GenoADME design choices. Resolving any of them is independent of the rest.

-----

## Tier-Change Protocol

If a validation result suggests a tier change after the fact:

1. The change must be logged in [`docs/tier-changes.md`](tier-changes.md) with date, original tier, new tier, the validation result that triggered the move, and a rationale.
1. The change must be disclosed in the preprint Limitations section.
1. All other validation cases must be re-run under the new methodology to demonstrate that the tier change does not retroactively alter other reported results.

A “Tier 1 fail” stays a Tier 1 fail. The pair is not silently demoted to Tier 2 to make Tier 1 look better.

-----

## Validation Drug List Final?

This file is committed to `main` before validation runs. Subsequent additions to the active tiers (e.g., promoting a Deferred pair to Tier 1) require:

1. A separate commit with prefix `tier-change:`.
1. A note in this section explaining what changed and why.
1. A re-run of all prior tier validations to confirm no methodological coupling.

The version of this file used for the first preprint is the version committed at git tag `v0.1.0`.
