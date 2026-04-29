"""Lock the predict_pk public surface.

These tests verify the signature contracts WITHOUT actually invoking
Sisyphus's pipeline. They protect against silent regressions in the
genotype/population gating that would breach docs/architecture.md §2
or docs/limitations.md §2.
"""

from __future__ import annotations

import pytest

from genoadme import predict_pk


def test_genotype_and_population_are_mutually_exclusive() -> None:
    with pytest.raises(ValueError) as exc:
        predict_pk(
            "CC(=O)Oc1ccccc1C(=O)O",
            dose_mg=100.0,
            genotype=object(),
            population="1000G_holdout500",
        )
    assert "exactly one" in str(exc.value).lower()


def test_genotype_path_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError) as exc:
        predict_pk(
            "CC(=O)Oc1ccccc1C(=O)O",
            dose_mg=100.0,
            genotype=object(),
        )
    assert "v0.1.0" in str(exc.value)
    assert "architecture.md" in str(exc.value)


def test_population_path_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        predict_pk(
            "CC(=O)Oc1ccccc1C(=O)O",
            dose_mg=100.0,
            population="1000G_holdout500",
        )


def test_dose_mg_is_required() -> None:
    # No default for dose_mg: TypeError if omitted.
    with pytest.raises(TypeError):
        predict_pk("CC(=O)Oc1ccccc1C(=O)O")  # type: ignore[call-arg]
