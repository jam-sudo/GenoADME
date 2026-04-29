"""Cherry-picking audit log.

Per ``docs/scientific-integrity.md`` §5, every execution that reads
holdout individual genotypes or returns a holdout-population metric is
recorded in ``reports/audit-log.jsonl``. The log is **append-only** and
forms part of the public integrity record reported in the preprint.

This module is one of the few in v0.1.0 that is fully implemented (not
stubbed) — the integrity contract requires the audit hook to exist
before any validation code can be allowed to read holdout data.
"""

from __future__ import annotations

import inspect
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_AUDIT_LOG: Path = _REPO_ROOT / "reports" / "audit-log.jsonl"


def _git_sha() -> str:
    """Return the current git SHA, or ``"unknown"`` if git is unavailable."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(_REPO_ROOT), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return out.decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return "unknown"


def log_query(
    holdout_id_list: str | Path,
    purpose: str,
    caller: str | None = None,
    log_path: str | Path | None = None,
) -> None:
    """Append one entry to the cherry-picking audit log.

    The entry is one JSON object per line. Format matches
    ``docs/reporting-standards.md`` §4.

    Args:
        holdout_id_list: Path to the holdout IDs file. **Must exist on
            disk** — we refuse to log queries against a non-existent
            holdout because doing so would corrupt the integrity record
            with fake entries.
        purpose: Short string describing why the holdout is being queried.
            Allowed values are documented in
            ``docs/scientific-integrity.md`` §5; new values should be
            introduced via an ``audit:`` commit.
        caller: Optional dotted path of the calling function. If not
            given, it is inferred from the call stack.
        log_path: Optional override for the audit log location (used by
            tests). Production code uses the default.

    Raises:
        FileNotFoundError: If ``holdout_id_list`` does not exist.
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

    target = Path(log_path) if log_path is not None else DEFAULT_AUDIT_LOG
    target.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "holdout_id_list": str(holdout_path),
        "purpose": purpose,
        "git_sha": _git_sha(),
        "caller": caller,
    }

    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    logger.info("audit: logged holdout query (purpose=%s)", purpose)
