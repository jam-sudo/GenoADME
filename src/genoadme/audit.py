"""Cherry-picking audit log.

Per ``docs/scientific-integrity.md`` §5, every execution that reads
holdout individual genotypes or returns a holdout-population metric is
recorded in ``reports/audit-log.jsonl``. The log is **append-only** and
forms part of the public integrity record reported in the preprint.

This module is one of the few in v0.1.0 that is fully implemented (not
stubbed) — the integrity contract requires the audit hook to exist
before any validation code can be allowed to read holdout data.

The 2026-05-01 reproducibility audit (``docs/limitations.md`` §10.2)
extended the schema to capture working-tree-clean state alongside
``git_sha``. The lesson it codifies: a SHA records HEAD at query time,
not working-tree state. Without the clean assertion, an audit entry can
be technically truthful (the SHA is the SHA) yet not strictly
reproducible from a fresh clone.
"""

from __future__ import annotations

import inspect
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from genoadme.errors import WorkingTreeNotCleanError

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_AUDIT_LOG: Path = _REPO_ROOT / "reports" / "audit-log.jsonl"


def _git_sha_at(repo_root: Path) -> str:
    """Return the HEAD SHA of *repo_root*, or ``"unknown"`` if unavailable."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return out.decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return "unknown"


def _git_sha() -> str:
    """Return the GenoADME repo HEAD SHA, or ``"unknown"`` if unavailable."""
    return _git_sha_at(_REPO_ROOT)


def _worktree_clean_at(repo_root: Path) -> bool | None:
    """Return ``True`` if *repo_root*'s working tree is clean, ``False`` if
    dirty, or ``None`` if the directory is not a git checkout / git is
    unavailable. ``git status --porcelain`` empty output means clean.
    """
    if not (repo_root / ".git").exists():
        return None
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return out.decode().strip() == ""
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _find_sisyphus_repo_root() -> Path | None:
    """Walk up from the imported ``sisyphus`` package to find a ``.git``
    ancestor, or return ``None`` if Sisyphus isn't installed as an
    editable git checkout (e.g., installed from a wheel).
    """
    try:
        import sisyphus  # type: ignore[import-not-found]
    except ImportError:
        return None
    pkg_dir = Path(sisyphus.__file__).resolve().parent
    for ancestor in pkg_dir.parents:
        if (ancestor / ".git").exists():
            return ancestor
    return None


def _collect_repo_states() -> dict[str, dict[str, str | bool | None]]:
    """Return ``{name: {"git_sha": ..., "worktree_clean": ...}}`` for every
    repository whose state is reproducibility-relevant to a GenoADME
    audit entry: GenoADME itself, plus Sisyphus when it is installed as
    an editable git checkout.

    Tests monkey-patch this to inject deterministic state.
    """
    states: dict[str, dict[str, str | bool | None]] = {
        "genoadme": {
            "git_sha": _git_sha_at(_REPO_ROOT),
            "worktree_clean": _worktree_clean_at(_REPO_ROOT),
        }
    }
    sisyphus_root = _find_sisyphus_repo_root()
    if sisyphus_root is not None:
        states["sisyphus"] = {
            "git_sha": _git_sha_at(sisyphus_root),
            "worktree_clean": _worktree_clean_at(sisyphus_root),
        }
    return states


def _is_validation_purpose(purpose: str) -> bool:
    """Validation purposes (``"tier 1 validation"`` etc.) are gated on a
    clean working tree by default. Other purposes (``"holdout
    generation"``, ``"unit test"``) record state but do not refuse.
    """
    return purpose.lower().startswith("tier")


def log_query(
    holdout_id_list: str | Path,
    purpose: str,
    caller: str | None = None,
    log_path: str | Path | None = None,
    allow_dirty: bool = False,
) -> None:
    """Append one entry to the cherry-picking audit log.

    The entry is one JSON object per line. Format matches
    ``docs/reporting-standards.md`` §4, extended 2026-05-01 with
    ``worktree_clean`` (GenoADME) and ``deps`` (pinned dependencies).

    Args:
        holdout_id_list: Path to the holdout IDs file. **Must exist on
            disk** — we refuse to log queries against a non-existent
            holdout because doing so would corrupt the integrity record
            with fake entries.
        purpose: Short string describing why the holdout is being queried.
            Allowed values are documented in
            ``docs/scientific-integrity.md`` §5; new values should be
            introduced via an ``audit:`` commit. Purposes starting with
            ``"tier"`` are gated on a clean working tree (see
            ``allow_dirty``).
        caller: Optional dotted path of the calling function. If not
            given, it is inferred from the call stack.
        log_path: Optional override for the audit log location (used by
            tests). Production code uses the default.
        allow_dirty: If ``True``, log the entry even when a participating
            repository's working tree is dirty. The entry will record
            ``worktree_clean: false`` so the dirtiness is preserved in
            the audit trail. Use only for exploratory runs that are
            already understood to be non-reproducible.

    Raises:
        FileNotFoundError: If ``holdout_id_list`` does not exist.
        WorkingTreeNotCleanError: If ``purpose`` is a validation purpose
            (prefix ``"tier"``), any participating repository is dirty,
            and ``allow_dirty`` is ``False``.
    """
    holdout_path = Path(holdout_id_list)
    if not holdout_path.exists():
        raise FileNotFoundError(
            f"Refusing to log audit entry: holdout file {holdout_path!s} "
            f"does not exist. The audit log records real holdout queries; "
            f"logging a fake one would corrupt the integrity record."
        )

    if caller is None:
        frame = inspect.stack()[1]
        module = frame.frame.f_globals.get("__name__", "?")
        caller = f"{module}.{frame.function}"

    states = _collect_repo_states()
    genoadme_state = states.get("genoadme", {})
    deps = {name: state for name, state in states.items() if name != "genoadme"}

    dirty_repos = [
        name for name, state in states.items() if state.get("worktree_clean") is False
    ]
    if dirty_repos and _is_validation_purpose(purpose) and not allow_dirty:
        raise WorkingTreeNotCleanError(
            f"Refusing to log {purpose!r} audit entry: working tree dirty in "
            f"{dirty_repos}. The 2026-05-01 reproducibility audit "
            f"(docs/limitations.md §10.2) requires validation runs to "
            f"execute from a strictly clean working tree. Commit or stash "
            f"changes, or pass allow_dirty=True for an explicitly-marked "
            f"exploratory run."
        )

    target = Path(log_path) if log_path is not None else DEFAULT_AUDIT_LOG
    target.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "holdout_id_list": str(holdout_path),
        "purpose": purpose,
        "git_sha": genoadme_state.get("git_sha", "unknown"),
        "caller": caller,
        "worktree_clean": genoadme_state.get("worktree_clean"),
        "deps": deps,
    }

    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    logger.info("audit: logged holdout query (purpose=%s)", purpose)
