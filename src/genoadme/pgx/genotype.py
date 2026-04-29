"""1000 Genomes ingest and individual-level genotype representation.

The data path conventions (``data/genotype/...``) come from
``docs/architecture.md`` §5; the holdout-generation protocol comes from
``docs/holdout-seed.md``.

This module is **deterministic** in two senses:

1. ``generate_holdout(seed, panel_path)`` always produces the same
   holdout for the same seed and the same panel file (verified by SHA).
2. Reading the holdout back via ``load_holdout`` returns IDs in the same
   lexicographic order they were written in.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class Genotype:
    """An individual-level genotype, restricted to ADME-relevant variants.

    Attributes:
        sample_id: 1000 Genomes individual ID, or a synthetic ID for
            user-supplied genotypes.
        super_population: One of {"AFR", "AMR", "EAS", "EUR", "SAS"} for
            1000 Genomes individuals; ``None`` for user-supplied data.
        calls: Mapping ``rsid -> (allele_a, allele_b)`` for ADME variants
            present on the individual. Phasing is preserved when the
            source data is phased (1000 Genomes phase 3 is phased).
    """

    sample_id: str
    super_population: str | None
    calls: dict[str, tuple[str, str]]


@dataclass(frozen=True)
class HoldoutRecord:
    """Audit-record returned by ``generate_holdout``.

    Used to populate ``docs/holdout-seed.md`` after first generation.
    The ``holdout_sha256`` field lets any later ``git checkout`` verify
    that the committed holdout file has not been silently modified.
    """

    seed: int
    n: int
    panel_path: str
    panel_sha256: str
    holdout_path: str
    holdout_sha256: str
    super_pop_breakdown: dict[str, int]
    first_id: str
    last_id: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_PANEL_REQUIRED_COLUMNS = ("sample", "pop", "super_pop")


def _read_panel(panel_path: Path) -> dict[str, list[str]]:
    """Parse the 1000G phase 3 panel TSV.

    Returns ``{super_pop: [sorted sample IDs]}``. Sample IDs are sorted
    inside each super-population so the rng.choice index draw is
    deterministic regardless of original line order.
    """
    by_super: dict[str, list[str]] = {}
    with panel_path.open("r", encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        cols = [h.strip() for h in header]
        for required in _PANEL_REQUIRED_COLUMNS:
            if required not in cols:
                raise ValueError(
                    f"Panel {panel_path} missing required column {required!r}; "
                    f"got header={cols}"
                )
        i_sample = cols.index("sample")
        i_super = cols.index("super_pop")
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) <= max(i_sample, i_super):
                continue
            sample = parts[i_sample].strip()
            super_pop = parts[i_super].strip()
            if not sample or not super_pop:
                continue
            by_super.setdefault(super_pop, []).append(sample)
    for sp in by_super:
        by_super[sp].sort()
    return by_super


def _stratified_targets(counts: dict[str, int], n_total: int) -> dict[str, int]:
    """Largest-remainder allocation: targets sum to exactly ``n_total``.

    Per ``docs/holdout-seed.md`` "Sampling protocol", the holdout's
    super-population proportions match the full panel within ±1 per
    super-population.
    """
    grand = sum(counts.values())
    raw = {sp: counts[sp] * n_total / grand for sp in counts}
    floor = {sp: int(v) for sp, v in raw.items()}
    deficit = n_total - sum(floor.values())
    if deficit > 0:
        # Sort super-pops by descending fractional remainder, ties broken
        # by lex order on super-pop name (deterministic).
        order = sorted(counts, key=lambda sp: (-(raw[sp] - floor[sp]), sp))
        for sp in order[:deficit]:
            floor[sp] += 1
    return floor


def _sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_holdout(
    seed: int,
    panel_path: str | Path,
    out_path: str | Path,
    n: int = 500,
    audit_log_path: str | Path | None = None,
) -> HoldoutRecord:
    """Generate the holdout subset deterministically from ``seed``.

    Implementation matches the protocol in ``docs/holdout-seed.md``:

    1. Read the 1000G phase 3 panel (TSV with columns sample, pop, super_pop).
    2. Stratify the draw by super-population using largest-remainder
       allocation (sum of targets exactly = ``n``).
    3. Use ``np.random.default_rng(seed)`` to draw IDs without
       replacement within each super-population.
    4. Write the resulting IDs, lexicographically sorted, one per line,
       to ``out_path``.
    5. Append a ``purpose="holdout generation"`` entry to the audit log.

    Args:
        seed: Random seed. The canonical v0.1.0 value is 42.
        panel_path: Path to the 1000G phase 3 panel TSV.
        out_path: Where to write the holdout IDs (one per line, sorted).
        n: Number of individuals to draw. Default 500.
        audit_log_path: Optional override for the audit log location.
            Defaults to ``reports/audit-log.jsonl`` (resolved by
            ``genoadme.audit``).

    Returns:
        ``HoldoutRecord`` with seed, panel SHA, holdout SHA, super-pop
        breakdown, and first/last IDs. Used to populate the v0.1.0
        record in ``docs/holdout-seed.md``.

    Raises:
        ValueError: If the panel is malformed or smaller than ``n``.
    """
    panel_path = Path(panel_path)
    out_path = Path(out_path)

    by_super = _read_panel(panel_path)
    counts = {sp: len(samples) for sp, samples in by_super.items()}
    grand = sum(counts.values())
    if grand < n:
        raise ValueError(
            f"Panel {panel_path} has {grand} samples; cannot draw {n}."
        )

    targets = _stratified_targets(counts, n)

    rng = np.random.default_rng(seed)
    chosen: list[str] = []
    breakdown: dict[str, int] = {}
    # Iterate super-pops in lex order so the rng draw sequence is
    # deterministic across Python versions.
    for sp in sorted(by_super):
        samples = by_super[sp]  # already sorted
        target = targets[sp]
        if target == 0:
            breakdown[sp] = 0
            continue
        idx = rng.choice(len(samples), size=target, replace=False)
        picked = [samples[int(i)] for i in idx]
        chosen.extend(picked)
        breakdown[sp] = len(picked)

    chosen_sorted = sorted(chosen)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(chosen_sorted) + "\n", encoding="utf-8")

    record = HoldoutRecord(
        seed=seed,
        n=n,
        panel_path=str(panel_path),
        panel_sha256=_sha256_of(panel_path),
        holdout_path=str(out_path),
        holdout_sha256=_sha256_of(out_path),
        super_pop_breakdown=breakdown,
        first_id=chosen_sorted[0],
        last_id=chosen_sorted[-1],
    )

    # Audit *after* the file exists so log_query's existence check passes.
    from genoadme.audit import log_query
    log_query(
        out_path,
        purpose="holdout generation",
        caller="genoadme.pgx.genotype.generate_holdout",
        log_path=audit_log_path,
    )
    return record


def load_holdout(holdout_id_path: str | Path) -> list[str]:
    """Read the holdout IDs file, one per line, lex-sorted.

    Returns the list of sample IDs as committed to disk. Skips blank
    lines. Does not log an audit entry — reading the IDs file alone is
    aggregate-level access (per ``docs/scientific-integrity.md`` §5).
    """
    path = Path(holdout_id_path)
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def load_slco1b1_calls(
    tsv_path: str | Path,
    holdout_id_path: str | Path | None = None,
) -> list[Genotype]:
    """Load rs4149056 (SLCO1B1 521T>C) calls from a 3-column TSV.

    The TSV must have a header line with columns
    ``sample_id``, ``rs4149056_a``, ``rs4149056_b``. Phasing is
    preserved as the source order (the upstream Ensembl REST response
    returns phased calls in the order ``allele|allele``).

    Args:
        tsv_path: Path to the calls TSV. v0.1.0 ships
            ``data/genotype/slco1b1_rs4149056_holdout.tsv``.
        holdout_id_path: Optional. If provided, the result is
            restricted to sample IDs in this holdout file. Use this to
            guarantee the returned list has exactly ``n`` elements per
            the holdout protocol.

    Returns:
        List of ``Genotype`` records, lex-sorted by ``sample_id``,
        each with ``calls = {"rs4149056": (allele_a, allele_b)}``.
        ``super_population`` is resolved from the bundled 1000G panel
        snapshot or ``None`` if the sample is not in the panel.

    Raises:
        ValueError: If the TSV is malformed.
        KeyError: If ``holdout_id_path`` references samples missing
            from the TSV.
    """
    tsv_path = Path(tsv_path)
    by_id: dict[str, tuple[str, str]] = {}
    with tsv_path.open("r", encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        cols = [h.strip() for h in header]
        required = ("sample_id", "rs4149056_a", "rs4149056_b")
        for r in required:
            if r not in cols:
                raise ValueError(
                    f"TSV {tsv_path} missing required column {r!r}; got {cols}"
                )
        i_id = cols.index("sample_id")
        i_a = cols.index("rs4149056_a")
        i_b = cols.index("rs4149056_b")
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) <= max(i_id, i_a, i_b):
                continue
            sid = parts[i_id].strip()
            if not sid:
                continue
            by_id[sid] = (parts[i_a].strip(), parts[i_b].strip())

    if holdout_id_path is not None:
        wanted = load_holdout(holdout_id_path)
        missing = [s for s in wanted if s not in by_id]
        if missing:
            raise KeyError(
                f"{len(missing)} holdout sample(s) missing from {tsv_path}; "
                f"first few: {missing[:5]}"
            )
        ids = sorted(wanted)
    else:
        ids = sorted(by_id.keys())

    panel_lookup = _build_super_pop_lookup()
    return [
        Genotype(
            sample_id=sid,
            super_population=panel_lookup.get(sid),
            calls={"rs4149056": by_id[sid]},
        )
        for sid in ids
    ]


def load_thousand_genomes_holdout(holdout_id_path: str | Path) -> list[Genotype]:
    """Load the 500-individual holdout subset as ``Genotype`` records.

    **Stub for v0.1.0** — returns IDs only (calls={}). When the per-gene
    ADME-variant VCF subsets are committed under ``data/genotype/``,
    this function will populate ``calls`` with the relevant rsids.

    Any caller of this function reads holdout data and therefore MUST
    have logged the access via ``genoadme.audit.log_query`` before
    invoking it.
    """
    panel_lookup = _build_super_pop_lookup()
    return [
        Genotype(
            sample_id=sid,
            super_population=panel_lookup.get(sid),
            calls={},
        )
        for sid in load_holdout(holdout_id_path)
    ]


def _build_super_pop_lookup() -> dict[str, str]:
    """Map sample_id → super_pop using the bundled panel file."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    panel = repo_root / "data" / "genotype" / "integrated_call_samples_v3.20130502.ALL.panel"
    if not panel.exists():
        return {}
    out: dict[str, str] = {}
    by_super = _read_panel(panel)
    for sp, samples in by_super.items():
        for s in samples:
            out[s] = sp
    return out
