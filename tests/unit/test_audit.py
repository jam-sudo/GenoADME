"""Lock the audit log behavior.

The cherry-picking audit is the integrity hook that the preprint
Methods section reports against. If these tests pass on a green CI,
the audit log can be trusted to be append-only, JSONL-formatted, and
honest about non-existent holdouts.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from genoadme.audit import log_query


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
