"""Pre-specified validation tier assignments — machine-readable copy.

The canonical, human-readable record of these assignments is in
``docs/validation-tiers.md``. The values here exist so production code
can refer to them without parsing markdown at runtime.

Tests verify the two stay in sync — see ``tests/unit/test_constants.py``.
If a test fails because the docs and constants drift, **update the docs
first**, then run validation, then update the constants under a
``tier-change:`` commit per ``docs/commit-discipline.md`` §4. The doc is
the spec; the code follows the spec, never the other way around.
"""

from __future__ import annotations

# Tier 1 — strong eQTL signal + CPIC Level A. Hybrid mapping
# (categorical phenotype × continuous eQTL refinement).
TIER_1_PAIRS: tuple[tuple[str, str], ...] = (
    ("SLCO1B1", "simvastatin"),
    ("NAT2", "isoniazid"),
    ("UGT1A1", "irinotecan"),
)

# Tier 2 — CPIC Level A but eQTL noisy. Categorical phenotype only;
# the continuous mapping is bypassed for these genes.
TIER_2_PAIRS: tuple[tuple[str, str], ...] = (
    ("CYP2C19", "clopidogrel"),
    ("CYP2C9", "warfarin"),
)

# Tier 3 — acknowledged gap. Requesting these genes raises
# ``UnsupportedGeneError`` (see ``genoadme.errors``).
TIER_3_GENES: frozenset[str] = frozenset({"CYP2D6", "CYP3A4", "ABCB1"})

# Convenience: every gene currently mentioned in any tier.
TIER_1_GENES: frozenset[str] = frozenset(g for g, _ in TIER_1_PAIRS)
TIER_2_GENES: frozenset[str] = frozenset(g for g, _ in TIER_2_PAIRS)
ALL_TIERED_GENES: frozenset[str] = TIER_1_GENES | TIER_2_GENES | TIER_3_GENES
