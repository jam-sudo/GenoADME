"""Validation entry points keyed to tier.

Each tier's runner is the only function permitted to query the holdout.
When implemented, every runner MUST:

1. Verify the holdout file exists (raise ``HoldoutNotGeneratedError``
   otherwise).
2. Call ``genoadme.audit.log_query`` as the **first action that touches
   holdout state**. Per ``docs/scientific-integrity.md`` §5, smoke
   tests, debugging runs, and failed runs all count.
3. Refuse to publish numbers into ``reports/headline-metrics-*.json``
   without a corresponding audit log entry for the same git SHA.

The runners are ``NotImplementedError`` stubs in v0.1.0 — they
deliberately do not call ``log_query`` yet because they do not (and
must not) read holdout data while raising the stub.
"""

from __future__ import annotations

from pathlib import Path

from genoadme.errors import HoldoutNotGeneratedError

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_HOLDOUT_PATH: Path = _REPO_ROOT / "data" / "genotype" / "holdout500_ids.txt"


def _require_holdout(holdout_path: Path) -> None:
    """Raise ``HoldoutNotGeneratedError`` if the holdout file is missing.

    Used by future implementations of the tier runners. Exposed here so
    the contract is testable independently of any tier-specific logic.
    """
    if not holdout_path.exists():
        raise HoldoutNotGeneratedError(
            f"Holdout file {holdout_path!s} does not exist. "
            f"The 500-individual holdout must be drawn once and committed "
            f"per docs/holdout-seed.md before any validation run."
        )


def run_tier1(seed: int = 42, holdout_path: Path | None = None) -> dict:
    """Run Tier 1 validation. **Stub — not implemented in v0.1.0.**

    Pre-specified pairs (docs/validation-tiers.md §Tier 1):
    SLCO1B1/simvastatin, NAT2/isoniazid, UGT1A1/irinotecan.
    """
    raise NotImplementedError(
        "Tier 1 validation runner is not implemented in v0.1.0. "
        "See docs/validation-tiers.md §Tier 1."
    )


def run_tier2(seed: int = 42, holdout_path: Path | None = None) -> dict:
    """Run Tier 2 validation. **Stub — not implemented in v0.1.0.**

    Pre-specified pairs (docs/validation-tiers.md §Tier 2):
    CYP2C19/clopidogrel, CYP2C9/warfarin.
    """
    raise NotImplementedError(
        "Tier 2 validation runner is not implemented in v0.1.0. "
        "See docs/validation-tiers.md §Tier 2."
    )


def run_all(seed: int = 42, holdout_path: Path | None = None) -> dict:
    """Run Tier 1 + Tier 2 validation and emit headline JSON.

    **Stub — not implemented in v0.1.0.**
    """
    raise NotImplementedError(
        "Multi-tier validation runner is not implemented in v0.1.0."
    )
