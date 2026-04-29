"""Lock docs ↔ code consistency for tier assignments.

If ``docs/validation-tiers.md`` and ``src/genoadme/_constants.py`` ever
drift apart, these tests fail. The doc is the spec; if the test fails,
**update the docs first** (and the constants under a ``tier-change:``
commit). The code follows the spec, never the other way around.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from genoadme._constants import TIER_1_PAIRS, TIER_2_PAIRS, TIER_3_GENES

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_VALIDATION_TIERS_MD = _REPO_ROOT / "docs" / "validation-tiers.md"


def _section(text: str, heading_pattern: str) -> str:
    """Return the markdown section starting at the H2 matching *heading_pattern*."""
    m = re.search(
        rf"^## {heading_pattern}.*?$(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not m:
        raise AssertionError(
            f"Could not find H2 section matching {heading_pattern!r} in "
            f"{_VALIDATION_TIERS_MD}"
        )
    return m.group(1)


def _table_first_two_columns(section: str) -> list[tuple[str, str]]:
    """Extract (col1, col2) from every data row of every pipe-table in *section*."""
    rows: list[tuple[str, str]] = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 2:
            continue
        col1, col2 = cols[0], cols[1]
        # Skip header (Gene/Drug) and separator rows (---).
        if col1.lower() in {"gene", ""} or set(col1) <= set("-:"):
            continue
        rows.append((col1, col2))
    return rows


@pytest.fixture(scope="module")
def md_text() -> str:
    return _VALIDATION_TIERS_MD.read_text(encoding="utf-8")


def test_validation_tiers_md_exists(md_text: str) -> None:
    assert md_text, f"{_VALIDATION_TIERS_MD} is empty"


def test_tier1_pairs_match_docs(md_text: str) -> None:
    section = _section(md_text, r"Tier 1")
    pairs = _table_first_two_columns(section)
    # Validation-tiers.md has only one pairs table per tier section.
    assert tuple(pairs) == TIER_1_PAIRS, (
        f"Tier 1 pairs in docs ({pairs}) do not match _constants.TIER_1_PAIRS "
        f"({TIER_1_PAIRS}). Update the docs first, then the constants under a "
        f"`tier-change:` commit per docs/commit-discipline.md §4."
    )


def test_tier2_pairs_match_docs(md_text: str) -> None:
    section = _section(md_text, r"Tier 2")
    pairs = _table_first_two_columns(section)
    assert tuple(pairs) == TIER_2_PAIRS, (
        f"Tier 2 pairs in docs ({pairs}) do not match _constants.TIER_2_PAIRS "
        f"({TIER_2_PAIRS}). Update the docs first."
    )


def test_tier3_genes_match_docs(md_text: str) -> None:
    section = _section(md_text, r"Tier 3")
    rows = _table_first_two_columns(section)
    genes_in_docs = frozenset(g for g, _ in rows)
    assert genes_in_docs == TIER_3_GENES, (
        f"Tier 3 genes in docs ({sorted(genes_in_docs)}) do not match "
        f"_constants.TIER_3_GENES ({sorted(TIER_3_GENES)}). Update the docs first."
    )


def test_no_overlap_between_tiers() -> None:
    tier1_genes = {g for g, _ in TIER_1_PAIRS}
    tier2_genes = {g for g, _ in TIER_2_PAIRS}
    assert tier1_genes.isdisjoint(tier2_genes)
    assert tier1_genes.isdisjoint(TIER_3_GENES)
    assert tier2_genes.isdisjoint(TIER_3_GENES)
