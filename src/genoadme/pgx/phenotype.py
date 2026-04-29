"""CPIC star-allele tables → phenotype label *caller*.

This module's job is to produce the ``{gene: phenotype-label}`` dict
that ``sisyphus.predict.phenotype.apply_phenotype_to_graph`` consumes.
The phenotype labels themselves (PM/IM/EM/NM/UM/RM) and their activity
multipliers are defined upstream in Sisyphus — we do **not** redefine
them here. Re-exporting is allowed; redefining would drift from the
canonical Sisyphus definitions over time.
"""

from __future__ import annotations

# Re-export the canonical labels and multipliers from Sisyphus so the
# rest of GenoADME can import them from one place. If the upstream
# definitions change, GenoADME inherits the change automatically — the
# whole point of architecture.md §1.
from sisyphus.predict.phenotype import (  # noqa: F401
    PHENOTYPE_SCALES,
    TRANSPORTER_ALIASES,
)

from genoadme.errors import check_gene_supported
from genoadme.pgx.genotype import Genotype


def call_phenotype(genotype: Genotype, gene: str) -> str:
    """Assign a CPIC phenotype label (PM/IM/EM/NM/UM/RM) to one gene.

    **Stub — not implemented in v0.1.0.**

    When implemented this will look up the individual's variant calls
    in the CPIC star-allele table snapshotted under ``data/pharmgkb/``
    and return the canonical phenotype label.

    Tier 3 genes raise ``UnsupportedGeneError`` immediately — the
    star-allele caller is not allowed to silently produce a label for
    them. See ``docs/limitations.md`` §2.
    """
    check_gene_supported(gene)
    raise NotImplementedError(
        f"CPIC star-allele phenotype caller for gene {gene!r} is not "
        f"implemented in v0.1.0. See docs/architecture.md §1."
    )
