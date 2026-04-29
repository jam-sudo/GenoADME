"""Top-level ``predict_pk`` entry point.

Behavioral contract (architecture.md §2):
- Without a genotype, ``predict_pk`` is the average-patient Sisyphus
  prediction — equivalent to calling ``sisyphus.pipeline.predict.predict``
  directly.
- With a genotype, ``predict_pk`` routes the prediction through the PGx
  layer. **In v0.1.0 the PGx route raises ``NotImplementedError``.** The
  integration path goes through ``sisyphus.predict.phenotype`` (already
  available upstream) plus the GenoADME mapping layer (stubs in
  ``genoadme.pgx``).
"""

from __future__ import annotations

from typing import Any


def predict_pk(
    smiles: str,
    *,
    dose_mg: float,
    route: str = "oral",
    genotype: Any = None,
    population: str | None = None,
    **kwargs: Any,
) -> Any:
    """Genotype-conditional ADME / PK prediction.

    Args:
        smiles: Drug SMILES string.
        dose_mg: Dose in mg. Required — no default, because there is no
            honest default for an arbitrary drug. (Note: the README's
            illustrative example omits ``dose_mg``; in v0.1.0 the call
            requires it.)
        route: ``"oral"`` or ``"iv"``. Defaults to ``"oral"``.
        genotype: Optional individual-level genotype object. When
            supplied, the prediction is conditioned on that genotype via
            the PGx layer. Mutually exclusive with ``population``.
        population: Optional population specifier (e.g.,
            ``"1000G_holdout500"``) producing a population-level
            distribution. Mutually exclusive with ``genotype``.
        **kwargs: Forwarded to ``sisyphus.pipeline.predict.predict``.

    Returns:
        ``sisyphus.core.PredictionResult`` (no genotype) or a
        genotype-conditional distribution wrapper (with genotype, once
        the PGx layer is implemented).

    Raises:
        ValueError: If both ``genotype`` and ``population`` are supplied.
        NotImplementedError: If either ``genotype`` or ``population`` is
            supplied. The PGx route is not implemented in v0.1.0.
    """
    if genotype is not None and population is not None:
        raise ValueError("Pass exactly one of `genotype` or `population`, not both.")

    if genotype is None and population is None:
        # architecture.md §2: no genotype → average-patient Sisyphus prediction.
        from sisyphus.pipeline.predict import predict as _sisyphus_predict
        return _sisyphus_predict(
            smiles, dose_mg=dose_mg, route=route, **kwargs
        )

    raise NotImplementedError(
        "Genotype-conditional prediction is not implemented in v0.1.0. "
        "Planned integration: genoadme.pgx.mapping.genotype_to_phenotypes "
        "→ sisyphus.predict.phenotype.apply_phenotype_to_graph "
        "→ sisyphus engine + pk layers. See docs/architecture.md §1. "
        "Tier 3 genes (CYP2D6, CYP3A4, ABCB1) raise UnsupportedGeneError "
        "before reaching this point — see docs/limitations.md §2."
    )
