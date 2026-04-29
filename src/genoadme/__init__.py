"""GenoADME — genotype-conditional ADME prediction wrapping Sisyphus.

See:
- README.md for the public usage surface.
- docs/architecture.md for the layering rules (GenoADME wraps Sisyphus;
  it does not reimplement it).
- docs/scientific-integrity.md for the rules that make every reported
  metric defensible.
"""

from __future__ import annotations

__version__ = "0.1.0"

from genoadme.errors import (
    GenoADMEError,
    HoldoutNotGeneratedError,
    UnsupportedGeneError,
)
from genoadme.predict import predict_pk

__all__ = [
    "__version__",
    "predict_pk",
    "GenoADMEError",
    "UnsupportedGeneError",
    "HoldoutNotGeneratedError",
]
