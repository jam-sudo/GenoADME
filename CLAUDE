# CLAUDE.md — GenoADME

Behavioral guidelines for Claude Code working on this repository.

**Tradeoff:** These guidelines bias toward caution and honesty over speed. For trivial tasks, use judgment. For anything that touches reported metrics, validation tiers, or holdout data, follow the integrity rules without exception.

-----

## Project in one paragraph

GenoADME is a pharmacogenomic extension of [Sisyphus](https://github.com/jam-sudo/Sisyphus): it ingests human ADME-gene variant data (1000 Genomes phase 3) and tissue eQTL effects (GTEx v8) to make Sisyphus’s ADME predictions genotype-conditional. Output is a distribution of plasma PK trajectories conditional on genotype, validated by reproducing pre-specified pharmacogenomic phenomena. Deliverable is a `pip`-installable package and a single-author Zenodo preprint. The repository is public and the preprint will be cited under the same author name as Sisyphus and Charon — inflated metrics here erode the integrity record those projects have built.

-----

## 1. Think Before Coding

Don’t assume. Don’t hide confusion. Surface tradeoffs.

- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don’t pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- Many design choices in GenoADME (eQTL mapping function, LD handling, tier assignments) are scientifically contested. Never silently pick one.

## 2. Simplicity First

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No “flexibility” or “configurability” that wasn’t requested.
- Sisyphus already implements ODE solving, ADME prediction, and Bayesian refinement. If you find yourself reimplementing any of these, stop.

## 3. Surgical Changes

Touch only what you must. Clean up only your own mess.

- Don’t refactor things that aren’t broken.
- Match existing style.
- Sisyphus is a dependency, not a fork. Never modify code inside the Sisyphus package; raise an issue instead.
- Every changed line should trace directly to the user’s request.

## 4. Goal-Driven Execution

Define success criteria. Loop until verified.

- “Add validation” → “Write tests for invalid inputs, then make them pass.”
- “Fix the bug” → “Write a test that reproduces it, then make it pass.”
- For multi-step tasks, state a brief plan with verifiable checks per step.

## 5. Scientific Integrity

**Non-negotiable.** GenoADME results will be cited under a real name in a real preprint. Do not let an automated commit erase the disclosure record.

→ See [`docs/scientific-integrity.md`](docs/scientific-integrity.md) for the full rules.

Quick reference:

- **Validation tiers (Tier 1/2/3)** are pre-specified before any validation runs. Post-hoc changes require an audit entry.
- **Holdout populations** are generated once with a committed seed and never reused for methodological choices.
- **Reported metric changes** require a `metric-change:` commit prefix and an audit comment.
- **eQTL-derived predictions** are research-only and never claimed as clinically actionable.
- **Cherry-picking audits** are tracked automatically and reported in the preprint, whatever the number.

## 6. Architecture Constraints

→ See [`docs/architecture.md`](docs/architecture.md) for the full constraints.

Quick reference:

- GenoADME wraps Sisyphus; it does not reimplement it.
- The PGx layer is composable and optional (no genotype → average-patient Sisyphus prediction).
- Tier 3 genes raise explicit errors, not silent fallbacks.
- dbGaP-restricted data must not appear in this repo.

## 7. Output and Reporting

→ See [`docs/reporting-standards.md`](docs/reporting-standards.md) for the full standards.

Quick reference:

- Validation runs produce dated, append-only reports.
- Headline metrics are exported to a machine-readable JSON for preprint inclusion.
- Old reports are not deleted; corrections are added with annotation.

## 8. Commit Discipline

→ See [`docs/commit-discipline.md`](docs/commit-discipline.md) for the full conventions.

Quick reference:

- Commit prefixes: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `audit:`, `metric-change:`, `tier-change:`.
- Commits touching validation logic, tier assignments, or holdout generation include a one-line audit rationale.

-----

**These guidelines are working if** validation results match what `genoadme validate` produces from a clean clone, every reported metric is reproducible from a documented seed, the preprint can be defended in a five-minute conversation with a skeptical reviewer who has read only the README and `docs/limitations.md`, and the audit log is dull.
