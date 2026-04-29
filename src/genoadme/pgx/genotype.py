"""1000 Genomes ingest and individual-level genotype representation.

Stub module. The data path conventions (``data/genotype/...``) come from
``docs/architecture.md`` §5; the holdout-generation protocol comes from
``docs/holdout-seed.md``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Genotype:
    """An individual-level genotype, restricted to ADME-relevant variants.

    Attributes:
        sample_id: 1000 Genomes individual ID, or a synthetic ID for
            user-supplied genotypes.
        super_population: One of {"AFR", "AMR", "EAS", "EUR", "SAS"} for
            1000 Genomes individuals; ``None`` for user-supplied data.
        calls: Mapping ``rsid -> (allele_a, allele_b)`` for ADME variants
            present on the individual. Phasing is preserved when the
            source data is phased (1000 Genomes phase 3 is phased).

    The dataclass is frozen because a Genotype is an evidentiary record:
    once constructed for a validation run, it is not mutated.
    """

    sample_id: str
    super_population: str | None
    calls: dict[str, tuple[str, str]]


def load_thousand_genomes_holdout(holdout_id_path: str) -> list[Genotype]:
    """Load the 500-individual holdout subset.

    **Stub — not implemented in v0.1.0.**

    When implemented this will read ``data/genotype/holdout500_ids.txt``,
    extract the corresponding ADME-gene VCF subsets from
    ``data/genotype/``, and emit one ``Genotype`` per individual.

    Any caller of this function reads holdout data and therefore MUST
    have logged the access via ``genoadme.audit.log_query`` first.
    """
    raise NotImplementedError(
        "1000 Genomes holdout ingest is not implemented in v0.1.0. "
        "See docs/architecture.md §5 for the data layout and "
        "docs/holdout-seed.md for the sampling protocol."
    )
