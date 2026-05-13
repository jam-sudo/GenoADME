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


@pytest.mark.parametrize("gene", ["UGT1A1", "CYP2C19", "CYP2C9"])
def test_deferred_genes_raise_not_implemented(gene: str) -> None:
    """Pre-specified-but-deferred genes must fail loudly with a pointer
    to the Deferred docs section, not silently default to EM/NM.

    NAT2 was promoted out of this set in v0.4 (Phase 3 infrastructure
    commit, then Phase 4 `tier-change:`). The remaining three deferred
    genes still require Sisyphus #11 (prodrug registry) work.
    """
    g = _genotype({"rs1": ("A", "A")})
    with pytest.raises(NotImplementedError) as exc:
        call_phenotype(g, gene)
    assert "Deferred" in str(exc.value)
    assert "v0." in str(exc.value)  # any version-string mention is fine


# ---------------------------------------------------------------------------
# NAT2 phenotype caller (v0.4) — 5-SNP haplotype-based SA/IA/RA → PM/IM/EM
# ---------------------------------------------------------------------------

# REF / ALT allele convention from genoadme.pgx.phenotype._NAT2_SLOW_FUNCTION_SNPS:
#   rs1801279 G/A; rs1041983 C/T; rs1801280 T/C; rs1799930 G/A; rs1799931 G/A.
# ALT is the slow-function allele. A haplotype is "slow" if ANY of the five
# SNPs carries the ALT on that haplotype.

_NAT2_ALL_REF: dict[str, tuple[str, str]] = {
    "rs1801279": ("G", "G"),
    "rs1041983": ("C", "C"),
    "rs1801280": ("T", "T"),
    "rs1799930": ("G", "G"),
    "rs1799931": ("G", "G"),
}


def _nat2_calls(overrides: dict[str, tuple[str, str]]) -> dict[str, tuple[str, str]]:
    """Build a NAT2 calls dict starting from all-REF and applying overrides."""
    out = dict(_NAT2_ALL_REF)
    out.update(overrides)
    return out


def test_nat2_both_alleles_all_ref_returns_em_rapid_acetylator() -> None:
    """*4/*4 (all REF on the five marker SNPs) → RA → EM label."""
    g = _genotype(_NAT2_ALL_REF)
    assert call_phenotype(g, "NAT2") == "EM"


def test_nat2_one_slow_allele_via_341c_returns_im_intermediate() -> None:
    """*4/*5A (one allele carries rs1801280 ALT) → IA → IM."""
    g = _genotype(_nat2_calls({"rs1801280": ("T", "C")}))
    assert call_phenotype(g, "NAT2") == "IM"


def test_nat2_both_alleles_slow_via_341c_returns_pm_slow_acetylator() -> None:
    """*5A/*5A (both alleles carry rs1801280 ALT) → SA → PM."""
    g = _genotype(_nat2_calls({"rs1801280": ("C", "C")}))
    assert call_phenotype(g, "NAT2") == "PM"


def test_nat2_mixed_slow_alleles_via_different_snps_returns_pm() -> None:
    """*5A/*6B (one haplotype carries 341C, the other 590A) → SA → PM."""
    g = _genotype(
        _nat2_calls(
            {
                "rs1801280": ("C", "T"),  # haplotype 0 has 341C (slow)
                "rs1799930": ("G", "A"),  # haplotype 1 has 590A (slow)
            }
        )
    )
    assert call_phenotype(g, "NAT2") == "PM"


def test_nat2_two_slow_snps_on_same_haplotype_returns_im() -> None:
    """*4/*6A (one allele REF; other carries BOTH 282T + 590A — *6A linkage):
    only one haplotype is slow → IA → IM."""
    g = _genotype(
        _nat2_calls(
            {
                "rs1041983": ("C", "T"),  # haplotype 1 has 282T
                "rs1799930": ("G", "A"),  # haplotype 1 has 590A
            }
        )
    )
    assert call_phenotype(g, "NAT2") == "IM"


def test_nat2_returned_labels_are_in_sisyphus_phenotype_scales() -> None:
    """Every label NAT2 can produce must be a key in Sisyphus's PHENOTYPE_SCALES."""
    for label in ["EM", "IM", "PM"]:
        assert label in PHENOTYPE_SCALES


def test_nat2_missing_one_of_five_snps_raises() -> None:
    """NAT2 caller refuses to fabricate slow-count if any marker SNP is missing."""
    calls = dict(_NAT2_ALL_REF)
    del calls["rs1799931"]
    g = _genotype(calls)
    with pytest.raises(ValueError, match="rs1799931"):
        call_phenotype(g, "NAT2")


def test_nat2_unrecognized_allele_raises() -> None:
    g = _genotype(_nat2_calls({"rs1801280": ("T", "G")}))  # G is not T or C
    with pytest.raises(ValueError, match="Unrecognized"):
        call_phenotype(g, "NAT2")


def test_nat2_display_label_mapping_documented() -> None:
    """Sanity-lock the SA/IA/RA → PM/IM/EM display mapping for reports."""
    from genoadme.pgx.phenotype import NAT2_DISPLAY_LABEL

    assert NAT2_DISPLAY_LABEL["PM"] == "SA"
    assert NAT2_DISPLAY_LABEL["IM"] == "IA"
    assert NAT2_DISPLAY_LABEL["EM"] == "RA"
