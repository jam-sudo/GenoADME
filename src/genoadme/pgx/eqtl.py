"""GTEx v8 eQTL ingest and SNP-to-expression effect mapping.

Stub module. Uses **public GTEx v8 summary statistics only**; individual-
level GTEx data is dbGaP-restricted and is excluded by repo policy
(see ``docs/architecture.md`` §4 and ``docs/limitations.md`` §5).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EQTLEffect:
    """A single SNP → tissue-mRNA expression effect from GTEx summary stats.

    Attributes:
        rsid: dbSNP rsID of the variant.
        gene: ENSG identifier of the eGene.
        gene_symbol: HGNC gene symbol (e.g., ``"SLCO1B1"``).
        tissue: GTEx tissue label (e.g., ``"Liver"``, ``"Small_Intestine_Terminal_Ileum"``).
        beta: Effect size (slope of normalized expression vs allele dosage).
        beta_se: Standard error of ``beta``.
        ref_allele: Reference allele used by GTEx for the effect direction.
        alt_allele: Alternate (effect) allele.
        pval_nominal: Nominal p-value reported by GTEx.

    Sign convention: ``beta`` is the change in normalized expression per
    additional copy of ``alt_allele``. **GTEx ALT/REF convention must be
    cross-checked against 1000 Genomes ALT/REF for each variant.** A
    flipped sign here would silently invert genotype-conditional
    predictions; see ``docs/commit-discipline.md`` §3 example.
    """

    rsid: str
    gene: str
    gene_symbol: str
    tissue: str
    beta: float
    beta_se: float
    ref_allele: str
    alt_allele: str
    pval_nominal: float


def load_eqtl_table(gene_symbol: str, tissue: str) -> list[EQTLEffect]:
    """Load eQTL summary statistics for a single gene × tissue.

    **Stub — not implemented in v0.1.0.**

    When implemented this will read effect tables from ``data/eqtl/``
    (committed alongside provenance in ``data/eqtl/README.md``).
    """
    raise NotImplementedError(
        "GTEx eQTL ingest is not implemented in v0.1.0. "
        "See docs/architecture.md §5 for the data layout."
    )
