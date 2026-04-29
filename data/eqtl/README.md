# `data/eqtl/`

ADME-gene eQTL summary statistics from **GTEx v8** (open data).

## Status

Empty in v0.1.0 skeleton.

## What goes here

- One effect table per gene × tissue, restricted to ADME genes ([`../../docs/architecture.md`](../../docs/architecture.md) §1) and to tissues relevant to ADME (liver, intestine, kidney).
- A provenance record naming the GTEx release version, the date of download, and the upstream URL.

## What does NOT go here

- Individual-level GTEx data (genotype + tissue RNA-seq). That is dbGaP-restricted ([`../../docs/architecture.md`](../../docs/architecture.md) §4) and never appears in this repository.
- Re-analyses of GTEx that reuse individual-level data. GenoADME relies exclusively on the published summary statistics.

## License

GTEx v8 summary statistics are open data. Cite per the GTEx Consortium guidance.
