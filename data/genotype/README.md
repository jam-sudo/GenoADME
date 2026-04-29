# `data/genotype/`

ADME-gene VCF subsets from **1000 Genomes phase 3** (open data).

## Status

Empty in v0.1.0 skeleton. Files will be added by a single `audit:` commit when the holdout is first drawn (see [`../../docs/holdout-seed.md`](../../docs/holdout-seed.md)).

## What goes here

- One VCF (or VCF-subset) per ADME gene, restricted to variants on the gene plus a configurable flanking window.
- `holdout500_ids.txt` — the 500 individual IDs drawn for the holdout (one ID per line, lexicographic order).
- A provenance record naming the exact 1000 Genomes phase 3 release (e.g., `1000G_phase3_v5a`) and the date of download.

## What does NOT go here

- Full-genome VCFs (out of scope and very large).
- dbGaP-restricted data of any kind ([`../../docs/architecture.md`](../../docs/architecture.md) §4).
- Re-derivations, lifted-over copies, or analyst-modified versions of the public data — only the ascertained ADME-gene subsets.

## License

1000 Genomes phase 3 data is open. Provenance and citation are recorded per file in this directory.
