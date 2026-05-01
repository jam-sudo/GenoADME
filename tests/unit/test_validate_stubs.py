"""Lock the validation runner contract.

These tests use a fake simulator so the runner's orchestration is
verified without running 500 ODE solves. The real Sisyphus simulator
is exercised in a separate integration test (slow-marked).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from genoadme import audit as audit_mod
from genoadme.errors import HoldoutNotGeneratedError
from genoadme.validate import (
    SimResult,
    _aggregate,
    _require_holdout,
    run_all,
    run_tier1,
    run_tier2,
)


@pytest.fixture
def clean_repo_states(monkeypatch):
    """Insulate runner tests from the actual dev-repo working-tree state.

    The audit hook (GenoADME issue #1) refuses tier-purpose entries when
    the working tree is dirty. Tests must pass regardless of whether the
    dev who is running them has uncommitted changes — so we fake a clean
    state for every participating repo. The wiring of ``allow_dirty`` is
    covered by ``test_audit.py``; here we only verify the runner.
    """
    monkeypatch.setattr(
        audit_mod,
        "_collect_repo_states",
        lambda: {
            "genoadme": {"git_sha": "test-clean", "worktree_clean": True},
            "sisyphus": {"git_sha": "test-clean", "worktree_clean": True},
        },
    )


# ---------------------------------------------------------------------------
# Fake simulator
# ---------------------------------------------------------------------------


def _fake_simulator(label: str) -> SimResult:
    """Deterministic fake: PM > IM > EM, monotonic in OATP1B1 reduction.

    Calibrated so the population mean (when EM dominates 1000G) lands
    near the published Niemi 2006 reference (Cmax 0.075 mg/L, AUC 0.250
    mg·h/L) and the PM/EM ratios fall comfortably inside the v0.1.0
    Tier 1 pre-spec criteria. The exact numbers do not represent any
    real prediction — they exist so the orchestration test has a
    deterministic "passing" signal.
    """
    return {
        "EM": SimResult(cmax_mg_per_L=0.075, auc_mg_h_per_L=0.250),
        "IM": SimResult(cmax_mg_per_L=0.110, auc_mg_h_per_L=0.380),
        "PM": SimResult(cmax_mg_per_L=0.150, auc_mg_h_per_L=0.500),
    }[label]


# ---------------------------------------------------------------------------
# Pre-conditions
# ---------------------------------------------------------------------------


def test_run_tier1_raises_when_holdout_missing(tmp_path: Path) -> None:
    missing_holdout = tmp_path / "no_holdout.txt"
    with pytest.raises(HoldoutNotGeneratedError):
        run_tier1(holdout_path=missing_holdout, write_reports=False)


def test_run_tier1_raises_when_calls_missing(tmp_path: Path) -> None:
    holdout = tmp_path / "h.txt"
    holdout.write_text("HG00114\n")
    missing_calls = tmp_path / "no_calls.tsv"
    with pytest.raises(FileNotFoundError, match="SLCO1B1 calls"):
        run_tier1(
            holdout_path=holdout,
            slco1b1_calls_path=missing_calls,
            write_reports=False,
        )


def test_require_holdout_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(HoldoutNotGeneratedError) as exc:
        _require_holdout(tmp_path / "no.txt")
    assert "holdout-seed.md" in str(exc.value)


def test_require_holdout_passes_when_present(tmp_path: Path) -> None:
    p = tmp_path / "h.txt"
    p.write_text("HG00096\n")
    _require_holdout(p)  # no exception


# ---------------------------------------------------------------------------
# Orchestration with fake simulator
# ---------------------------------------------------------------------------


def _bundled_paths() -> tuple[Path, Path]:
    repo = Path(__file__).resolve().parent.parent.parent
    holdout = repo / "data" / "genotype" / "holdout500_ids.txt"
    calls = repo / "data" / "genotype" / "slco1b1_rs4149056_holdout.tsv"
    return holdout, calls


def test_run_tier1_against_bundled_data_with_fake_simulator(
    tmp_path: Path, clean_repo_states
) -> None:
    holdout, calls = _bundled_paths()
    if not (holdout.exists() and calls.exists()):
        pytest.skip("Bundled holdout / calls not committed")
    audit = tmp_path / "audit.jsonl"
    summary = run_tier1(
        holdout_path=holdout,
        slco1b1_calls_path=calls,
        output_dir=tmp_path / "reports",
        simulator=_fake_simulator,
        audit_log_path=audit,
        write_reports=True,
    )

    assert summary["n_individuals"] == 500
    assert sum(summary["phenotype_distribution"].values()) == 500
    # The bundled calls produce these counts (locked elsewhere too):
    assert summary["phenotype_distribution"] == {"EM": 413, "IM": 84, "PM": 3}

    # All criteria should be evaluable (PM=3 is enough for ratios).
    for k in (
        "population_aafe_auc_pass",
        "pm_em_auc_ratio_in_band",
        "pm_em_cmax_ratio_meets_min",
    ):
        assert summary["criterion_results"][k] is not None
    # With the fake simulator's design, all should pass.
    assert summary["criterion_results"]["population_aafe_auc_pass"] is True
    assert summary["criterion_results"]["pm_em_auc_ratio_in_band"] is True
    assert summary["criterion_results"]["pm_em_cmax_ratio_meets_min"] is True
    assert summary["overall_pass"] is True

    # Reports are written.
    assert Path(summary["report_md"]).exists()
    assert Path(summary["report_json"]).exists()
    headline = json.loads(Path(summary["report_json"]).read_text())
    assert "tier1" in headline
    assert headline["tier1"]["SLCO1B1/pravastatin"]["n_individuals"] == 500

    # Audit log got exactly one new entry for this run.
    lines = audit.read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["purpose"] == "tier 1 validation"
    assert "run_tier1" in entry["caller"]


def test_run_tier1_skip_reports_does_not_pollute_reports_dir(
    tmp_path: Path, clean_repo_states
) -> None:
    holdout, calls = _bundled_paths()
    if not (holdout.exists() and calls.exists()):
        pytest.skip("Bundled holdout / calls not committed")
    audit = tmp_path / "audit.jsonl"
    out = tmp_path / "should_not_be_written"
    summary = run_tier1(
        holdout_path=holdout,
        slco1b1_calls_path=calls,
        output_dir=out,
        simulator=_fake_simulator,
        audit_log_path=audit,
        write_reports=False,
    )
    assert "report_md" not in summary
    assert not out.exists()


# ---------------------------------------------------------------------------
# Aggregation edge cases
# ---------------------------------------------------------------------------


def test_aggregate_with_no_pm_returns_none_for_pm_em_ratio() -> None:
    individuals = [
        {
            "sample_id": "X1",
            "phenotype_label": "EM",
            "cmax_mg_per_L": 0.07,
            "auc_mg_h_per_L": 0.24,
        }
    ]
    summary = _aggregate(individuals)
    assert summary["pm_em_auc_ratio"] is None
    assert summary["pm_em_cmax_ratio"] is None
    assert summary["criterion_results"]["pm_em_auc_ratio_in_band"] is None
    # Overall "pass" cannot be determined when any criterion is None.
    assert summary["overall_pass"] is None


# ---------------------------------------------------------------------------
# Tier 2 / Tier 3 stubs (still expected behaviour for v0.1.0)
# ---------------------------------------------------------------------------


def test_run_tier2_announces_empty_v01() -> None:
    out = run_tier2()
    assert out["n_pairs"] == 0
    assert "Deferred" in out["note"]


def test_run_all_invokes_tier1_and_acks_tier2_3(
    tmp_path: Path, clean_repo_states
) -> None:
    holdout, calls = _bundled_paths()
    if not (holdout.exists() and calls.exists()):
        pytest.skip("Bundled holdout / calls not committed")
    audit = tmp_path / "audit.jsonl"
    out = run_all(
        holdout_path=holdout,
        slco1b1_calls_path=calls,
        output_dir=tmp_path / "reports",
        simulator=_fake_simulator,
        audit_log_path=audit,
        write_reports=True,
    )
    assert out["tier1"]["n_individuals"] == 500
    assert out["tier2"]["n_pairs"] == 0
    assert "CYP2D6" in out["tier3"]
