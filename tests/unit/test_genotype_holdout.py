"""Lock the holdout-generation contract.

The most important test in this file is ``test_v01_holdout_sha_is_canonical``
— it pins the exact SHA-256 of ``data/genotype/holdout500_ids.txt`` produced
by ``generate_holdout(seed=42)`` against the bundled panel snapshot. If the
random-draw implementation ever changes (e.g., a numpy RNG behavior change),
this test fails and the canonical record in ``docs/holdout-seed.md`` must
be updated under a new ``audit:`` commit per
``docs/scientific-integrity.md`` §2.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from genoadme.pgx.genotype import (
    HoldoutRecord,
    _stratified_targets,
    generate_holdout,
    load_holdout,
    load_thousand_genomes_holdout,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_BUNDLED_PANEL = (
    _REPO_ROOT / "data" / "genotype" / "integrated_call_samples_v3.20130502.ALL.panel"
)
_BUNDLED_HOLDOUT = _REPO_ROOT / "data" / "genotype" / "holdout500_ids.txt"

# Canonical record for v0.1.0 — see docs/holdout-seed.md.
_V01_PANEL_SHA = "b4023dc6ee2d62ee89c8d4d347db4d348e65518d66d346574cdae7a4bbd76858"
_V01_HOLDOUT_SHA = "1fcca63b0e674f53210ef16cf66a1d1a451d66dafe0121ae475e6fcf8c5616ed"
_V01_BREAKDOWN = {"AFR": 132, "AMR": 69, "EAS": 101, "EUR": 100, "SAS": 98}
_V01_FIRST_ID = "HG00114"
_V01_LAST_ID = "NA21135"


# ---------------------------------------------------------------------------
# Canonical-SHA regression — the most important test
# ---------------------------------------------------------------------------


def test_v01_holdout_sha_is_canonical(tmp_path: Path) -> None:
    """`generate_holdout(seed=42)` against the bundled panel must reproduce
    exactly the SHA recorded in docs/holdout-seed.md.

    If this fails, EITHER (a) numpy's default_rng behavior has changed
    OR (b) the algorithm in generate_holdout has drifted. Either way,
    the docs need to be updated and a new `audit:` commit logged.
    """
    out = tmp_path / "holdout.txt"
    log = tmp_path / "audit.jsonl"
    record = generate_holdout(
        seed=42,
        panel_path=_BUNDLED_PANEL,
        out_path=out,
        n=500,
        audit_log_path=log,
    )
    assert record.holdout_sha256 == _V01_HOLDOUT_SHA, (
        f"holdout SHA changed: {record.holdout_sha256} != {_V01_HOLDOUT_SHA}. "
        f"If numpy RNG behavior changed, update docs/holdout-seed.md under "
        f"a new audit: commit and rotate the seed if needed."
    )
    assert record.panel_sha256 == _V01_PANEL_SHA
    assert record.super_pop_breakdown == _V01_BREAKDOWN
    assert record.first_id == _V01_FIRST_ID
    assert record.last_id == _V01_LAST_ID


def test_bundled_holdout_file_matches_canonical_sha() -> None:
    """The committed `data/genotype/holdout500_ids.txt` must hash to the
    canonical v0.1.0 SHA. Catches accidental edits to the holdout file.
    """
    if not _BUNDLED_HOLDOUT.exists():
        pytest.skip("Bundled holdout file not committed yet")
    actual = hashlib.sha256(_BUNDLED_HOLDOUT.read_bytes()).hexdigest()
    assert actual == _V01_HOLDOUT_SHA


# ---------------------------------------------------------------------------
# Determinism / properties
# ---------------------------------------------------------------------------


def test_generate_holdout_is_deterministic(tmp_path: Path) -> None:
    out1 = tmp_path / "h1.txt"
    out2 = tmp_path / "h2.txt"
    log = tmp_path / "log.jsonl"
    r1 = generate_holdout(42, _BUNDLED_PANEL, out1, n=500, audit_log_path=log)
    r2 = generate_holdout(42, _BUNDLED_PANEL, out2, n=500, audit_log_path=log)
    assert r1.holdout_sha256 == r2.holdout_sha256
    assert out1.read_text() == out2.read_text()


def test_different_seed_produces_different_holdout(tmp_path: Path) -> None:
    out1 = tmp_path / "h1.txt"
    out2 = tmp_path / "h2.txt"
    log = tmp_path / "log.jsonl"
    r1 = generate_holdout(42, _BUNDLED_PANEL, out1, n=500, audit_log_path=log)
    r2 = generate_holdout(7, _BUNDLED_PANEL, out2, n=500, audit_log_path=log)
    assert r1.holdout_sha256 != r2.holdout_sha256


def test_holdout_count_is_n(tmp_path: Path) -> None:
    out = tmp_path / "h.txt"
    log = tmp_path / "log.jsonl"
    record = generate_holdout(
        42, _BUNDLED_PANEL, out, n=500, audit_log_path=log
    )
    assert sum(record.super_pop_breakdown.values()) == 500
    assert len(load_holdout(out)) == 500


def test_holdout_is_lex_sorted(tmp_path: Path) -> None:
    out = tmp_path / "h.txt"
    log = tmp_path / "log.jsonl"
    generate_holdout(42, _BUNDLED_PANEL, out, n=500, audit_log_path=log)
    ids = load_holdout(out)
    assert ids == sorted(ids)


def test_holdout_individuals_are_unique(tmp_path: Path) -> None:
    out = tmp_path / "h.txt"
    log = tmp_path / "log.jsonl"
    generate_holdout(42, _BUNDLED_PANEL, out, n=500, audit_log_path=log)
    ids = load_holdout(out)
    assert len(set(ids)) == len(ids)


def test_stratified_targets_largest_remainder() -> None:
    counts = {"AFR": 661, "AMR": 347, "EAS": 504, "EUR": 503, "SAS": 489}
    targets = _stratified_targets(counts, 500)
    assert sum(targets.values()) == 500
    # Match expected v0.1.0 breakdown bit-for-bit.
    assert targets == _V01_BREAKDOWN


def test_stratified_targets_handles_small_n(tmp_path: Path) -> None:
    counts = {"AFR": 100, "EUR": 100}
    targets = _stratified_targets(counts, 5)
    assert sum(targets.values()) == 5
    # Tie-broken lex (AFR comes before EUR), so on ties AFR gets the
    # extra slot. With equal counts, fractional remainders are equal,
    # so AFR gets the extra.
    assert targets["AFR"] >= targets["EUR"]


# ---------------------------------------------------------------------------
# Audit log integration
# ---------------------------------------------------------------------------


def test_generate_holdout_writes_audit_entry(tmp_path: Path) -> None:
    out = tmp_path / "h.txt"
    log = tmp_path / "audit.jsonl"
    generate_holdout(42, _BUNDLED_PANEL, out, n=500, audit_log_path=log)
    lines = log.read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["purpose"] == "holdout generation"
    assert entry["holdout_id_list"] == str(out)
    assert "generate_holdout" in entry["caller"]


# ---------------------------------------------------------------------------
# load_thousand_genomes_holdout
# ---------------------------------------------------------------------------


def test_load_thousand_genomes_holdout_attaches_super_pops() -> None:
    if not _BUNDLED_HOLDOUT.exists():
        pytest.skip("Bundled holdout file not committed yet")
    genotypes = load_thousand_genomes_holdout(_BUNDLED_HOLDOUT)
    assert len(genotypes) == 500
    # Every individual must have a known super-pop.
    super_pops = {g.super_population for g in genotypes}
    assert super_pops == {"AFR", "AMR", "EAS", "EUR", "SAS"}
    # calls is empty stub for v0.1.0.
    assert all(g.calls == {} for g in genotypes)


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------


def test_generate_holdout_rejects_oversized_n(tmp_path: Path) -> None:
    out = tmp_path / "h.txt"
    log = tmp_path / "log.jsonl"
    with pytest.raises(ValueError, match="cannot draw"):
        generate_holdout(42, _BUNDLED_PANEL, out, n=99999, audit_log_path=log)


def test_generate_holdout_rejects_malformed_panel(tmp_path: Path) -> None:
    bad = tmp_path / "bad.panel"
    bad.write_text("not\ta\tvalid\theader\n")
    out = tmp_path / "h.txt"
    log = tmp_path / "log.jsonl"
    with pytest.raises(ValueError, match="missing required column"):
        generate_holdout(42, bad, out, n=500, audit_log_path=log)
