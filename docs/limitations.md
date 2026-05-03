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

## 10. v0.1.0 / v0.2 Tier 1 result is PARTIAL — failing criterion shifted across two reproducibility/calibration events

**Discovered:** 2026-04-29 (commit `133ab1f`); rediagnosed 2026-05-01 after the reproducibility audit (§10.2); reconfirmed 2026-05-03 under the post-Sisyphus-#8 calibration (§10.1, current canonical).

### 10.1 Headline result (2026-05-03, current canonical)

The canonical Tier 1 validation run from [`reports/validation-tier1-20260503.md`](../reports/validation-tier1-20260503.md), executed under Sisyphus pin `9f1680d` (issue #8 closing commit — includes PR #22 OATP1B1/ECM reconciliation, PR #25 pravastatin SMILES fix, PR #28 digoxin SMILES fix):

|Criterion                                  |Threshold |Observed |Result|
|-------------------------------------------|----------|---------|------|
|Population AAFE (AUC)                      |≤ 2.0     |1.152    |PASS  |
|PM/EM AUC ratio                            |[1.4, 2.5]|4.482    |FAIL  |
|PM/EM Cmax ratio                           |≥ 1.3     |2.639    |PASS  |

Two of three criteria pass. The **failing criterion is the PM/EM AUC ratio over-shoot** (4.482 outside the [1.4, 2.5] band). Under the post-Sisyphus-#8 calibration the AAFE criterion is now comfortably inside its band (1.152 vs 2.0 threshold) — Sisyphus's OATP1B1/ECM reconciliation closed the population-mean-magnitude gap that drove the 2026-04-29 AAFE FAIL. The PM/EM AUC ratio over-shoot is *more pronounced* than under the prior Sisyphus state (was 2.737 at pin `aef6f8e`, now 4.482 at pin `9f1680d`).

Sisyphus issue #8 closing comment diagnosed the residual gap: PM AUC is over-predicted (0.81× vs Niemi clinical) while EM AUC is under-predicted (1.71× vs Niemi clinical) — this is *not* a constant-fold bias, so no single scaling parameter can close both ends. The closing comment attributes the over-shoot to "CPIC PM activity scaling (0.10×) may be too aggressive for AUC; this would need separate investigation but is community-standard so not a Sisyphus-specific defect."

Resolution paths:

- **(R1) Re-anchor the population-mean Cmax reference to FDA Pravachol label** (0.045 mg/L) per Sisyphus #8 closing recommendation, while retaining Niemi 2006 for the PM/EM ratio direction check. This reflects the empirical reality that FDA's large-cohort regulatory dataset and Niemi 2006's N=6 EM cohort cannot be satisfied by a single-knob calibration. Logged in [`docs/tier-changes.md`](tier-changes.md).
- **(R2) Investigate CPIC PM=0.10× scale appropriateness** for AUC-level metrics in graph-based PBPK models. This is a v0.3 work item — the CPIC scale is community-standard, so the investigation question is whether GenoADME's PM/EM ratio band itself was set with insufficient appreciation of how the 0.10× compounds through Sisyphus's graph layer. See v0.3 milestone for scope.
- **(R3) Document the PM/EM AUC over-shoot as a known limitation** until R2 resolves. The PM/EM Cmax ratio still passes, the AAFE PASSES, and the *direction* of the SLCO1B1 phenotype effect is correctly captured (PM > IM > EM). v0.2 closing accepts the PARTIAL verdict explicitly rather than tuning the band post-hoc.

### 10.2 Reproducibility audit (the 2026-04-29 numbers were not strictly reproducible)

The original 2026-04-29 Tier 1 validation reported AAFE FAIL + PM/EM PASS. The 2026-05-01 re-run from a strictly clean Sisyphus `aef6f8e` checkout produces AAFE PASS + PM/EM AUC FAIL — *the failing criterion shifted*.

Root cause: at the time of the 2026-04-29 run, Sisyphus's working tree carried uncommitted prodrug-v2 WIP. That WIP altered the per-individual RNG draw order during `graph.sample(rng)` (one fewer rng.sample call per ProdrugActivationEdge), shifting deterministic numerical outputs even though the SLCO1B1/pravastatin code path itself was unchanged. The audit-log captured `git_sha` (HEAD at query time) but not the working-tree state, so the original record is *technically* truthful but not strictly reproducible.

The WIP was eventually merged into Sisyphus `main` via PR #7, but in slightly different form, so even a later checkout of the prodrug-v2 branch HEAD does not reproduce the 2026-04-29 numbers exactly.

**Lesson:** for strict reproducibility, validation must execute from a clean working tree, and the audit chain should record `git_sha` *plus* a working-tree-clean assertion. This is now enforced by the supersession block in [`reports/validation-tier1-20260429.md`](../reports/validation-tier1-20260429.md), the [Corrections section in the 2026-05-01 report](../reports/validation-tier1-20260501.md#corrections), and — codified in code — the `worktree_clean` field plus the `WorkingTreeNotCleanError` gate in [`genoadme.audit.log_query`](../src/genoadme/audit.py) (GenoADME issue #1, commit `013d17d`). Both the 2026-05-03 canonical run and any future tier-purpose run cannot now log an audit entry from a dirty tree without an explicit `allow_dirty=True` opt-in.

### 10.3 Sample-size constraint (unchanged)

The PM cohort size (n=3) widens the implicit CI on the PM/EM ratios — the result is directionally consistent but underpowered for tight magnitude inference. Rotating the holdout to enrich for EUR ancestry would inflate PM count but contaminate the holdout for any future ancestry-stratified analysis (so the rotation is not done; the n=3 limitation is reported as-is).

-----

## 11. PM/EM AUC ratio over-shoot under graph-compounded CPIC scaling

**Discovered:** 2026-05-03 (commit *to be filled at commit time* — `tier-change:` Tier 1 reference re-anchor).

### 11.1 Empirical signal

Under Sisyphus pin `9f1680d` (issue #8 closing state), the GenoADME holdout produces:

|Metric                 |Value  |Niemi 2006 reference        |Result                                |
|-----------------------|-------|----------------------------|--------------------------------------|
|PM/EM AUC ratio        |4.482  |~2.0 (PM 0.500 / EM 0.250)  |FAIL band [1.4, 2.5] (over-shoot)     |
|PM/EM Cmax ratio       |2.639  |~2.6 (PM 0.195 / EM 0.075)  |PASS gate ≥ 1.3 (direction correct)   |
|Population AAFE (AUC)  |1.152  |Niemi 0.250 mg·h/L          |PASS (≤ 2.0)                          |
|Population AAFE (Cmax) |1.131* |FDA Pravachol 0.045 mg/L    |PASS but not gated (anchor reasoning) |

\* AAFE Cmax against FDA: pred 0.0509 / FDA 0.045 = 1.131. Against Niemi 0.075 the same prediction yields 1.474. The two-anchor reporting follows from the [`docs/validation-tiers.md`](validation-tiers.md) §"Reference anchoring" rationale.

### 11.2 Mechanism

Sisyphus issue #8 closing comment diagnoses the over-shoot:

> PM AUC is over-predicted (0.81×) while EM AUC is under-predicted (1.71×) — this is **not** a constant-fold systematic bias and is therefore inconsistent with a single scaling-parameter fix... CPIC PM activity scaling (0.10×) may be too aggressive for AUC; this would need separate investigation but is community-standard so not a Sisyphus-specific defect.

The CPIC PM = 0.10× activity multiplier is published per-enzyme-or-transporter and is community-standard for *isolated phenotype-effect* calculations. Applied to a graph-based PBPK model where the OATP1B1 abundance enters multiple coupled clearance terms (uptake, sinusoidal efflux, hepatocellular partition), the same 0.10× compounds beyond the published per-enzyme effect. The 4.48× PM/EM AUC ratio observed here is consistent with this compounding hypothesis.

### 11.3 Resolution path

This is a v0.3 work item. Two non-exclusive directions:

- **(11.3a) Per-substrate CPIC scale calibration.** Investigate whether the CPIC 0.10× scale should be replaced by a per-substrate multiplier when applied through a graph-compounded model. Open-data study-level meta-analysis (Niemi 2006 + Pasanen 2007 + later SLCO1B1 cohorts) could fit a per-substrate effective scale such that the graph-compounded PM/EM AUC matches the clinical mid-band.
- **(11.3b) Re-spec the [1.4, 2.5] PM/EM AUC band.** Only after (11.3a) shows the empirical PM/EM AUC ratio under graph-compounded scaling is *itself* in a band other than [1.4, 2.5], and only via a `tier-change:` commit with a study-meta-analysis citation. Not a face-saving widen; a re-spec backed by evidence.

The PM/EM AUC band is **not** widened in v0.2. The over-shoot is reported as-is.

### 11.4 Why this is in §11 and not §10

§10 is about reproducibility and Sisyphus-pin-driven number shifts. §11 is about a residual model-level architectural mismatch that is *known* to be unsolved at the v0.2 level. The two are distinct and both will be referenced from the preprint Limitations section.

-----

## Adding to this document

New limitations are added with the format:

```
## N. <one-line title>
**Discovered:** YYYY-MM-DD (commit <sha>)
<body>
```

Limitations are not removed; mitigations are noted in-line.