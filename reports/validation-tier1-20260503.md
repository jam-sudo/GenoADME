# Tier 1 Validation Report — SLCO1B1 / pravastatin (20260503)

> Research and educational tool only; not FDA-cleared.

## Run metadata

- git SHA: `0a2e049f6160927498606cc283a7949e39581f4d`
- timestamp (UTC): 2026-05-03T22:37:46+00:00
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
|EM|413|0.0476|0.1968|
|IM|84|0.0643|0.2926|
|PM|3|0.1256|0.8818|

## Pre-specified criteria (docs/validation-tiers.md §Tier 1)

- Population AAFE (AUC) ≤ 2.0: 1.152 → PASS
- PM/EM AUC ratio in [1.4, 2.5]: 4.482 → FAIL
- PM/EM Cmax ratio ≥ 1.3: 2.639 → PASS

**Overall: FAIL/PARTIAL**

## Reference

- Niemi M, et al. Pharmacogenet Genomics. 2006;16(11):801-8
- Reference Cmax: 0.075 mg/L
- Reference AUC: 0.25 mg·h/L
- Reference population: healthy volunteers, predominantly SLCO1B1 NM

## Audit notes

- Cherry-picking audit log: `reports/audit-log.jsonl` line for `purpose="tier 1 validation"` with this git SHA (timestamp `2026-05-03T22:36:45Z`).
- Pre-spec criteria committed in `docs/validation-tiers.md` before this run.
- This is the first GenoADME validation run under Sisyphus pin `9f1680d` (issue #8 closing state — includes PR #22 OATP1B1/ECM reconciliation, PR #25 pravastatin SMILES connectivity fix, PR #28 digoxin SMILES fix). The Sisyphus working tree was a clean detached HEAD at `9f1680d` for this run; the audit-log entry's `deps.sisyphus.worktree_clean = true` confirms strict reproducibility.
- This run **supersedes** [`reports/validation-tier1-20260501.md`](validation-tier1-20260501.md) per `docs/reporting-standards.md` §5. The earlier run was executed against Sisyphus pin `aef6f8e4...` which is no longer reachable from `origin/main` (see `pyproject.toml` comment for context).
- Audit-log entries for both prior runs (2026-04-29 and 2026-05-01) remain in place (append-only) as evidence those runs occurred.

## Corrections

This report supersedes the following metrics from [`reports/validation-tier1-20260501.md`](validation-tier1-20260501.md):

|Metric                       |Superseded value |This report      |Δ change cause                                             |
|-----------------------------|-----------------|-----------------|-----------------------------------------------------------|
|Population mean Cmax (mg/L)  |0.04225          |0.05088          |Sisyphus pin `aef6f8e` → `9f1680d` (PR #22 + #25 + #28)    |
|Population mean AUC (mg·h/L) |0.17387          |0.21698          |Same                                                       |
|AAFE (Cmax)                  |1.775            |1.474            |Same; PASS direction (not gated)                           |
|AAFE (AUC)                   |1.438            |**1.152**        |Same; result PASS → **PASS** (further inside band)         |
|PM/EM AUC ratio              |2.737            |**4.482**        |Same; result FAIL → **FAIL** (further outside [1.4, 2.5])  |
|PM/EM Cmax ratio             |2.068            |2.639            |Same; PASS unchanged                                       |
|Overall verdict              |PARTIAL          |PARTIAL          |Verdict unchanged; failing criterion still PM/EM AUC ratio |

The PM/EM AUC ratio over-shoot is *more pronounced* under the new Sisyphus calibration. This is consistent with Sisyphus issue #8 closing comment's diagnosis: "PM AUC is over-predicted (0.81×) while EM AUC is under-predicted (1.71×) — this is **not** a constant-fold systematic bias and is therefore inconsistent with a single scaling-parameter fix... CPIC PM activity scaling (0.10×) may be too aggressive for AUC; this would need separate investigation but is community-standard so not a Sisyphus-specific defect."

A separate `tier-change:` commit will follow to (a) re-anchor the population mean Cmax reference to the FDA Pravachol label per Sisyphus #8 closing recommendation while retaining Niemi 2006 for the PM/EM ratio direction check, and (b) document the PM/EM AUC over-shoot as a v0.2 limitation pending CPIC PM scale investigation in v0.3.
