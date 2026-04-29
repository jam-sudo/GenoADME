# Commit Discipline

This document expands [`CLAUDE.md` §8](../CLAUDE.md#8-commit-discipline).

The discipline below exists for one reason: every reported metric in the GenoADME preprint must be traceable to a single commit, and every methodologically meaningful change must be readable from `git log` alone — without having to open the diff.

-----

## 1. Commit prefixes

Every commit message starts with one of the following prefixes, followed by `: ` and a single-line summary.

|Prefix          |When to use                                                                                                                                                                                       |
|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|`feat:`         |New user-visible capability (new public function, new CLI flag, new validation tier entry point).                                                                                                 |
|`fix:`          |Bug fix that does **not** move a reported metric. If the fix would move a metric, use `metric-change:` instead.                                                                                   |
|`docs:`         |Documentation-only change (any file under `docs/`, `README.md`, or docstrings). No code or data behavior change.                                                                                  |
|`test:`         |Adding or modifying tests without changing production code.                                                                                                                                       |
|`refactor:`     |Internal restructuring with no behavior change. Must not move any reported metric — verify before committing.                                                                                     |
|`audit:`        |Updates to the cherry-picking audit log, holdout seed metadata, or other integrity-record files (`reports/audit-log.jsonl`, `docs/holdout-seed.md`, `docs/tier-changes.md`).                      |
|`metric-change:`|Code or data change that moves a reported metric. **Always** include old and new value in the commit message body. See [`docs/scientific-integrity.md`](scientific-integrity.md) §3.              |
|`tier-change:`  |Change to a drug-gene tier assignment after validation has run. Must be accompanied by an entry in [`docs/tier-changes.md`](tier-changes.md). See [`scientific-integrity.md`](scientific-integrity.md) §1.|

If a single change spans two prefixes (e.g., a `fix:` that turns out to move a metric), it becomes `metric-change:`. The stricter prefix wins.

-----

## 2. Audit rationale

Commits that touch any of the following must include a one-line audit rationale in the commit message body:

- Validation logic (`src/genoadme/validate.py`, anything under `src/genoadme/pgx/mapping.py`).
- Tier assignments ([`docs/validation-tiers.md`](validation-tiers.md)).
- Holdout generation or holdout seed metadata.
- Anything that contributes to a number reported in `README.md` or the preprint.

The rationale is a single sentence answering: *why was this change necessary?* Not *what changed* (that’s the diff) but *what would have gone wrong without it*.

-----

## 3. `metric-change:` body format

```
metric-change: <one-line summary>

old: <metric name> = <old value> (commit <sha-or-tag>)
new: <metric name> = <new value>
reason: <one or two sentences>
audit: <reports/validation-... or audit-log.jsonl entry>
```

Example:

```
metric-change: SLCO1B1/simvastatin AAFE 1.83 → 1.71

old: SLCO1B1/simvastatin AAFE = 1.83 (commit a1b2c3d)
new: SLCO1B1/simvastatin AAFE = 1.71
reason: eQTL beta sign flipped for rs4149056 due to ALT/REF
  convention mismatch in GTEx ingest.
audit: reports/validation-tier1-20260612.md (correction note)
```

The old value’s commit SHA is required so that the prior reported result is recoverable from `git checkout <sha>`.

-----

## 4. `tier-change:` body format

```
tier-change: <gene>/<drug> Tier <X> → Tier <Y>

trigger: <what validation result moved this pair>
old tier: <X>
new tier: <Y>
disclosure: <preprint section that will note the change>
audit: docs/tier-changes.md entry dated <YYYY-MM-DD>
```

A `tier-change:` commit also requires re-running every other validation case under the new methodology. The re-run results are reported in the next dated validation report.

-----

## 5. What never goes in a commit

- dbGaP-restricted data of any kind ([`architecture.md`](architecture.md) §4). If `git status` shows individual-level GTEx files, **stop and revert** before committing.
- Holdout individual genotype dumps. The holdout is referenced by ID list, not by inlined genotype data.
- API keys, tokens, or any credential. The repository is public.
- Reports generated from a holdout query that wasn’t logged through `genoadme.audit.log_query`.

-----

## 6. Amending and rewriting

- **Never** amend a commit that has been pushed to `main` or to a tagged release. The git history of `main` is part of the integrity record.
- For local-only commits (not yet pushed), `git commit --amend` is acceptable for fixing typos in the commit message itself.
- `git rebase -i` and history rewrites on `main` are not used. If a commit needs to be undone, use `git revert` (which leaves both the original and the revert in history).

-----

## 7. Squashing

- Pull requests are merged with a **merge commit**, not squash-merged. The individual commits are part of the audit trail.
- If a feature branch contains noisy WIP commits, clean them up via `git rebase -i` **before** opening the PR, while the branch is still local.