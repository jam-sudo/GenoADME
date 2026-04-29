"""Lock the Tier 3 contract.

If a Tier 3 gene ever stops raising ``UnsupportedGeneError``, that is a
silent fallback — exactly what ``docs/architecture.md`` §3 prohibits.
These tests make that regression noisy.
"""

from __future__ import annotations

import pytest

from genoadme._constants import TIER_1_GENES, TIER_2_GENES, TIER_3_GENES
from genoadme.errors import UnsupportedGeneError, check_gene_supported


@pytest.mark.parametrize("gene", sorted(TIER_3_GENES))
def test_tier3_genes_raise(gene: str) -> None:
    with pytest.raises(UnsupportedGeneError) as exc:
        check_gene_supported(gene)
    assert exc.value.gene == gene
    # Error message must point users to the canonical disclosure docs.
    msg = str(exc.value)
    assert "limitations.md" in msg
    assert "validation-tiers.md" in msg


@pytest.mark.parametrize("gene", sorted(TIER_1_GENES | TIER_2_GENES))
def test_tier1_and_tier2_genes_do_not_raise(gene: str) -> None:
    check_gene_supported(gene)


def test_unsupported_gene_error_carries_gene() -> None:
    err = UnsupportedGeneError("CYP2D6")
    assert err.gene == "CYP2D6"
    assert "CYP2D6" in str(err)


def test_tier3_set_is_exactly_specified() -> None:
    assert TIER_3_GENES == frozenset({"CYP2D6", "CYP3A4", "ABCB1"})
