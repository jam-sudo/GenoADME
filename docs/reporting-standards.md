# Reporting Standards

This document expands [`CLAUDE.md` §7](../CLAUDE.md#7-output-and-reporting).

These rules govern what goes into the `reports/` directory. The directory is the public, append-only record of every validation run that produced a number anyone might cite.

-----

## 1. Append-only, dated reports

Every validation run produces a Markdown report at:

```
reports/validation-{tier}-{YYYYMMDD}.md
```

Where `{tier}` is `tier1`, `tier2`, or `all`, and `{YYYYMMDD}` is the date the validation was executed (UTC).

If two validation runs occur on the same date, suffix with `-{HHMM}` (e.g., `validation-tier1-20260612-1830.md`).

**Reports are never deleted.** A superseded result stays in the directory; the corrected result is added as a new dated report and the old report receives an annotation pointing to its replacement.

-----

## 2. Report contents

Each report begins with the verbatim disclaimer line:

```
> Research and educational tool only; not FDA-cleared.
```

Followed by these sections, in order:

1. **Run metadata** — git commit SHA, GenoADME version, Sisyphus version, holdout ID list reference, seed used, timestamp (UTC), command line invoked.
1. **Tier results table** — for each pre-specified pair, the predicted vs expected metric and pass/fail against the criterion in [`docs/validation-tiers.md`](validation-tiers.md).
1. **Population-level metrics** — AAFE, %within-2x, %within-3x, %CV reproduction error, with confidence intervals where applicable.
1. **Audit notes** — pointer to the cherry-picking audit log entry for this run, plus any deviations from the pre-specified protocol (there should be none on a Tier 1 final run).
1. **Corrections** — empty on first publication of the report. Populated only by later commits with a `metric-change:` or `audit:` prefix that supersede a number in this report.

-----

## 3. Headline metrics JSON

Each report has a paired machine-readable file:

```
reports/headline-metrics-{YYYYMMDD}.json
```

Schema (sketch — finalized when `genoadme.validate` is implemented):

```json
{
  "schema_version": "1",
  "report": "reports/validation-tier1-20260612.md",
  "git_sha": "<full SHA>",
  "genoadme_version": "0.1.0",
  "sisyphus_version": "<resolved version>",
  "holdout_id_list": "data/genotype/holdout500_ids.txt",
  "seed": 42,
  "timestamp_utc": "2026-06-12T18:30:00Z",
  "tier1": {
    "SLCO1B1/simvastatin": {
      "AAFE": 1.71,
      "carrier_vs_noncarrier_ratio": 2.31,
      "criterion_met": true
    },
    "NAT2/isoniazid":  { "...": "..." },
    "UGT1A1/irinotecan": { "...": "..." }
  },
  "tier2": { "...": "..." },
  "tier3": {
    "CYP2D6": "skipped (Tier 3)",
    "CYP3A4": "skipped (Tier 3)",
    "ABCB1":  "skipped (Tier 3)"
  },
  "cherry_picking_audit": {
    "queries_to_date": 47,
    "log": "reports/audit-log.jsonl"
  }
}
```

The preprint cites a specific `headline-metrics-*.json` by date and SHA. Every number in the preprint must come from a single such file.

-----

## 4. Cherry-picking audit log

```
reports/audit-log.jsonl
```

JSONL (one JSON object per line). Each line:

```json
{"ts":"2026-06-12T18:30:00Z","holdout_id_list":"data/genotype/holdout500_ids.txt","purpose":"tier 1 final run","git_sha":"<sha>","caller":"genoadme.validate.run_tier1"}
```

- Append-only. The file is never rewritten or compacted.
- Every entry includes a `purpose` string. Allowed values are documented in [`scientific-integrity.md`](scientific-integrity.md) §5; new purpose strings are added by `audit:` commits with rationale.
- The preprint Methods section reports the count and the distribution of `purpose` values.

-----

## 5. Corrections to a published report

If a number in a previously published report is found to be wrong:

1. The new validation run produces a fresh dated report (do not modify the old one).
1. The new report’s **Corrections** section identifies the old report and the specific number(s) being superseded.
1. The old report receives a single appended block at the bottom:
   ```markdown
   ----- 
   ## Superseded
   
   The metric `<name>` reported above (`<old value>`) is superseded by 
   `reports/validation-{tier}-{new date}.md` (`<new value>`). 
   See `metric-change:` commit `<sha>` for rationale.
   ```
1. The commit that produces all of the above uses the `metric-change:` prefix per [`commit-discipline.md`](commit-discipline.md) §3.

The original (now-superseded) numbers remain visible. The audit trail is more important than the cleanliness of the directory.

-----

## 6. What is *not* in `reports/`

- Sisyphus-side outputs. Those belong to the Sisyphus repo.
- Per-individual prediction trajectories. The holdout has 500 individuals × multiple drugs; storing all trajectories in-repo would explode the repository size. Trajectories are regeneratable from the seed and the validation command.
- Plot images. The preprint figures are generated from the JSON files at preprint-build time, not committed alongside the reports.