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

# ---------------------------------------------------------------------------
# NAT2 phenotype caller (v0.4)
# ---------------------------------------------------------------------------
#
# Per docs/v0.4-nat2-isoniazid-protocol.md §1.2, NAT2 phenotype is called from
# the minimum-sufficient five-SNP set for CPIC-standard SA/IA/RA classification:
#
#   rs1801279 (191G>A) — *14A/B           slow
#   rs1041983 (282C>T) — *6A linkage      slow (linked)
#   rs1801280 (341T>C) — *5A/B/C          slow
#   rs1799930 (590G>A) — *6A/B            slow
#   rs1799931 (857G>A) — *7A/B            slow
#
# Algorithm: per-allele (phased), allele is "slow" if ANY of the five SNPs
# carries the ALT (alternative, slow-function) allele on that haplotype. Sum
# slow alleles across the two haplotypes; map to phenotype:
#
#   slow_count == 2 → SA (Slow Acetylator)
#   slow_count == 1 → IA (Intermediate Acetylator)
#   slow_count == 0 → RA (Rapid Acetylator)
#
# Sisyphus's PHENOTYPE_SCALES is keyed by CPIC functional label (PM/IM/EM/NM/
# UM/RM), not per-gene. NAT2 SA/IA/RA are NAT2-nomenclature names for the
# *functional* categories the rest of CPIC calls PM/IM/EM. The caller returns
# the Sisyphus-compatible label (PM/IM/EM); validation runners translate to
# SA/IA/RA for NAT2-specific reporting.
#
# *11/*12/*13 (rapid-function variants on different SNPs) are NOT separately
# distinguished — see protocol §1.2 disclosure.
#
# Sources:
#  - CPIC isoniazid / NAT2 guideline (https://cpicpgx.org/guidelines/)
#  - PharmGKB NAT2 allele definitions
#  - Hein DW et al. NAT2 haplotype/functional classifications

# (rsid, REF, ALT) — ALT is the slow-function allele per CPIC NAT2 standard.
_NAT2_SLOW_FUNCTION_SNPS: tuple[tuple[str, str, str], ...] = (
    ("rs1801279", "G", "A"),
    ("rs1041983", "C", "T"),
    ("rs1801280", "T", "C"),
    ("rs1799930", "G", "A"),
    ("rs1799931", "G", "A"),
)

# Map NAT2 SA/IA/RA → Sisyphus PHENOTYPE_SCALES label.
# Internal note: NAT2 "Rapid Acetylator" is the WILD-TYPE / normal-function
# phenotype, mapping to CPIC "EM" (Extensive Metabolizer = normal function).
# "Slow Acetylator" is decreased-function → CPIC "PM" (Poor Metabolizer).
# This mapping is what makes a 0.1×/0.5×/1.0× scale match the NAT2 functional
# categories.
_NAT2_SLOW_COUNT_TO_LABEL: dict[int, str] = {
    2: "PM",  # SA — Slow Acetylator (both alleles slow)
    1: "IM",  # IA — Intermediate Acetylator (one slow, one rapid)
    0: "EM",  # RA — Rapid Acetylator (both alleles rapid, wild-type)
}

# Display-label mapping for NAT2-specific reporting (validation reports use this).
NAT2_DISPLAY_LABEL: dict[str, str] = {
    "PM": "SA",
    "IM": "IA",
    "EM": "RA",
}


# ---------------------------------------------------------------------------
# SLCO1B1 phenotype caller
# ---------------------------------------------------------------------------
#
# v0.1.0 uses a single-variant model: rs4149056 (521T>C, NM_006446.4:c.521T>C).
# This captures the dominant pharmacogenomic signal (the *5 / *15 / *17
# Decreased-Function alleles are all rs4149056-positive) but not the full
# star-allele resolution. The full caller (rs4149056 + rs2306283 + structural
# variants for *14, *20, etc.) is deferred to v0.2; the limitation is
# documented in docs/limitations.md §6.
#
# Sources:
# - CPIC SLCO1B1 functionality table (https://cpicpgx.org/guidelines/guideline-for-simvastatin-and-slco1b1/)
# - PharmGKB SLCO1B1 allele definitions (https://www.pharmgkb.org/page/slco1b1RefMaterials)
# - Cooper-DeHoff 2022 CPIC update (label mapping to PM/IM/EM/UM)
# - Niemi 2006, Pasanen 2007 (clinical PK effect on pravastatin)
#
# Activity-label convention follows sisyphus.predict.phenotype.PHENOTYPE_SCALES:
#   EM = 1.00× (Normal Function)
#   IM = 0.50× (Decreased Function)
#   PM = 0.10× (Poor Function)

_SLCO1B1_VARIANT = "rs4149056"
_SLCO1B1_REF = "T"
_SLCO1B1_ALT = "C"

# rs4149056 alt-allele dosage → CPIC SLCO1B1 phenotype label.
_SLCO1B1_PHENOTYPE_BY_ALT_DOSAGE: dict[int, str] = {
    0: "EM",  # T/T  — Normal Function
    1: "IM",  # T/C  — Decreased Function  (*1/*5 carrier)
    2: "PM",  # C/C  — Poor Function       (*5/*5 homozygous)
}


def call_phenotype(genotype: Genotype, gene: str) -> str:
    """Assign a CPIC phenotype label (PM/IM/EM/NM/UM/RM) to one gene.

    v0.1.0 implements the SLCO1B1 caller. Other pre-specified genes
    (NAT2, UGT1A1, CYP2C19, CYP2C9) are deferred — see
    ``docs/validation-tiers.md`` §Deferred for the Sisyphus blocker
    that prevents end-to-end validation of each.

    Tier 3 genes (CYP2D6, CYP3A4, ABCB1) raise
    ``UnsupportedGeneError`` immediately — the star-allele caller is
    not allowed to silently produce a label for them. See
    ``docs/limitations.md`` §2.

    Args:
        genotype: Individual-level genotype with ``calls`` populated for
            the gene's marker variant(s).
        gene: HGNC gene symbol (e.g., ``"SLCO1B1"``).

    Returns:
        Phenotype label string, one of the keys in
        ``sisyphus.predict.phenotype.PHENOTYPE_SCALES``.

    Raises:
        UnsupportedGeneError: If ``gene`` is in Tier 3.
        NotImplementedError: If ``gene`` is pre-specified-but-deferred.
        ValueError: If ``gene`` is supported in v0.1.0 but the genotype
            is missing the required marker variant or carries an
            unrecognized allele.
    """
    check_gene_supported(gene)
    if gene == "SLCO1B1":
        return _call_slco1b1(genotype)
    if gene == "NAT2":
        return _call_nat2(genotype)
    raise NotImplementedError(
        f"Phenotype caller for gene {gene!r} is not implemented. "
        f"This gene is in the Deferred list — see "
        f"docs/validation-tiers.md §Deferred for the Sisyphus blocker. "
        f"v0.4 supports SLCO1B1 and NAT2."
    )


def _call_nat2(genotype: Genotype) -> str:
    """Five-SNP haplotype-based NAT2 phenotype caller (v0.4).

    Per ``docs/v0.4-nat2-isoniazid-protocol.md`` §1.2-§1.3: a phased
    haplotype is "slow" if any of the five marker SNPs carries the
    slow-function ALT allele on that haplotype. Sum slow haplotypes
    across the two alleles → CPIC SA/IA/RA.

    Returns the Sisyphus-compatible label (``"PM"`` / ``"IM"`` / ``"EM"``);
    the display mapping to ``"SA"`` / ``"IA"`` / ``"RA"`` is in
    ``NAT2_DISPLAY_LABEL``.
    """
    missing = [rsid for rsid, _, _ in _NAT2_SLOW_FUNCTION_SNPS if rsid not in genotype.calls]
    if missing:
        raise ValueError(
            f"NAT2 phenotype call requires all five marker SNPs in "
            f"genotype.calls (sample {genotype.sample_id!r}). "
            f"Missing: {missing}. Available: {sorted(genotype.calls.keys())}."
        )

    # For each of the two phased haplotypes, decide slow vs rapid.
    slow_count = 0
    for hap_index in (0, 1):
        is_slow = False
        for rsid, ref, alt in _NAT2_SLOW_FUNCTION_SNPS:
            allele = genotype.calls[rsid][hap_index]
            if allele not in (ref, alt):
                raise ValueError(
                    f"Unrecognized {rsid} allele {allele!r} for "
                    f"sample {genotype.sample_id!r} on haplotype "
                    f"{hap_index}; expected one of {(ref, alt)}."
                )
            if allele == alt:
                is_slow = True
                # First slow ALT on this haplotype is enough — no need to
                # check remaining SNPs on the same haplotype.
                break
        if is_slow:
            slow_count += 1

    return _NAT2_SLOW_COUNT_TO_LABEL[slow_count]


def _call_slco1b1(genotype: Genotype) -> str:
    """rs4149056-only SLCO1B1 phenotype caller (v0.1.0)."""
    if _SLCO1B1_VARIANT not in genotype.calls:
        raise ValueError(
            f"SLCO1B1 phenotype call requires {_SLCO1B1_VARIANT} in "
            f"genotype.calls (sample {genotype.sample_id!r}). "
            f"Available: {sorted(genotype.calls.keys())}."
        )
    a, b = genotype.calls[_SLCO1B1_VARIANT]
    for allele in (a, b):
        if allele not in (_SLCO1B1_REF, _SLCO1B1_ALT):
            raise ValueError(
                f"Unrecognized {_SLCO1B1_VARIANT} allele {allele!r} for "
                f"sample {genotype.sample_id!r}; expected one of "
                f"{(_SLCO1B1_REF, _SLCO1B1_ALT)}."
            )
    alt_dosage = sum(1 for allele in (a, b) if allele == _SLCO1B1_ALT)
    return _SLCO1B1_PHENOTYPE_BY_ALT_DOSAGE[alt_dosage]
