"""Validation entry points keyed to tier.

v0.1.0 implements ``run_tier1`` (SLCO1B1/pravastatin). The runner
orchestrates Sisyphus's lower-level building blocks per the pattern
established in ``sisyphus/tests/integration/test_slco1b1_phenotype.py``:

    build_from_yaml → apply_phenotype_to_graph (per individual)
                    → build_drug_on_graph (with OATP1B1 ECM kwargs)
                    → ODECompiler.compile → solve → compute_endpoints

This route (b) of the (a)/(b) wiring decision is documented in
``docs/architecture.md`` §1; route (a) (extending Sisyphus's
top-level ``predict()`` to take ``phenotypes=`` and to auto-load ECM
params) is left to upstream Sisyphus discretion and not required by
v0.1.0.

Per ``docs/scientific-integrity.md`` §5, the runner calls
``genoadme.audit.log_query`` *before* reading individual genotypes —
even for failed runs and dry runs that never compute an ODE.
"""

from __future__ import annotations

import json
import math
import statistics
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from genoadme.audit import log_query
from genoadme.errors import HoldoutNotGeneratedError
from genoadme.pgx.genotype import Genotype, load_slco1b1_calls
from genoadme.pgx.phenotype import call_phenotype

# ---------------------------------------------------------------------------
# Constants pinned to the v0.1.0 Tier 1 spec
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_HOLDOUT_PATH: Path = _REPO_ROOT / "data" / "genotype" / "holdout500_ids.txt"
DEFAULT_SLCO1B1_CALLS: Path = (
    _REPO_ROOT / "data" / "genotype" / "slco1b1_rs4149056_holdout.tsv"
)
DEFAULT_REPORTS_DIR: Path = _REPO_ROOT / "reports"

PRAVASTATIN_SMILES: str = (
    "CC[C@@H](C)C(=O)O[C@@H]1C[C@H](C=C2[C@@H]1CC[C@H]"
    "([C@@H]2CC[C@H](C[C@H](CC(=O)O)O)O)C)O"
)
PRAVASTATIN_DOSE_MG: float = 40.0  # standard clinical dose; cf. Niemi 2006 protocol

# Published reference values for AAFE comparison.
# Source: Niemi 2006 (control SLCO1B1 *1B/*1B carriers, pravastatin 40 mg PO).
# These are EM/NM-population means; reported here as ``mg/L`` and
# ``mg*h/L`` to match Sisyphus's PKEndpoints units.
TIER1_REFERENCE = {
    "drug": "pravastatin",
    "dose_mg": 40.0,
    "population": "healthy volunteers, predominantly SLCO1B1 NM",
    "cmax_mg_per_L": 0.075,    # ≈ 75 ng/mL; Niemi 2006 controls
    "auc_mg_h_per_L": 0.250,   # ≈ 250 ng·h/mL; Niemi 2006 controls
    "citation": "Niemi M, et al. Pharmacogenet Genomics. 2006;16(11):801-8",
}

# Pre-spec criteria from docs/validation-tiers.md §Tier 1.
TIER1_CRITERIA = {
    "population_aafe_max": 2.0,
    "pm_em_auc_ratio_min": 1.4,
    "pm_em_auc_ratio_max": 2.5,
    "pm_em_cmax_ratio_min": 1.3,
}


# ---------------------------------------------------------------------------
# Holdout precondition (used by future tier runners too)
# ---------------------------------------------------------------------------


def _require_holdout(holdout_path: Path) -> None:
    """Raise ``HoldoutNotGeneratedError`` if the holdout file is missing."""
    if not holdout_path.exists():
        raise HoldoutNotGeneratedError(
            f"Holdout file {holdout_path!s} does not exist. "
            f"Generate it once via "
            f"genoadme.pgx.genotype.generate_holdout(seed=42, ...) per "
            f"docs/holdout-seed.md before any validation run."
        )


# ---------------------------------------------------------------------------
# Simulator protocol
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SimResult:
    """Per-individual simulated PK summary."""

    cmax_mg_per_L: float
    auc_mg_h_per_L: float


# A simulator is a callable that takes a phenotype label string ("EM"/"IM"/"PM")
# and returns a SimResult. Production uses ``_real_pravastatin_simulator``;
# tests inject a fake to avoid running 500 ODE solves.
Simulator = Callable[[str], SimResult]


def _real_pravastatin_simulator(
    dose_mg: float,
    seed: int,
) -> Simulator:
    """Build the per-individual pravastatin simulator from Sisyphus.

    The expensive setup (chemistry profile, ADME prediction, base
    physiology graph, OATP1B1 ECM parameters) is computed once and
    closed over. Each per-individual call only does the phenotype
    application + drug build + compile + solve.
    """
    import numpy as np

    import sisyphus  # for the bundled physiology YAML path
    import sisyphus.engine.flux  # noqa: F401 — register flux specs
    from sisyphus.engine.compiler import ODECompiler, ResolvedParams
    from sisyphus.engine.solver import solve
    from sisyphus.graph.builder import build_from_yaml
    from sisyphus.pk.endpoints import compute_endpoints
    from sisyphus.predict.adme import predict_adme
    from sisyphus.predict.chemistry import compute_profile
    from sisyphus.predict.ivive import build_drug_on_graph
    from sisyphus.predict.phenotype import apply_phenotype_to_graph
    from sisyphus.predict.transporter_db import (
        load_hepatic_ecm_params,
        load_oatp1b1_kinetics,
    )

    sis_root = Path(sisyphus.__file__).resolve().parent.parent.parent
    phys_yaml = sis_root / "data" / "physiology" / "reference_man.yaml"

    profile = compute_profile(PRAVASTATIN_SMILES)
    adme = predict_adme(profile)
    base_graph = build_from_yaml(phys_yaml)
    base_liver_enzymes = {
        tag: d.mean for tag, d in base_graph.nodes["liver"].enzymes.items()
    }
    transporter_kinetics = load_oatp1b1_kinetics("pravastatin")
    hepatic_ecm = load_hepatic_ecm_params("pravastatin")

    def sim(phenotype_label: str) -> SimResult:
        graph = apply_phenotype_to_graph(base_graph, {"SLCO1B1": phenotype_label})
        drug = build_drug_on_graph(
            profile,
            adme,
            dose_mg=dose_mg,
            route="oral",
            liver_enzymes=base_liver_enzymes,
            transporter_kinetics=transporter_kinetics,
            hepatic_ecm_params=hepatic_ecm,
        )
        rng = np.random.default_rng(seed)
        realized_graph = graph.sample(rng)
        realized_drug = drug.sample(rng)
        compiled = ODECompiler().compile(realized_graph)
        params = ResolvedParams(realized_graph, realized_drug)
        y0 = np.zeros(compiled.n_states)
        y0[compiled.state_index[drug.administration_node]] = drug.dose_mg
        result = solve(compiled, params, y0, t_span=(0, 24))
        if not result.solver_success:
            raise RuntimeError(
                f"ODE solver did not converge for SLCO1B1={phenotype_label}"
            )
        endpoints = compute_endpoints(result, observation_node="venous_blood")
        return SimResult(
            cmax_mg_per_L=float(endpoints.cmax.mean),
            auc_mg_h_per_L=float(endpoints.auc_0t.mean),
        )

    return sim


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _aafe(predicted: float, observed: float) -> float:
    """Absolute average fold-error for a single (pred, obs) pair.

    AAFE = max(pred/obs, obs/pred). For a single point this is trivially
    the fold-deviation; for a population it is the geometric mean of
    the per-point AAFEs. Here we use the single-point form against
    population-mean references.
    """
    if observed <= 0 or predicted <= 0:
        return math.inf
    return max(predicted / observed, observed / predicted)


def _aggregate(
    individuals: list[dict[str, Any]],
    reference: dict[str, Any] = TIER1_REFERENCE,
    criteria: dict[str, float] = TIER1_CRITERIA,
) -> dict[str, Any]:
    """Compute population-level metrics + criterion-pass flags."""
    by_pheno: dict[str, list[dict[str, Any]]] = {}
    for ind in individuals:
        by_pheno.setdefault(ind["phenotype_label"], []).append(ind)

    pheno_summary = {}
    for label, items in by_pheno.items():
        cmax = [i["cmax_mg_per_L"] for i in items if "cmax_mg_per_L" in i]
        auc = [i["auc_mg_h_per_L"] for i in items if "auc_mg_h_per_L" in i]
        pheno_summary[label] = {
            "n": len(items),
            "cmax_mg_per_L_mean": statistics.fmean(cmax) if cmax else None,
            "auc_mg_h_per_L_mean": statistics.fmean(auc) if auc else None,
        }

    # Pop-level mean across all individuals.
    all_cmax = [i["cmax_mg_per_L"] for i in individuals if "cmax_mg_per_L" in i]
    all_auc = [i["auc_mg_h_per_L"] for i in individuals if "auc_mg_h_per_L" in i]
    pop_cmax = statistics.fmean(all_cmax) if all_cmax else None
    pop_auc = statistics.fmean(all_auc) if all_auc else None

    aafe_cmax = (
        _aafe(pop_cmax, reference["cmax_mg_per_L"])
        if pop_cmax is not None
        else None
    )
    aafe_auc = (
        _aafe(pop_auc, reference["auc_mg_h_per_L"])
        if pop_auc is not None
        else None
    )

    em = pheno_summary.get("EM") or pheno_summary.get("NM")
    pm = pheno_summary.get("PM")
    pm_em_auc_ratio: float | None = None
    pm_em_cmax_ratio: float | None = None
    if (
        em is not None
        and pm is not None
        and (em_auc := em["auc_mg_h_per_L_mean"])
        and (pm_auc := pm["auc_mg_h_per_L_mean"])
    ):
        pm_em_auc_ratio = pm_auc / em_auc
    if (
        em is not None
        and pm is not None
        and (em_cmax := em["cmax_mg_per_L_mean"])
        and (pm_cmax := pm["cmax_mg_per_L_mean"])
    ):
        pm_em_cmax_ratio = pm_cmax / em_cmax

    # Criterion checks (None = unable to evaluate).
    crit = {
        "population_aafe_auc_pass": (
            aafe_auc <= criteria["population_aafe_max"]
            if aafe_auc is not None
            else None
        ),
        "pm_em_auc_ratio_in_band": (
            criteria["pm_em_auc_ratio_min"]
            <= pm_em_auc_ratio
            <= criteria["pm_em_auc_ratio_max"]
            if pm_em_auc_ratio is not None
            else None
        ),
        "pm_em_cmax_ratio_meets_min": (
            pm_em_cmax_ratio >= criteria["pm_em_cmax_ratio_min"]
            if pm_em_cmax_ratio is not None
            else None
        ),
    }
    overall_pass = (
        all(v is True for v in crit.values()) if all(v is not None for v in crit.values()) else None
    )

    return {
        "n_individuals": len(individuals),
        "phenotype_distribution": dict(
            Counter(i["phenotype_label"] for i in individuals)
        ),
        "phenotype_summary": pheno_summary,
        "population_cmax_mg_per_L_mean": pop_cmax,
        "population_auc_mg_h_per_L_mean": pop_auc,
        "aafe_cmax": aafe_cmax,
        "aafe_auc": aafe_auc,
        "pm_em_auc_ratio": pm_em_auc_ratio,
        "pm_em_cmax_ratio": pm_em_cmax_ratio,
        "criteria": criteria,
        "criterion_results": crit,
        "overall_pass": overall_pass,
        "reference": reference,
    }


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


_DISCLAIMER = "> Research and educational tool only; not FDA-cleared.\n"


def _write_tier1_report(
    summary: dict[str, Any],
    output_dir: Path,
    today: str,
    git_sha: str,
) -> tuple[Path, Path]:
    """Write the dated Markdown report + headline JSON. Returns paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / f"validation-tier1-{today}.md"
    json_path = output_dir / f"headline-metrics-{today}.json"

    md_lines = [
        f"# Tier 1 Validation Report — SLCO1B1 / pravastatin ({today})",
        "",
        _DISCLAIMER,
        "## Run metadata",
        "",
        f"- git SHA: `{git_sha}`",
        f"- timestamp (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- holdout: `data/genotype/holdout500_ids.txt`",
        f"- calls: `data/genotype/slco1b1_rs4149056_holdout.tsv`",
        f"- n individuals: {summary['n_individuals']}",
        f"- drug: pravastatin (`{PRAVASTATIN_SMILES}`)",
        f"- dose: {PRAVASTATIN_DOSE_MG} mg PO",
        "",
        "## Phenotype distribution",
        "",
    ]
    for label, count in sorted(summary["phenotype_distribution"].items()):
        md_lines.append(f"- {label}: {count}")
    md_lines += [
        "",
        "## Per-phenotype mean PK",
        "",
        "|Phenotype|n|Mean Cmax (mg/L)|Mean AUC (mg·h/L)|",
        "|---------|--|----------------|------------------|",
    ]
    for label in sorted(summary["phenotype_summary"]):
        s = summary["phenotype_summary"][label]
        cmax = s["cmax_mg_per_L_mean"]
        auc = s["auc_mg_h_per_L_mean"]
        md_lines.append(
            f"|{label}|{s['n']}|"
            f"{cmax:.4f}|{auc:.4f}|"
            if cmax is not None and auc is not None
            else f"|{label}|{s['n']}|—|—|"
        )
    md_lines += [
        "",
        "## Pre-specified criteria (docs/validation-tiers.md §Tier 1)",
        "",
        f"- Population AAFE (AUC) ≤ {summary['criteria']['population_aafe_max']}: "
        f"{summary['aafe_auc']:.3f} → "
        f"{'PASS' if summary['criterion_results']['population_aafe_auc_pass'] else 'FAIL'}"
        if summary["aafe_auc"] is not None
        else "- Population AAFE (AUC): unable to compute",
        f"- PM/EM AUC ratio in [{summary['criteria']['pm_em_auc_ratio_min']}, "
        f"{summary['criteria']['pm_em_auc_ratio_max']}]: "
        f"{summary['pm_em_auc_ratio']:.3f} → "
        f"{'PASS' if summary['criterion_results']['pm_em_auc_ratio_in_band'] else 'FAIL'}"
        if summary["pm_em_auc_ratio"] is not None
        else "- PM/EM AUC ratio: unable to compute (PM or EM group empty)",
        f"- PM/EM Cmax ratio ≥ {summary['criteria']['pm_em_cmax_ratio_min']}: "
        f"{summary['pm_em_cmax_ratio']:.3f} → "
        f"{'PASS' if summary['criterion_results']['pm_em_cmax_ratio_meets_min'] else 'FAIL'}"
        if summary["pm_em_cmax_ratio"] is not None
        else "- PM/EM Cmax ratio: unable to compute (PM or EM group empty)",
        "",
        f"**Overall: {'PASS' if summary['overall_pass'] else 'FAIL/PARTIAL'}**",
        "",
        "## Reference",
        "",
        f"- {summary['reference']['citation']}",
        f"- Reference Cmax: {summary['reference']['cmax_mg_per_L']} mg/L",
        f"- Reference AUC: {summary['reference']['auc_mg_h_per_L']} mg·h/L",
        f"- Reference population: {summary['reference']['population']}",
        "",
        "## Audit notes",
        "",
        f"- Cherry-picking audit log: `reports/audit-log.jsonl` line for "
        f"`purpose=\"tier 1 validation\"` with this git SHA.",
        f"- Pre-spec criteria committed in "
        f"`docs/validation-tiers.md` before this run.",
        "",
        "## Corrections",
        "",
        "*None at time of first publication.*",
        "",
    ]
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    try:
        report_str = str(md_path.relative_to(_REPO_ROOT))
    except ValueError:
        report_str = str(md_path)
    headline = {
        "schema_version": "1",
        "report": report_str,
        "git_sha": git_sha,
        "genoadme_version": "0.1.0",
        "holdout_id_list": "data/genotype/holdout500_ids.txt",
        "seed": 42,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tier1": {
            "SLCO1B1/pravastatin": {
                "n_individuals": summary["n_individuals"],
                "phenotype_distribution": summary["phenotype_distribution"],
                "population_cmax_mg_per_L_mean": summary[
                    "population_cmax_mg_per_L_mean"
                ],
                "population_auc_mg_h_per_L_mean": summary[
                    "population_auc_mg_h_per_L_mean"
                ],
                "aafe_cmax": summary["aafe_cmax"],
                "aafe_auc": summary["aafe_auc"],
                "pm_em_auc_ratio": summary["pm_em_auc_ratio"],
                "pm_em_cmax_ratio": summary["pm_em_cmax_ratio"],
                "criteria": summary["criteria"],
                "criterion_results": summary["criterion_results"],
                "overall_pass": summary["overall_pass"],
                "reference": summary["reference"],
            }
        },
        "tier2": "empty in v0.1.0",
        "tier3": {
            "CYP2D6": "skipped (Tier 3)",
            "CYP3A4": "skipped (Tier 3)",
            "ABCB1": "skipped (Tier 3)",
        },
        "cherry_picking_audit": {"log": "reports/audit-log.jsonl"},
    }
    json_path.write_text(
        json.dumps(headline, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return md_path, json_path


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def run_tier1(
    seed: int = 42,
    holdout_path: Path | None = None,
    slco1b1_calls_path: Path | None = None,
    output_dir: Path | None = None,
    dose_mg: float = PRAVASTATIN_DOSE_MG,
    simulator: Simulator | None = None,
    audit_log_path: Path | None = None,
    write_reports: bool = True,
) -> dict[str, Any]:
    """Run Tier 1 validation: SLCO1B1/pravastatin against the holdout.

    Per-individual workflow:

    1. Read rs4149056 call from the calls TSV.
    2. ``call_phenotype(genotype, "SLCO1B1")`` → EM / IM / PM.
    3. Apply phenotype to the body graph and run the Sisyphus
       OATP1B1-ECM pipeline (``simulator``).
    4. Record Cmax / AUC.

    Aggregation produces:

    - per-phenotype mean Cmax / AUC
    - population-level AAFE against the published reference
      (``TIER1_REFERENCE``)
    - PM vs EM ratios checked against ``TIER1_CRITERIA``.

    Args:
        seed: RNG seed for the per-individual ODE solve. v0.1.0 = 42.
        holdout_path: Path to ``holdout500_ids.txt``. Defaults to bundled.
        slco1b1_calls_path: Path to the rs4149056 TSV. Defaults to bundled.
        output_dir: Where to write
            ``validation-tier1-{date}.md`` and
            ``headline-metrics-{date}.json``. Defaults to ``reports/``.
        dose_mg: Pravastatin dose in mg. v0.1.0 = 40.0.
        simulator: Optional injection. Production callers pass ``None``
            (uses the real Sisyphus pipeline). Tests pass a fake
            simulator to avoid 500 ODE solves.
        audit_log_path: Optional override for the audit log location.
        write_reports: Set to ``False`` to skip writing the dated
            Markdown + JSON reports (useful for tests / exploratory
            runs that should not pollute ``reports/``).

    Returns:
        Headline summary dict matching the schema in
        ``docs/reporting-standards.md`` §3.

    Raises:
        HoldoutNotGeneratedError: If the holdout file is missing.
        FileNotFoundError: If the calls TSV is missing.
    """
    holdout_path = Path(holdout_path) if holdout_path else DEFAULT_HOLDOUT_PATH
    slco1b1_calls_path = (
        Path(slco1b1_calls_path) if slco1b1_calls_path else DEFAULT_SLCO1B1_CALLS
    )
    output_dir = Path(output_dir) if output_dir else DEFAULT_REPORTS_DIR

    _require_holdout(holdout_path)
    if not slco1b1_calls_path.exists():
        raise FileNotFoundError(
            f"SLCO1B1 calls file {slco1b1_calls_path!s} does not exist. "
            f"See data/genotype/README.md for the expected provenance."
        )

    # Audit log entry — first action that touches holdout state.
    log_query(
        holdout_path,
        purpose="tier 1 validation",
        caller="genoadme.validate.run_tier1",
        log_path=audit_log_path,
    )

    genotypes: list[Genotype] = load_slco1b1_calls(
        slco1b1_calls_path, holdout_id_path=holdout_path
    )

    if simulator is None:
        simulator = _real_pravastatin_simulator(dose_mg=dose_mg, seed=seed)

    individuals: list[dict[str, Any]] = []
    for g in genotypes:
        label = call_phenotype(g, "SLCO1B1")
        sim_result = simulator(label)
        individuals.append(
            {
                "sample_id": g.sample_id,
                "super_population": g.super_population,
                "phenotype_label": label,
                "cmax_mg_per_L": sim_result.cmax_mg_per_L,
                "auc_mg_h_per_L": sim_result.auc_mg_h_per_L,
            }
        )

    summary = _aggregate(individuals)

    if write_reports:
        from genoadme.audit import _git_sha as _capture_git_sha
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        md_path, json_path = _write_tier1_report(
            summary, output_dir, today=today, git_sha=_capture_git_sha()
        )
        summary["report_md"] = str(md_path)
        summary["report_json"] = str(json_path)

    return summary


def run_tier2(seed: int = 42, holdout_path: Path | None = None) -> dict:
    """Tier 2 is empty in v0.1.0 (see docs/validation-tiers.md)."""
    return {
        "tier": 2,
        "n_pairs": 0,
        "note": "Tier 2 is empty in v0.1.0. The originally-scoped pairs "
        "(CYP2C19/clopidogrel, CYP2C9/warfarin) are deferred — see "
        "docs/validation-tiers.md §Deferred.",
    }


def run_all(
    seed: int = 42,
    holdout_path: Path | None = None,
    slco1b1_calls_path: Path | None = None,
    output_dir: Path | None = None,
    simulator: Simulator | None = None,
    audit_log_path: Path | None = None,
    write_reports: bool = True,
) -> dict[str, Any]:
    """Run Tier 1 + acknowledge Tier 2 / Tier 3 status."""
    tier1 = run_tier1(
        seed=seed,
        holdout_path=holdout_path,
        slco1b1_calls_path=slco1b1_calls_path,
        output_dir=output_dir,
        simulator=simulator,
        audit_log_path=audit_log_path,
        write_reports=write_reports,
    )
    return {
        "tier1": tier1,
        "tier2": run_tier2(seed=seed, holdout_path=holdout_path),
        "tier3": {
            "CYP2D6": "Tier 3 — UnsupportedGeneError",
            "CYP3A4": "Tier 3 — UnsupportedGeneError",
            "ABCB1": "Tier 3 — UnsupportedGeneError",
        },
    }
