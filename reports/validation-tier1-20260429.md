# Tier 1 Validation Report — SLCO1B1 / pravastatin (20260429)

> Research and educational tool only; not FDA-cleared.

## Run metadata

- git SHA: `e4308e2c78d6e01f690a17691c9e94bc6bd34476`
- timestamp (UTC): 2026-04-29T20:38:19+00:00
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
|EM|413|0.0303|0.1062|
|IM|84|0.0394|0.1442|
|PM|3|0.0610|0.2486|

## Pre-specified criteria (docs/validation-tiers.md §Tier 1)

- Population AAFE (AUC) ≤ 2.0: 2.204 → FAIL
- PM/EM AUC ratio in [1.4, 2.5]: 2.341 → PASS
- PM/EM Cmax ratio ≥ 1.3: 2.014 → PASS

**Overall: FAIL/PARTIAL**

## Reference

- Niemi M, et al. Pharmacogenet Genomics. 2006;16(11):801-8
- Reference Cmax: 0.075 mg/L
- Reference AUC: 0.25 mg·h/L
- Reference population: healthy volunteers, predominantly SLCO1B1 NM

## Audit notes

- Cherry-picking audit log: `reports/audit-log.jsonl` line for `purpose="tier 1 validation"` with this git SHA.
- Pre-spec criteria committed in `docs/validation-tiers.md` before this run.

## Corrections

*None at time of first publication.*
