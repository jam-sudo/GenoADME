# Tier 1 Validation Report — SLCO1B1 / pravastatin (20260501)

> Research and educational tool only; not FDA-cleared.

## Run metadata

- git SHA: `e660624b5b5057a5d452fde705a8b8d8fefa2988`
- timestamp (UTC): 2026-05-01T15:46:39+00:00
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
|EM|413|0.0399|0.1613|
|IM|84|0.0521|0.2264|
|PM|3|0.0826|0.4413|

## Pre-specified criteria (docs/validation-tiers.md §Tier 1)

- Population AAFE (AUC) ≤ 2.0: 1.438 → PASS
- PM/EM AUC ratio in [1.4, 2.5]: 2.737 → FAIL
- PM/EM Cmax ratio ≥ 1.3: 2.068 → PASS

**Overall: FAIL/PARTIAL**

## Reference

- Niemi M, et al. Pharmacogenet Genomics. 2006;16(11):801-8
- Reference Cmax: 0.075 mg/L
- Reference AUC: 0.25 mg·h/L
- Reference population: healthy volunteers, predominantly SLCO1B1 NM

## Audit notes

- Cherry-picking audit log: `reports/audit-log.jsonl` line for `purpose="tier 1 validation"` with this git SHA (timestamp `2026-05-01T15:45:41Z`).
- Pre-spec criteria committed in `docs/validation-tiers.md` before this run.
- This run **supersedes** [`reports/validation-tier1-20260429.md`](validation-tier1-20260429.md) per `docs/reporting-standards.md` §5. The earlier run was executed against the same Sisyphus SHA pin (`aef6f8e`) but Sisyphus's working tree carried uncommitted prodrug-v2 WIP that altered the per-individual RNG draw order. This run is from a strictly clean Sisyphus `aef6f8e` checkout and therefore reproducible from any later clone of both repos at their pinned states.
- The 2026-04-29 audit-log entry remains in place (append-only) as evidence the earlier run happened.
- Investigation log: [Sisyphus issue #8 root-cause comment](https://github.com/jam-sudo/Sisyphus/issues/8) for the working-tree-state discovery.

## Corrections

This report supersedes the following metrics from [`reports/validation-tier1-20260429.md`](validation-tier1-20260429.md):

|Metric                       |Superseded value |This report      |Δ change cause                                  |
|-----------------------------|-----------------|-----------------|------------------------------------------------|
|Population mean Cmax (mg/L)  |0.03200          |0.04225          |Sisyphus working-tree RNG-order shift           |
|Population mean AUC (mg·h/L) |0.11345          |0.17387          |Sisyphus working-tree RNG-order shift           |
|AAFE (Cmax)                  |2.344            |1.775            |Same cause; result PASS direction (not gated)   |
|AAFE (AUC)                   |2.204            |**1.438**        |Same cause; result moved FAIL → **PASS**        |
|PM/EM AUC ratio              |2.341            |**2.737**        |Same cause; result moved PASS → **FAIL** (out of [1.4, 2.5] band) |
|PM/EM Cmax ratio             |2.014            |2.068            |Same cause; PASS unchanged                      |
|Overall verdict              |PARTIAL          |PARTIAL          |Verdict unchanged, but failing criterion shifted |

No code change in Sisyphus or GenoADME caused this. The cause is purely working-tree state at the time of the earlier run. The lesson is documented in [`docs/limitations.md` §10](../docs/limitations.md).

-----

## Superseded

This entire report is superseded by [`reports/validation-tier1-20260503.md`](validation-tier1-20260503.md). The Sisyphus pin used for this run (`aef6f8e4...`) is no longer reachable from `origin/main` and was bumped in GenoADME commit `0a2e049` to `9f1680d` (Sisyphus issue #8 closing state). The 2026-05-03 re-run produces:

|Metric                       |Superseded (this report) |New canonical (2026-05-03)|
|-----------------------------|-------------------------|--------------------------|
|Population AAFE (AUC)        |1.438 (PASS)             |1.152 (PASS, deeper inside band)|
|PM/EM AUC ratio              |2.737 (FAIL [1.4, 2.5])  |4.482 (FAIL, more pronounced)   |
|PM/EM Cmax ratio             |2.068 (PASS)             |2.639 (PASS)                    |
|Overall                      |PARTIAL                  |PARTIAL                         |

The verdict is unchanged. The failing criterion is the same. The numbers shift because Sisyphus PR #22 (OATP1B1/ECM double-counting reconciliation) and PR #25 (pravastatin SMILES connectivity fix) both move the pravastatin pipeline. The CPIC PM=0.10× over-shoot on AUC is *more* pronounced under the new Sisyphus calibration — Sisyphus issue #8 closing comment notes this is "community-standard and not a Sisyphus-specific defect" and recommends GenoADME re-anchor population mean Cmax to FDA Pravachol while retaining Niemi 2006 for the PM/EM direction check.

The audit-log entries for both this run (2026-05-01) and the 2026-04-29 run remain in place as evidence those runs occurred.
