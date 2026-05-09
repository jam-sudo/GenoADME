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

## 9. v0.1.0 PK propagation was limited to OATP1B1-mediated substrates — root cause re-attributed and partially mitigated post-Sisyphus PR #32 (v0.3.2)

**Discovered:** 2026-04-29 (commit `133ab1f`). **Root cause re-attributed:** 2026-05-08 after Sisyphus PR #32 merge — the originally-reported mechanism was incomplete.

### 9.1 Original framing (v0.1.0)

The body-graph enzyme-and-transporter abundance scaling that GenoADME drove via Sisyphus's `apply_phenotype_to_graph` propagated to predicted PK only along Sisyphus's Extended Clearance Model (ECM) pathway. The v0.1.0 explanation attributed the non-propagation across non-ECM paths to:

- **Generic CYP-cleared drugs:** Sisyphus's CLint comes from an XGBoost predictor on molecular descriptors. Scaling liver enzyme abundance does not change the predicted CLint and therefore does not change the predicted PK. Empirical: caffeine + CYP1A2 PM moved AUC by 8.5×10⁻¹⁰ (floating-point noise).
- **Prodrugs not in Sisyphus's activation registry:** Without a registry entry, the active species is not produced in simulation. Genotype-driven scaling on the activating enzyme therefore has no path to influence active-species PK.
- **Genes absent from `PHENOTYPE_SCALES` or from `reference_man.yaml`:** NAT2 and UGT1A1, both of which appear in the GenoADME deferred-pairs list, were not represented in Sisyphus's physiology graph or activity-multiplier table at v0.1.0.

This explanation was **partially correct**. The XGBoost-CLint argument applies to generic CYP-cleared drugs that go through `_decompose_clint` on a path that reads molecular descriptors but not enzyme abundance — that part stands.

### 9.2 What v0.1.0 missed (Sisyphus PR #32 root-cause comment, 2026-05-08)

Sisyphus PR #32 (`feat/nat2-ugt1a1-phenotype`, v0.3.2, merged 2026-05-06) ships **a back-solve cancellation fix** that was, in the v0.1.0 / v0.2 codebase, silently nullifying CYP/UGT/NAT phenotype effects — producing ratio = 1.000 *exactly* on EM/IM/PM individuals across non-transporter paths. Per the Sisyphus #31 acknowledgment comment:

> SLCO1B1 was the only working phenotype path because OATP1B1 uses saturable Michaelis-Menten kinetics, not affinity back-solve. The 4.482 AUC ratio you measured for `pravastatin` SLCO1B1 PM was, accordingly, the only phenotype channel actually doing work pre-#32.

So the caffeine + CYP1A2 PM = 8.5×10⁻¹⁰ floating-point-noise observation was *consistent with* the XGBoost-CLint hypothesis, but the *primary* failure mechanism for *all non-transporter phenotype paths* — including any path that *would* have read enzyme abundance — was the back-solve cancellation, not the XGBoost pathway choice. The XGBoost-CLint argument was over-attributed; it was the back-solve fix that re-enables the channel.

### 9.3 Post-PR-#32 status (current as of v0.3 closing)

After Sisyphus pin bump to `bf764c5` (PR #33 merge, includes PR #32):

- **NAT2 + UGT1A1:** added to `PHENOTYPE_SCALES` and `reference_man.yaml`. The "genes absent from physiology" subset of v0.1.0 §9 is **resolved**.
- **Back-solve cancellation:** fixed. Non-transporter phenotype paths now propagate effects through to PK rather than producing artifactual ratio = 1.000.
- **Generic CYP-cleared drugs (e.g., warfarin/CYP2C9):** the XGBoost-CLint pathway question stands as a separate concern. Whether the enzyme-abundance signal can now influence CLint via the post-PR-#32 path requires a fresh empirical check (deferred to v0.4 work on the CYP2C9/warfarin Deferred pair).
- **Prodrug routing (clopidogrel, simvastatin acid, irinotecan→SN-38):** still pending Sisyphus's prodrug-activation-registry expansion (Sisyphus #11). Independent of PR #32.

### 9.4 v0.4 acceleration

The v0.4 milestone (Activate Deferred pairs) is partially **un**blocked by PR #32:

- NAT2/isoniazid: physiology-side prerequisites resolved; remaining work is GenoADME-side data (NAT2 marker variant calls, holdout integration). Could be picked up in v0.4 without further Sisyphus changes.
- UGT1A1/irinotecan: physiology-side resolved for UGT1A1 phenotype scaling. The irinotecan → SN-38 prodrug routing is still gated on Sisyphus #11.
- CYP2C19/clopidogrel, CYP2C9/warfarin: still gated on Sisyphus #11 (prodrug registry) and a fresh empirical check of the CLint pathway.

The v0.1.0 user-foot-gun warning ("phenotype-conditional predictions are reliable only where Sisyphus has a propagation path") still applies but the supported set has expanded materially.

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

## 11. PM/EM AUC ratio: ultrathink-driven correction of the v0.2 over-shoot framing (PATH 3 closure)

**Discovered:** 2026-05-03 (under v0.2 framing: "model over-shoot").
**Re-attributed:** 2026-05-09 (under PATH 3: "band-spec citation error, model empirically defensible").

### 11.1 What the evidence actually says (post-meta-analysis, post-PR-32, no override)

|Metric                 |Value  |Empirical reference                                |Result                              |
|-----------------------|-------|---------------------------------------------------|------------------------------------|
|PM/EM AUC ratio        |3.574  |Niemi 2006 men-stratum 95% CI [1.74, 4.91]         |INSIDE empirical CI (central 3.32)  |
|PM/EM Cmax ratio       |2.579  |Niemi 2006 men-stratum 95% CI ~[1.74, 5.91]        |INSIDE empirical CI                 |
|Population AAFE (AUC)  |1.825  |Niemi 0.250 mg·h/L                                 |PASS (≤ 2.0)                        |
|Population AAFE (Cmax) |1.286* |FDA Pravachol 0.045 mg/L                           |PASS (not gated)                    |

\* Under Sisyphus pin `bf764c5` (v0.3.3), no override.

The model's PM/EM AUC ratio output (3.574) is **inside Niemi 2006 men-stratum 95% CI [1.74, 4.91]**, just above the central estimate 3.32. Statistical interpretation: the model is consistent with the only primary single-dose CC-vs-TT N≥4 evidence we can extract. **The model is not measurably wrong against primary data.**

### 11.2 What v0.2 thought was happening (and what was actually happening)

The v0.2-era framing (this section's prior content) attributed the PM/EM AUC ratio over-shoot to "CPIC PM=0.10× scaling compounding through Sisyphus's graph-based PBPK", and proposed (a) per-substrate calibration or (b) band re-spec. The framing assumed the model output was wrong against the [1.4, 2.5] spec band.

Two facts the v0.2 framing missed (surfaced by ultrathink self-audit on 2026-05-09):

1. **The pre-spec band [1.4, 2.5] was based on a flawed citation chain.** The original [`docs/validation-tiers.md`](validation-tiers.md) cited "Niemi 2006 + Pasanen 2007 → 1.6–2.0×". The v0.3 meta-analysis showed: (a) Pasanen 2007 is on atorvastatin / rosuvastatin, *not* pravastatin (a citation error), and (b) Niemi 2006's accessible PM/EM AUC ratio data is the men-stratum 232% (CI 74–391%, ratio [1.74, 4.91]) — the "1.6–2.0×" range does not appear in primary CC-vs-TT N≥4 data and likely traces to review-aggregate summaries that pool over haplotype-equivalents differently.

2. **The model output was empirically defensible against primary data.** The PM/EM AUC ratio 3.574 is inside Niemi 2006 men-stratum 95% CI. The "over-shoot" was over-shoot vs the *spec band*, not over-shoot vs *empirical CI*. The two are the same only if the spec band correctly reflects empirical CI, which it didn't.

### 11.3 Resolution actually taken (PATH 3, 2026-05-09)

Band re-spec from [1.4, 2.5] to **[1.4, 5.0]** under a `tier-change:` commit. The widening is not face-saving — it corrects an identified citation error in the original spec. Direction floor 1.4 preserved; upper bound 5.0 encompasses Niemi 2006 men-stratum 95% CI upper (4.91, rounded). See [`docs/tier-changes.md`](tier-changes.md) entry "Tier 1 PM/EM AUC band re-spec [1.4, 2.5] → [1.4, 5.0] (PATH 3)".

The override mechanism (`PER_SUBSTRATE_PHENOTYPE_SCALES`) added in commit `76738aa` for v0.3 P-ii calibration is **reverted to empty** in PATH 3. The mechanism is preserved as v0.4+ infrastructure (future cases where a per-substrate scale calibration genuinely is the right fix) but not load-bearing for v0.3.

The prior v0.3 closing run (commit `a13d2d9`, override 0.30, PM/EM AUC ratio 1.719) is superseded by the PATH-3 closing (no override, PM/EM AUC ratio 3.574). Both runs preserved in audit chain.

### 11.4 Sparse-evidence caveat (preserved across all versions)

The empirical anchor for the new band [1.4, 5.0] is single-study (Niemi 2006), sex-stratified (men only), N(CC)=3 sub-cohort 95% CI. This is the same evidence base as was used for the rejected v0.2 calibration target. The caveat applies equally: any future tightening of the band, or per-substrate calibration of the model, requires fresh primary evidence with N(CC) substantially > 3 or a documented multi-study pooled CI. Documented in [`docs/v0.3-meta-analysis.md`](v0.3-meta-analysis.md) §2.5 and §2.10.

### 11.5 Why this is in §11 and not §10

§10 is about reproducibility and Sisyphus-pin-driven number shifts. §11 is about: (a) a v0.2-era framing of "model over-shoot" that the v0.3 meta-analysis + PATH 3 ultrathink showed was actually a band-spec citation error, AND (b) the resulting PATH 3 correction. Both will be referenced from the preprint Limitations section so a reader can follow the integrity chain (original framing → identified flaw → correction).

-----

## Adding to this document

New limitations are added with the format:

```
## N. <one-line title>
**Discovered:** YYYY-MM-DD (commit <sha>)
<body>
```

Limitations are not removed; mitigations are noted in-line.