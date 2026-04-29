# Holdout Seed and Individual ID List

> Research and educational tool only; not FDA-cleared.

This document is the canonical record of the **500-individual holdout subset** of 1000 Genomes phase 3 used by GenoADME to produce the population-level metrics reported in the preprint.

The protocol that constrains this file is in [`docs/scientific-integrity.md`](scientific-integrity.md) §2:

- The holdout is sampled **once**.
- The seed and the resulting individual IDs are committed.
- The holdout is **never** used for methodological choices, hyperparameter tuning, or tier selection — only for producing headline metrics.

-----

## Status

**The holdout has not yet been drawn.** As of the latest commit, `genoadme.validate.generate_holdout` has not been implemented and `data/genotype/holdout500_ids.txt` does not exist.

This file is currently a **specification**, not a record. It will be updated to a record (with the actual seed value and the SHA of `holdout500_ids.txt`) by a single commit with prefix `audit:` at the moment the holdout is drawn for the first time. That commit becomes the canonical reference point.

Until that commit lands, no validation run that touches `holdout500_ids.txt` is allowed to publish a number into a `reports/headline-metrics-*.json`.

-----

## Sampling protocol (specification)

When `genoadme.validate.generate_holdout(seed)` is implemented, it will:

1. Read the full 1000 Genomes phase 3 sample manifest (the canonical 2,504-individual list from the public release).
1. Use `numpy.random.default_rng(seed)` to draw 500 individual IDs **without replacement**.
1. Stratify the draw by 1000 Genomes super-population (AFR, AMR, EAS, EUR, SAS) so that the holdout’s super-population proportions match the full 2,504 set within ±1 individual per super-population.
1. Write the resulting IDs, one per line in lexicographic order, to `data/genotype/holdout500_ids.txt`.
1. Write a one-line entry to `reports/audit-log.jsonl` with `purpose: "holdout generation"` and the seed value.

The function is deterministic given the seed and the 1000 Genomes manifest snapshot referenced in `data/genotype/README.md` (to be added when `data/genotype/` is populated).

-----

## Reserved seed value

The canonical seed for the v0.1.0 preprint holdout is reserved as:

```
seed = 42
```

This matches the seed used in the `README.md` reproducibility command (`genoadme validate --tier all --seed 42`).

If for any reason the holdout must be regenerated under a different seed (for example, the 1000 Genomes manifest is found to have been the wrong release), the rotation is logged here as an additional section, **not** as an edit to the seed-42 record. The old holdout’s metrics remain in the `reports/` directory.

-----

## Record format (to be filled at first generation)

When the holdout is first drawn, this section is replaced with concrete values by the same `audit:` commit that creates `data/genotype/holdout500_ids.txt`:

```markdown
## v0.1.0 holdout (drawn YYYY-MM-DD, commit <sha>)

- **Seed:** 42
- **1000G manifest snapshot:** <reference / SHA>
- **Holdout file:** `data/genotype/holdout500_ids.txt`
- **Holdout file SHA-256:** `<hash>`
- **Super-population breakdown:** AFR=NN, AMR=NN, EAS=NN, EUR=NN, SAS=NN
- **First and last IDs (sanity check, lexicographic):** `<first ID> ... <last ID>`
- **Audit log entry:** `reports/audit-log.jsonl` line dated `<timestamp UTC>`
```

The SHA-256 hash exists so that any later `git checkout <sha>` can verify the holdout file was not silently modified.

-----

## What this file is not

- It is **not** a list of individual IDs. The IDs live in `data/genotype/holdout500_ids.txt` once generated. This document records the seed, the protocol, and the file’s integrity hash.
- It is **not** a place to tune the sampling. If the protocol above is found to be wrong before the holdout is drawn, fix the protocol here under `docs:` prefix. After the holdout is drawn, changes to the protocol require regenerating the holdout under a new seed and disclosing the rotation.