"""Exceptions raised by GenoADME.

The most consequential one is ``UnsupportedGeneError``. Per
``docs/architecture.md`` §3 and ``docs/limitations.md`` §2, Tier 3 genes
must fail loudly — silently returning the average-patient prediction
for CYP2D6 (the most clinically actionable gene in pharmacogenomics)
would be a methodological failure disguised as a feature.
"""

from __future__ import annotations

from genoadme._constants import TIER_3_GENES


class GenoADMEError(Exception):
    """Base class for all GenoADME errors."""


class UnsupportedGeneError(GenoADMEError):
    """Raised when a Tier 3 gene is requested for genotype-conditional prediction.

    Tier 3 genes are pre-specified in ``docs/validation-tiers.md`` §Tier 3
    and the per-gene rationale is in ``docs/limitations.md`` §2.
    """

    def __init__(self, gene: str):
        self.gene = gene
        super().__init__(
            f"Gene {gene!r} is Tier 3 (not modeled). "
            f"Tier 3 genes: {sorted(TIER_3_GENES)}. "
            f"See docs/limitations.md §2 and docs/validation-tiers.md §Tier 3."
        )


class HoldoutNotGeneratedError(GenoADMEError):
    """Raised when a validation runner is invoked but the holdout file is missing.

    The fix is to generate the holdout once per the protocol in
    ``docs/holdout-seed.md``. Until that has been done, no headline
    metric can be produced — and the integrity rules in
    ``docs/scientific-integrity.md`` §2 require the holdout to be
    drawn from a committed seed before any validation run executes.
    """


class WorkingTreeNotCleanError(GenoADMEError):
    """Raised when a validation-purpose audit entry is requested while a
    participating repository's working tree is dirty.

    Surfaced by GenoADME issue #1, motivated by the 2026-05-01
    reproducibility audit (``docs/limitations.md`` §10.2): the original
    2026-04-29 Tier 1 run logged ``git_sha`` but not working-tree state,
    and Sisyphus's then-uncommitted prodrug-v2 WIP altered RNG draw
    order, so the recorded SHA did not strictly reproduce the numbers.

    Pass ``allow_dirty=True`` to ``audit.log_query`` for exploratory
    runs (the entry is still logged, with ``worktree_clean: false``).
    """


def check_gene_supported(gene: str) -> None:
    """Raise ``UnsupportedGeneError`` if *gene* is in Tier 3."""
    if gene in TIER_3_GENES:
        raise UnsupportedGeneError(gene)
