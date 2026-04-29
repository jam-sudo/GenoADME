"""Lock the SLCO1B1 phenotype-caller contract.

These tests pin the v0.1.0 single-variant model (rs4149056 only). When
the full star-allele caller is implemented for v0.2, the rs4149056-only
behavior must remain valid as a sub-case (i.e., diplotypes that are
unambiguous from rs4149056 alone must still produce the same labels).
"""

from __future__ import annotations

import pytest

from genoadme.errors import UnsupportedGeneError
from genoadme.pgx.genotype import Genotype
from genoadme.pgx.phenotype import (
    PHENOTYPE_SCALES,
    call_phenotype,
)


def _genotype(calls: dict[str, tuple[str, str]], sid: str = "TEST001") -> Genotype:
    return Genotype(sample_id=sid, super_population=None, calls=calls)


# ---------------------------------------------------------------------------
# SLCO1B1 happy paths
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "alleles, expected",
    [
        (("T", "T"), "EM"),
        (("T", "C"), "IM"),
        (("C", "T"), "IM"),  # phasing-agnostic
        (("C", "C"), "PM"),
    ],
)
def test_slco1b1_diplotype_to_phenotype(
    alleles: tuple[str, str], expected: str
) -> None:
    g = _genotype({"rs4149056": alleles})
    assert call_phenotype(g, "SLCO1B1") == expected


def test_slco1b1_returned_labels_are_in_sisyphus_phenotype_scales() -> None:
    """Every label SLCO1B1 can produce must be a key in Sisyphus's
    PHENOTYPE_SCALES so apply_phenotype_to_graph doesn't reject it."""
    for alleles in [("T", "T"), ("T", "C"), ("C", "C")]:
        g = _genotype({"rs4149056": alleles})
        label = call_phenotype(g, "SLCO1B1")
        assert label in PHENOTYPE_SCALES


# ---------------------------------------------------------------------------
# SLCO1B1 failure modes
# ---------------------------------------------------------------------------


def test_slco1b1_missing_marker_variant_raises() -> None:
    g = _genotype({"rs99999999": ("A", "A")})
    with pytest.raises(ValueError, match="rs4149056"):
        call_phenotype(g, "SLCO1B1")


def test_slco1b1_unknown_allele_raises() -> None:
    g = _genotype({"rs4149056": ("T", "G")})  # G is not REF (T) or ALT (C)
    with pytest.raises(ValueError, match="Unrecognized"):
        call_phenotype(g, "SLCO1B1")


# ---------------------------------------------------------------------------
# Tier 3 gating
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gene", ["CYP2D6", "CYP3A4", "ABCB1"])
def test_tier3_genes_raise_unsupported(gene: str) -> None:
    g = _genotype({"rs1": ("A", "A")})
    with pytest.raises(UnsupportedGeneError):
        call_phenotype(g, gene)


# ---------------------------------------------------------------------------
# Deferred-pair gating (NotImplementedError, not silent)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gene", ["NAT2", "UGT1A1", "CYP2C19", "CYP2C9"])
def test_deferred_genes_raise_not_implemented(gene: str) -> None:
    """Pre-specified-but-deferred genes must fail loudly with a pointer
    to the Deferred docs section, not silently default to EM/NM."""
    g = _genotype({"rs1": ("A", "A")})
    with pytest.raises(NotImplementedError) as exc:
        call_phenotype(g, gene)
    assert "Deferred" in str(exc.value)
    assert "v0.1.0" in str(exc.value) or "v0.2" in str(exc.value)
