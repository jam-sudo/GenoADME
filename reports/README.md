# `reports/`

Append-only public record of every validation run.

The format and rules for what lives here are in [`../docs/reporting-standards.md`](../docs/reporting-standards.md).

## Files

- `validation-{tier}-{YYYYMMDD}.md` — one Markdown report per validation run.
- `headline-metrics-{YYYYMMDD}.json` — paired machine-readable headline metrics, cited by date in the preprint.
- `audit-log.jsonl` — append-only cherry-picking audit log (one JSON object per line). See [`../docs/scientific-integrity.md`](../docs/scientific-integrity.md) §5.

## Status

Empty in v0.1.0 skeleton, except for `audit-log.jsonl` which is committed as an empty file so the path exists for the audit hook in `genoadme.audit.log_query`.

## Rules

- **Reports are never deleted.** A superseded result stays in this directory; the corrected result is added as a new dated report.
- **The audit log is append-only.** New entries are always appended; no entry is rewritten or removed.
- The disclaimer line `> Research and educational tool only; not FDA-cleared.` appears at the top of every Markdown report.
