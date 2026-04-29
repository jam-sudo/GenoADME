"""Lock the v0.1.0 stub contract for validation runners.

These tests will need to be updated when the runners are implemented.
For now they enforce that:

- The stubs raise NotImplementedError (not silently produce numbers).
- The stubs do NOT touch the holdout (so they cannot leak audit log
  entries on accidental import).
- ``_require_holdout`` raises HoldoutNotGeneratedError when the file is
  missing — the contract that future runners will rely on.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from genoadme.errors import HoldoutNotGeneratedError
from genoadme.validate import _require_holdout, run_all, run_tier1, run_tier2


def test_run_tier1_is_stub() -> None:
    with pytest.raises(NotImplementedError) as exc:
        run_tier1()
    assert "validation-tiers.md" in str(exc.value)


def test_run_tier2_is_stub() -> None:
    with pytest.raises(NotImplementedError) as exc:
        run_tier2()
    assert "validation-tiers.md" in str(exc.value)


def test_run_all_is_stub() -> None:
    with pytest.raises(NotImplementedError):
        run_all()


def test_require_holdout_raises_when_missing(tmp_path: Path) -> None:
    missing = tmp_path / "no_such_holdout.txt"
    with pytest.raises(HoldoutNotGeneratedError) as exc:
        _require_holdout(missing)
    assert "holdout-seed.md" in str(exc.value)


def test_require_holdout_passes_when_present(tmp_path: Path) -> None:
    present = tmp_path / "holdout.txt"
    present.write_text("HG00096\n")
    _require_holdout(present)  # no exception
