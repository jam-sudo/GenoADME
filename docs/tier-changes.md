# Tier Changes Log

This file is the **append-only audit log** for any post-validation change to a drug-gene tier assignment. Tier assignments are pre-specified in [`docs/validation-tiers.md`](validation-tiers.md) before validation runs.

The protocol that requires entries here is in [`docs/scientific-integrity.md`](scientific-integrity.md) §1 and the commit format is in [`docs/commit-discipline.md`](commit-discipline.md) §4.

The intent of this file is twofold:

1. Make any tier change visible from `git log --follow docs/tier-changes.md` alone.
1. Force an explicit disclosure step before a tier change is allowed to influence the headline numbers reported in the preprint.

-----

## How to add an entry

Append a new section to the bottom of this file (do **not** edit prior entries). One section per tier change. Every entry follows this template:

```markdown
## YYYY-MM-DD — <gene>/<drug>: Tier <X> → Tier <Y>

**Commit:** `<sha>`
**Trigger:** <which validation run, with report path>
**Old tier:** <X> (mapping methodology used)
**New tier:** <Y> (mapping methodology now applied)
**Rationale:** <2–4 sentences explaining why the tier change is honest rather than face-saving>
**Re-run scope:** <which other tier validations were re-run as a consequence>
**Disclosure:** <preprint section / README section that notes this change>
```

If a tier change requires re-running other validation cases, the resulting reports are listed under **Re-run scope**. The tier change is not considered “closed” until those reports exist in `reports/`.

-----

## Entries

*No tier changes recorded.*

The pre-specified tiers committed in [`docs/validation-tiers.md`](validation-tiers.md) are still the active assignments as of the latest commit on `main`.