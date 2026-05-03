# Tier Changes Log

This file is the **append-only audit log** for any post-validation change to a drug-gene tier assignment. Tier assignments are pre-specified in [`docs/validation-tiers.md`](validation-tiers.md) before validation runs.

The protocol that requires entries here is in [`docs/scientific-integrity.md`](scientific-integrity.md) §1 and the commit format is in [`docs/commit-discipline.md`](commit-discipline.md) §4.

The intent of this file is twofold:

1. Make any tier change visible from `git log --follow docs/tier-changes.md` alone.
1. Force an explicit disclosure step before a tier change is allowed to influence the headline numbers reported in the preprint.

-----

## How to add an entry

Append a new section to the bottom of this file (do **not** edit prior entries). One section per tier change. Every entry follows this template:

```markdown
## YYYY-MM-DD — <gene>/<drug>: Tier <X> → Tier <Y>

**Commit:** `<sha>`
**Trigger:** <which validation run, with report path>
**Old tier:** <X> (mapping methodology used)
**New tier:** <Y> (mapping methodology now applied)
**Rationale:** <2–4 sentences explaining why the tier change is honest rather than face-saving>
**Re-run scope:** <which other tier validations were re-run as a consequence>
**Disclosure:** <preprint section / README section that notes this change>
```

If a tier change requires re-running other validation cases, the resulting reports are listed under **Re-run scope**. The tier change is not considered “closed” until those reports exist in `reports/`.

-----

## Entries

### 2026-04-29 — Pre-validation spec correction (v0.1.0 scope reduction)

**Type:** Pre-validation spec correction. The formal "Tier-Change Protocol" in [`docs/validation-tiers.md`](validation-tiers.md) and [`docs/scientific-integrity.md`](scientific-integrity.md) §1 applies to changes *after* validation has been run; this entry documents a change made *before* any validation run, but is logged here for traceability and to keep the discipline equally strict regardless of timing.

**Commit:** *to be filled at commit time*
**Trigger:** Empirical investigation during v0.1.0 skeleton implementation (no validation runs executed). Two findings, both verified by direct experimentation against the pinned Sisyphus build (`aef6f8e`):

1. Sisyphus's top-level `predict()` did not auto-load the OATP1B1 Extended Clearance Model. Calling `predict(pravastatin, phenotypes={"SLCO1B1": "PM"})` produced AUC ratio PM/EM = 1.000 — the SLCO1B1 phenotype scaling had no path to influence PK at the top-level API. Lower-level building blocks (`build_drug_on_graph(..., transporter_kinetics=load_oatp1b1_kinetics(...), hepatic_ecm_params=load_hepatic_ecm_params(...))`) propagate the effect correctly, as proven by Sisyphus's existing `tests/integration/test_slco1b1_phenotype.py`.
2. Sisyphus's prodrug activation registry (`data/sbi/prodrug_activation_registry.json`) currently contains four prodrugs: BH4, GS-441524, tebipenem, R406. None of GenoADME's originally-scoped prodrug pairs (clopidogrel, simvastatin, irinotecan→SN-38) is registered. Without registry entries, the active species is not produced and any genotype-driven scaling on the activating enzyme has no PK propagation path.

A third finding (separately documented in [`docs/limitations.md`](limitations.md) §1.1): Sisyphus's CLint for non-ECM substrates is XGBoost-predicted from molecular descriptors and does not read enzyme abundance. Phenotype scaling for generic CYP-cleared drugs (warfarin/CYP2C9, caffeine/CYP1A2) therefore does not propagate to PK. Verified: caffeine + CYP1A2 PM moved AUC by 8.5×10⁻¹⁰.

**Old scope (committed 2026-04-29 in the initial spec):**
- Tier 1: SLCO1B1/simvastatin, NAT2/isoniazid, UGT1A1/irinotecan
- Tier 2: CYP2C19/clopidogrel, CYP2C9/warfarin
- Tier 3 (unchanged): CYP2D6, CYP3A4, ABCB1

**New scope (v0.1.0):**
- Tier 1: SLCO1B1/pravastatin (one pair — substituted from simvastatin because pravastatin is not a prodrug and Sisyphus's existing OATP1B1 ECM machinery validates its PGx effect end-to-end at the lower-level API)
- Tier 2: empty
- Tier 3 (unchanged): CYP2D6, CYP3A4, ABCB1
- Deferred (pre-specified for v0.2+): the five pairs above, each with the specific Sisyphus blocker recorded in [`docs/validation-tiers.md`](validation-tiers.md) §Deferred.

**Rationale:** The original spec assumed Sisyphus's `predict()` would propagate phenotype scaling end-to-end for any pre-specified pair. Empirical investigation showed this is true only for OATP1B1-routed drugs whose ECM is *already* loaded — pravastatin in the Sisyphus integration test path, but not via top-level `predict()` and not for any prodrug, NAT2-cleared, UGT1A1-cleared, or generic CYP-cleared drug. A single fully-validated pair is more defensible in the v0.1.0 preprint than five partially-validated ones. The original five pairs remain pre-specified targets for v0.2+ rather than being silently dropped.

**Re-run scope:** No prior validation runs to re-run — this correction precedes any holdout query. The cherry-picking audit log (`reports/audit-log.jsonl`) is empty as of this entry.

**Disclosure:** This change is the dominant content of the v0.1.0 [`README.md`](../README.md) "Validation strategy" section and is referenced from [`docs/limitations.md`](limitations.md) §9. The preprint Limitations and Methods sections will both reference this entry.

-----

### 2026-05-01 — Reproducibility audit of the 2026-04-29 Tier 1 validation run

**Type:** Audit-grade correction. Not a tier change in the strict sense (no drug-gene pair moves between tiers). Logged here for traceability of the integrity record.

**Commit:** *to be filled at commit time*
**Trigger:** Investigation of the 2026-04-29 Tier 1 PARTIAL result while sizing the v0.2 calibration work surfaced that the original numbers were not strictly reproducible from the committed Sisyphus SHA pin. Sisyphus's working tree at the time of the 2026-04-29 run carried uncommitted prodrug-v2 WIP that altered the per-individual RNG draw order. The WIP was eventually merged into Sisyphus `main` (PR #7) but in slightly different form, so even checking out either the pinned `aef6f8e` SHA *or* the `feat/prodrug-activation-v2` branch HEAD does not reproduce the 2026-04-29 numbers.

**Action taken:**

1. Re-ran `genoadme.validate.run_tier1` from a strictly clean Sisyphus `aef6f8e` checkout. New report at [`reports/validation-tier1-20260501.md`](../reports/validation-tier1-20260501.md) and headline JSON at [`reports/headline-metrics-20260501.json`](../reports/headline-metrics-20260501.json).
2. Appended a "Superseded" block to the 2026-04-29 report documenting that its numbers are no longer the canonical record. The audit-log entry from 2026-04-29 was preserved (append-only).
3. Updated the README status line and `docs/limitations.md` §10 to point at the new canonical numbers.

**Headline-criterion shift:**

|Criterion                  |2026-04-29 result |2026-05-01 result |
|---------------------------|------------------|------------------|
|Population AAFE (AUC)      |2.204 (FAIL)      |1.438 (**PASS**)  |
|PM/EM AUC ratio            |2.341 (PASS)      |2.737 (**FAIL**)  |
|PM/EM Cmax ratio           |2.014 (PASS)      |2.068 (PASS)      |
|Overall                    |PARTIAL           |PARTIAL           |

The overall verdict (PARTIAL) is unchanged but the *failing criterion shifted*. This rediagnoses the v0.2 work scope: the gap is the PM/EM ratio over-shoot, not the AAFE underprediction.

**Rationale (why this is logged here):** the audit chain integrity required the original record to stay (it does — the 2026-04-29 audit-log entry is untouched). But a reader following the 2026-04-29 numbers without seeing this entry would draw the wrong conclusion about which v0.2 work is needed. The honest disclosure is to mark the supersession in this log, in `docs/limitations.md` §10, in the report file itself, and in `README.md`.

**Lesson:** for the future, validation runs must execute from a clean working tree, and the audit chain should add a working-tree-clean assertion alongside `git_sha`. This is a v0.2+ improvement to `genoadme.audit.log_query`.

-----

### 2026-05-03 — Tier 1 reference re-anchor (v0.2)

**Type:** Tier-1 reference anchoring change. No drug-gene pair moves between tiers and no pass-criterion threshold changes. The change is to which clinical reference value backs each metric.

**Commit:** *to be filled at commit time*
**Trigger:** Sisyphus issue #8 closing comment ([`9f1680d`](https://github.com/jam-sudo/Sisyphus/commit/9f1680d), 2026-05-02). After PR #22 (OATP1B1/ECM reconciliation) + PR #25 (pravastatin SMILES connectivity fix), Sisyphus is calibrated to FDA Pravachol Cmax (0.045 mg/L), passing its ECM gate at FE 1.066. The 2026-05-03 GenoADME re-run under that pin (`reports/validation-tier1-20260503.md`) reproduced the closing-comment direction: AAFE deeper inside band, PM/EM AUC ratio over-shoot more pronounced.

**Old anchoring (implicit, v0.1.0):**
- All Tier 1 metrics scored against Niemi 2006 (Cmax 0.075 mg/L, AUC 0.250 mg·h/L, PM/EM AUC ~2.0, PM/EM Cmax ~2.6).
- Single anchor was a v0.1.0 simplification, not a deliberate scientific choice.

**New anchoring (explicit, v0.2):**
- Population-mean Cmax (gating) → **FDA Pravachol** 0.045 mg/L.
- Population-mean AUC (gating) → Niemi 2006 0.250 mg·h/L (FDA does not publish AUC).
- PM/EM AUC ratio (gating) → Niemi 2006 ~2.0.
- PM/EM Cmax ratio (gating) → Niemi 2006 ~2.6.
- Population-mean Cmax against Niemi 2006 (0.075 mg/L) → **secondary** report, transparency check on the 1.67× Niemi/FDA gap.

**Pass criterion thresholds:** unchanged. Population AAFE (AUC) ≤ 2.0; PM/EM AUC ratio in [1.4, 2.5]; PM/EM Cmax ratio ≥ 1.3.

**Rationale:** Sisyphus is FDA-anchored (large-cohort regulatory dataset), so GenoADME's population-mean Cmax gate is most informative against the same reference — gating against Niemi 2006 (N=6) would test Sisyphus's calibration choice rather than GenoADME's PGx layer. PM/EM ratios are pharmacogenomic phenotype-effect references, and Niemi 2006 was specifically designed to characterize that — so those gates retain Niemi 2006. The 1.67× gap between FDA and Niemi Cmax is itself a published-reference limitation, not a model defect; reporting both anchors makes the gap visible rather than hiding it.

**Re-run scope:** `reports/validation-tier1-20260503.md` is the v0.2 canonical run. Same numerical outputs (deterministic from Sisyphus pin + seed + holdout) score against the new reference table. The 20260503 report and `headline-metrics-20260503.json` are amended in this commit to include both anchors. No simulator re-run is needed because the simulation is independent of the reference table.

**Headline-criterion shift under new anchoring:**

|Criterion                       |2026-05-03 result vs old anchor (Niemi)|2026-05-03 result vs new anchor table |Shift                                    |
|--------------------------------|----------------------------------------|-----------------------------------------|-----------------------------------------|
|Population AAFE (Cmax) — secondary  |1.474 (vs Niemi 0.075)                |1.131 (vs FDA 0.045)                     |Reported, not gated; FDA shows tighter fit|
|Population AAFE (AUC) — gating  |1.152 (vs Niemi 0.250)                  |1.152 (unchanged — Niemi)                |No shift                                 |
|PM/EM AUC ratio — gating        |4.482                                   |4.482                                    |No shift; still FAIL band [1.4, 2.5]     |
|PM/EM Cmax ratio — gating       |2.639                                   |2.639                                    |No shift; PASS unchanged                 |
|Overall verdict                 |PARTIAL                                 |PARTIAL                                  |No shift                                 |

The verdict is unchanged. The re-anchor is honest because (a) the old single-anchor choice was an unexamined v0.1.0 simplification; (b) FDA-anchoring on Cmax is the Sisyphus calibration's actual reference; (c) the PM/EM ratio FAIL is *more* visible under the explicit anchoring (the over-shoot is real and is the v0.2 known limitation), not less.

**Disclosure:** This change is documented in:
- [`docs/validation-tiers.md`](validation-tiers.md) §"Reference anchoring (v0.2 explicit)" — added.
- [`docs/limitations.md`](limitations.md) §11 — added; details the PM/EM AUC over-shoot mechanism and v0.3 resolution path.
- [`README.md`](../README.md) status line — already updated to point at the 2026-05-03 canonical report.
- [`reports/validation-tier1-20260503.md`](../reports/validation-tier1-20260503.md) — Reference section amended to include both anchors.
- [`reports/headline-metrics-20260503.json`](../reports/headline-metrics-20260503.json) — `reference` field amended to include both anchors.

-----

*No further tier changes recorded.*

The pre-specified tiers committed in [`docs/validation-tiers.md`](validation-tiers.md) are still the active assignments as of the latest commit on `main`.