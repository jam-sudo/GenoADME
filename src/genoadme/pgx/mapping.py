"""Hybrid mapping: genotype → Sisyphus-compatible parameter modulation.

This is the integration point with Sisyphus. The output of
``genotype_to_phenotypes`` is what
``sisyphus.predict.phenotype.apply_phenotype_to_graph`` consumes —
returning a body graph whose enzyme/transporter abundances are scaled
by the CPIC activity multipliers.

Per ``docs/validation-tiers.md``, two mapping modes exist:

- **Tier 1** — hybrid (categorical phenotype × continuous eQTL refinement).
- **Tier 2** — categorical only; the continuous eQTL refinement is
  *bypassed* for these genes.

Tier 3 genes never reach this module — ``UnsupportedGeneError`` is
raised earlier (see ``genoadme.errors.check_gene_supported``).
"""

from __future__ import annotations

from genoadme._constants import TIER_1_GENES, TIER_2_GENES
from genoadme.errors import check_gene_supported
from genoadme.pgx.genotype import Genotype


def genotype_to_phenotypes(genotype: Genotype, genes: list[str]) -> dict[str, str]:
    """Return ``{gene: phenotype_label}`` for the given genes.

    **Stub — not implemented in v0.1.0.**

    Behavior contract for the future implementation:

    - For each gene in ``genes``: call ``check_gene_supported`` first
      (raises ``UnsupportedGeneError`` for Tier 3).
    - For Tier 1 genes: compute the categorical CPIC phenotype, then
      apply continuous eQTL refinement (see
      ``genoadme.pgx.eqtl``) to produce a refined effective scale.
    - For Tier 2 genes: compute the categorical CPIC phenotype only;
      eQTL refinement is intentionally bypassed.
    - The output dict is shaped for direct consumption by
      ``sisyphus.predict.phenotype.apply_phenotype_to_graph``.
    """
    for gene in genes:
        check_gene_supported(gene)
        if gene not in TIER_1_GENES and gene not in TIER_2_GENES:
            # Genes outside any tier are also not modeled — they are
            # neither passed nor failed; they are simply not part of
            # GenoADME's scope until pre-specified.
            raise ValueError(
                f"Gene {gene!r} is not in any pre-specified tier. "
                f"See docs/validation-tiers.md."
            )
    raise NotImplementedError(
        "Hybrid genotype→phenotype mapping is not implemented in v0.1.0. "
        "See docs/architecture.md §1 and docs/validation-tiers.md."
    )
