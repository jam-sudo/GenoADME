"""PGx layer — DNA variant → phenotype label / expression refinement.

This subpackage is the only place GenoADME adds new scientific logic on
top of Sisyphus. Sisyphus already provides:

- ``sisyphus.predict.phenotype.PHENOTYPE_SCALES``
  (PM/IM/EM/NM/UM/RM activity multipliers)
- ``sisyphus.predict.phenotype.apply_phenotype_to_graph``
  (applies a {gene: phenotype-label} dict to a body graph)

What Sisyphus does NOT provide, and therefore what this subpackage adds:

- ``genoadme.pgx.genotype`` — 1000 Genomes ingest, ADME variant extraction.
- ``genoadme.pgx.eqtl`` — GTEx eQTL ingest, SNP-to-expression effect mapping.
- ``genoadme.pgx.phenotype`` — CPIC star-allele tables → phenotype label
  *caller* (Sisyphus consumes the label; GenoADME produces it from
  variant calls).
- ``genoadme.pgx.mapping`` — hybrid (categorical phenotype × continuous
  eQTL refinement) mapping that turns a genotype into a Sisyphus-compatible
  parameter modulation.
"""

from __future__ import annotations
