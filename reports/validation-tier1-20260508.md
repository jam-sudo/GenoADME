# Tier 1 Validation Report — SLCO1B1 / pravastatin (20260508)

> Research and educational tool only; not FDA-cleared.

## Run metadata

- git SHA: `90a2f0a48b45c7bef6cbd69c133fb9ea4b690e28`
- timestamp (UTC): 2026-05-08T18:16:55+00:00
- holdout: `data/genotype/holdout500_ids.txt`
- calls: `data/genotype/slco1b1_rs4149056_holdout.tsv`
- n individuals: 500
- drug: pravastatin (`CC[C@@H](C)C(=O)O[C@@H]1C[C@H](C=C2[C@@H]1CC[C@H]([C@@H]2CC[C@H](C[C@H](CC(=O)O)O)O)C)O`)
- dose: 40.0 mg PO

## Phenotype distribution

- EM: 413
- IM: 84
- PM: 3

## Per-phenotype mean PK

|Phenotype|n|Mean Cmax (mg/L)|Mean AUC (mg·h/L)|
|---------|--|----------------|------------------|
|EM|413|0.0333|0.1282|
|IM|84|0.0417|0.1684|
|PM|3|0.0859|0.4583|

## Pre-specified criteria (docs/validation-tiers.md §Tier 1)

- Population AAFE (AUC) ≤ 2.0: 1.825 → PASS
- PM/EM AUC ratio in [1.4, 2.5]: 3.574 → FAIL
- PM/EM Cmax ratio ≥ 1.3: 2.579 → PASS

**Overall: FAIL/PARTIAL**

## Reference

Per the v0.2 reference anchoring made explicit in [`docs/validation-tiers.md`](../docs/validation-tiers.md) §"Reference anchoring" (`tier-change:` 2026-05-03, commit f96b5fc):

|Metric                            |Anchor                |Value             |Result vs anchor             |
|----------------------------------|----------------------|------------------|-----------------------------|
|Population-mean Cmax (gating)     |FDA Pravachol label   |0.045 mg/L        |0.0350 mg/L → AAFE 1.286 PASS (not currently in code; reported manually) |
|Population-mean AUC (gating)      |Niemi 2006            |0.250 mg·h/L      |0.137 mg·h/L → AAFE 1.825 PASS (≤ 2.0)                                   |
|PM/EM AUC ratio (gating)          |Niemi 2006            |~2.0 (PM 0.500 / EM 0.250) |3.574 → FAIL band [1.4, 2.5]                                       |
|PM/EM Cmax ratio (gating)         |Niemi 2006            |~2.6 (PM 0.195 / EM 0.075) |2.579 → PASS gate ≥ 1.3                                            |
|Population-mean Cmax (secondary)  |Niemi 2006            |0.075 mg/L        |0.0350 mg/L → AAFE 2.141 (transparency check; auto-computed in JSON)     |

References:

- FDA Pravachol Pravastatin Sodium Tablets full prescribing information (large-cohort regulatory dataset).
- Niemi M, et al. Pharmacogenet Genomics. 2006;16(11):801-8.

The auto-generated `aafe_cmax` field in `headline-metrics-20260508.json` (= 2.141) is computed against Niemi 0.075 (the legacy single-anchor in `validate.py`'s `TIER1_REFERENCE`). Per the v0.2 tier-change, the gating Cmax anchor is FDA 0.045 (AAFE 1.286, PASS); the Niemi 0.075 value is retained as a transparency check on the 1.67× Niemi/FDA gap. A follow-up `feat:` commit will update `validate.py` to emit both AAFE values explicitly; this baseline run is reported with the manual-recompute disclosure.

## Audit notes

- Cherry-picking audit log: `reports/audit-log.jsonl` line for `purpose="tier 1 validation"` with this git SHA (`90a2f0a48b45c7bef6cbd69c133fb9ea4b690e28`).
- Pre-spec criteria committed in `docs/validation-tiers.md` before this run.
- This is the first GenoADME validation run under Sisyphus pin `bf764c5` (v0.3.3 / PR #33 merge — includes PR #32 NAT2/UGT1A1 + back-solve cancellation fix, and the new `phenotype_scale_overrides` API hook). The Sisyphus working tree was clean detached HEAD at `bf764c5` for this run; the audit-log entry's `deps.sisyphus.worktree_clean = true` confirms strict reproducibility.
- This run **supersedes** [`reports/validation-tier1-20260503.md`](validation-tier1-20260503.md) per `docs/reporting-standards.md` §5.
- Audit-log entries for all prior runs (2026-04-29, 2026-05-01, 2026-05-03) remain in place (append-only) as evidence those runs occurred.
- This baseline does **not** apply `phenotype_scale_overrides`. The v0.3 P-ii calibration commit will follow — calibrating the SLCO1B1 PM scale to bring PM/EM AUC ratio toward Niemi 2006 men-stratum 95% CI lower bound (~1.74) per `docs/v0.3-meta-analysis.md`.

## Corrections

This report supersedes the following metrics from [`reports/validation-tier1-20260503.md`](validation-tier1-20260503.md):

|Metric                       |Superseded value |This report      |Δ change cause                                              |
|-----------------------------|-----------------|-----------------|------------------------------------------------------------|
|Population mean Cmax (mg/L)  |0.05088          |0.03503          |Sisyphus pin `9f1680d` → `bf764c5` (PR #32 back-solve fix)  |
|Population mean AUC (mg·h/L) |0.21698          |0.13696          |Same                                                        |
|AAFE Cmax (vs Niemi 0.075)   |1.474            |2.141            |Same; not gated metric                                      |
|AAFE AUC (vs Niemi 0.250)    |**1.152**        |**1.825**        |Same; both PASS but tighter margin to threshold 2.0         |
|PM/EM AUC ratio              |**4.482**        |**3.574**        |Same; result still FAIL but moved 20% toward band [1.4, 2.5]|
|PM/EM Cmax ratio             |2.639            |2.579            |Same; PASS unchanged                                        |
|Overall verdict              |PARTIAL          |PARTIAL          |Verdict unchanged; failing criterion still PM/EM AUC ratio  |

The PM/EM AUC ratio over-shoot is *less pronounced* under PR #32's back-solve cancellation fix — the prior 4.482 was inflated by the non-transporter phenotype paths producing exactly ratio = 1.000 on EM/IM/PM individuals (silently nullified). With the back-solve fix, the SLCO1B1 effect now propagates without artifactual amplification. The residual gap from 3.574 to band [2.5] upper is what the v0.3 `phenotype_scale_overrides` calibration will close.

No code change in GenoADME. The cause is purely Sisyphus pin `9f1680d` → `bf764c5`. The lesson reinforces `docs/limitations.md` §10.2: pin SHA captures HEAD state, not working-tree state; reproducibility requires both. The audit hook (GenoADME issue #1) is functioning as designed — this run's audit-log entry records the new `bf764c5` Sisyphus SHA + clean worktrees on both sides.
