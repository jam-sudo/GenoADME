"""Lock the audit log behavior.

The cherry-picking audit is the integrity hook that the preprint
Methods section reports against. If these tests pass on a green CI,
the audit log can be trusted to be append-only, JSONL-formatted,
honest about non-existent holdouts, and to refuse validation-purpose
entries when a participating repo's working tree is dirty.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from genoadme import audit as audit_mod
from genoadme.audit import log_query
from genoadme.errors import GenoADMEError, WorkingTreeNotCleanError


def test_log_query_appends_one_jsonl_line(tmp_path: Path) -> None:
    holdout = tmp_path / "holdout500_ids.txt"
    holdout.write_text("HG00096\nHG00097\n")
    log = tmp_path / "audit-log.jsonl"

    log_query(holdout, purpose="unit test", log_path=log)

    lines = log.read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["purpose"] == "unit test"
    assert entry["holdout_id_list"] == str(holdout)
    assert "ts" in entry and entry["ts"].endswith("Z")
    assert "git_sha" in entry
    assert "caller" in entry


def test_log_query_is_append_only(tmp_path: Path) -> None:
    holdout = tmp_path / "holdout500_ids.txt"
    holdout.write_text("HG00096\n")
    log = tmp_path / "audit-log.jsonl"

    log_query(holdout, purpose="first", log_path=log)
    log_query(holdout, purpose="second", log_path=log)
    log_query(holdout, purpose="third", log_path=log)

    lines = log.read_text().splitlines()
    assert len(lines) == 3
    purposes = [json.loads(line)["purpose"] for line in lines]
    assert purposes == ["first", "second", "third"]


def test_log_query_refuses_missing_holdout(tmp_path: Path) -> None:
    log = tmp_path / "audit-log.jsonl"
    nonexistent = tmp_path / "does_not_exist.txt"

    with pytest.raises(FileNotFoundError) as exc:
        log_query(nonexistent, purpose="bogus", log_path=log)
    assert "Refusing to log audit entry" in str(exc.value)
    assert not log.exists() or log.read_text() == ""


def test_log_query_creates_parent_dir(tmp_path: Path) -> None:
    holdout = tmp_path / "holdout500_ids.txt"
    holdout.write_text("HG00096\n")
    log = tmp_path / "nested" / "deep" / "audit-log.jsonl"

    log_query(holdout, purpose="dir-creation test", log_path=log)
    assert log.exists()
    assert json.loads(log.read_text().strip())["purpose"] == "dir-creation test"


def test_caller_is_inferred(tmp_path: Path) -> None:
    holdout = tmp_path / "holdout500_ids.txt"
    holdout.write_text("HG00096\n")
    log = tmp_path / "audit-log.jsonl"

    def some_inner_caller() -> None:
        log_query(holdout, purpose="inferred caller test", log_path=log)

    some_inner_caller()
    entry = json.loads(log.read_text().strip())
    assert "some_inner_caller" in entry["caller"]


def test_explicit_caller_overrides_inference(tmp_path: Path) -> None:
    holdout = tmp_path / "holdout500_ids.txt"
    holdout.write_text("HG00096\n")
    log = tmp_path / "audit-log.jsonl"

    log_query(holdout, purpose="x", caller="my.module.fn", log_path=log)
    entry = json.loads(log.read_text().strip())
    assert entry["caller"] == "my.module.fn"


# ---------------------------------------------------------------------------
# Working-tree-clean assertion (GenoADME issue #1, 2026-05-01 reproducibility
# audit lesson per docs/limitations.md §10.2). Tests monkey-patch
# _collect_repo_states so they are deterministic regardless of the actual
# state of the working repo running the suite.
# ---------------------------------------------------------------------------


def _patch_repo_states(monkeypatch, states: dict) -> None:
    monkeypatch.setattr(audit_mod, "_collect_repo_states", lambda: states)


def test_log_query_records_worktree_clean_field(tmp_path: Path, monkeypatch) -> None:
    _patch_repo_states(
        monkeypatch,
        {"genoadme": {"git_sha": "abc123", "worktree_clean": True}},
    )
    holdout = tmp_path / "holdout500_ids.txt"
    holdout.write_text("HG00096\n")
    log = tmp_path / "audit-log.jsonl"

    log_query(holdout, purpose="unit test", log_path=log)
    entry = json.loads(log.read_text().strip())
    assert entry["worktree_clean"] is True
    assert entry["git_sha"] == "abc123"
    assert entry["deps"] == {}


def test_log_query_records_deps_with_sisyphus_state(
    tmp_path: Path, monkeypatch
) -> None:
    _patch_repo_states(
        monkeypatch,
        {
            "genoadme": {"git_sha": "geno-sha", "worktree_clean": True},
            "sisyphus": {"git_sha": "sis-sha", "worktree_clean": True},
        },
    )
    holdout = tmp_path / "holdout500_ids.txt"
    holdout.write_text("HG00096\n")
    log = tmp_path / "audit-log.jsonl"

    log_query(holdout, purpose="unit test", log_path=log)
    entry = json.loads(log.read_text().strip())
    assert entry["deps"] == {
        "sisyphus": {"git_sha": "sis-sha", "worktree_clean": True}
    }


def test_log_query_refuses_dirty_working_tree_for_tier_purpose(
    tmp_path: Path, monkeypatch
) -> None:
    _patch_repo_states(
        monkeypatch,
        {"genoadme": {"git_sha": "geno-sha", "worktree_clean": False}},
    )
    holdout = tmp_path / "holdout500_ids.txt"
    holdout.write_text("HG00096\n")
    log = tmp_path / "audit-log.jsonl"

    with pytest.raises(WorkingTreeNotCleanError) as exc:
        log_query(holdout, purpose="tier 1 validation", log_path=log)
    assert "genoadme" in str(exc.value)
    assert not log.exists() or log.read_text() == ""


def test_log_query_refuses_dirty_sisyphus_for_tier_purpose(
    tmp_path: Path, monkeypatch
) -> None:
    """Even if GenoADME is clean, a dirty Sisyphus working tree blocks
    a tier-purpose entry — that is exactly the 2026-04-29 failure mode.
    """
    _patch_repo_states(
        monkeypatch,
        {
            "genoadme": {"git_sha": "geno-sha", "worktree_clean": True},
            "sisyphus": {"git_sha": "sis-sha", "worktree_clean": False},
        },
    )
    holdout = tmp_path / "holdout500_ids.txt"
    holdout.write_text("HG00096\n")
    log = tmp_path / "audit-log.jsonl"

    with pytest.raises(WorkingTreeNotCleanError) as exc:
        log_query(holdout, purpose="tier 1 validation", log_path=log)
    assert "sisyphus" in str(exc.value)


def test_log_query_allow_dirty_overrides_for_tier_purpose(
    tmp_path: Path, monkeypatch
) -> None:
    _patch_repo_states(
        monkeypatch,
        {"genoadme": {"git_sha": "geno-sha", "worktree_clean": False}},
    )
    holdout = tmp_path / "holdout500_ids.txt"
    holdout.write_text("HG00096\n")
    log = tmp_path / "audit-log.jsonl"

    log_query(holdout, purpose="tier 1 validation", log_path=log, allow_dirty=True)
    entry = json.loads(log.read_text().strip())
    assert entry["worktree_clean"] is False


def test_log_query_does_not_gate_non_tier_purposes(
    tmp_path: Path, monkeypatch
) -> None:
    """A dirty working tree during ``"holdout generation"`` or unit-test
    purposes is recorded (``worktree_clean: false``) but does not raise.
    Validation runs are the gated case; everything else is just logged.
    """
    _patch_repo_states(
        monkeypatch,
        {"genoadme": {"git_sha": "geno-sha", "worktree_clean": False}},
    )
    holdout = tmp_path / "holdout500_ids.txt"
    holdout.write_text("HG00096\n")
    log = tmp_path / "audit-log.jsonl"

    log_query(holdout, purpose="holdout generation", log_path=log)
    entry = json.loads(log.read_text().strip())
    assert entry["worktree_clean"] is False
    assert entry["purpose"] == "holdout generation"


def test_log_query_unknown_clean_state_does_not_gate(
    tmp_path: Path, monkeypatch
) -> None:
    """``worktree_clean is None`` (e.g., Sisyphus installed from wheel)
    is treated as 'unknown', not 'dirty'. The gate fires only on a
    confirmed dirty tree — no false-positive blocks for users who
    installed via PyPI.
    """
    _patch_repo_states(
        monkeypatch,
        {"genoadme": {"git_sha": "geno-sha", "worktree_clean": None}},
    )
    holdout = tmp_path / "holdout500_ids.txt"
    holdout.write_text("HG00096\n")
    log = tmp_path / "audit-log.jsonl"

    log_query(holdout, purpose="tier 1 validation", log_path=log)
    entry = json.loads(log.read_text().strip())
    assert entry["worktree_clean"] is None


def test_working_tree_not_clean_error_is_genoadme_error() -> None:
    assert issubclass(WorkingTreeNotCleanError, GenoADMEError)
