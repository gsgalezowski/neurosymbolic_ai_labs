"""Mutation testing of the executable SWI-Prolog rule base."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from engineering_study.runner import GUARD, load_cases, validate_with_prolog


MUTATIONS = [
    ("death_before_birth_direction", "Died < Born.", "Died > Born."),
    ("future_birth_direction", "Born > 2026.", "Born < 2026."),
    ("lifespan_direction", "Died - Born > 125.", "Died - Born < 125."),
    ("parent_age_direction", "ParentYear + 12 > ChildYear.", "ParentYear + 12 < ChildYear."),
    ("parent_chronology_direction", "ParentYear > ChildYear.", "ParentYear < ChildYear."),
    ("modified_date_direction", "Modified @< Created.", "Modified @> Created."),
    ("validity_interval_direction", "End @< Start.", "End @> Start."),
    ("archive_interval_direction", "End < Start.", "End > Start."),
    ("minimum_age_direction", "Age < Minimum.", "Age > Minimum."),
    ("deadline_direction", "Submitted @> Deadline.", "Submitted @< Deadline."),
    ("negative_fee_direction", "Fee < 0.", "Fee > 0."),
    (
        "allow_unknown_archive_access",
        "\\+ memberchk(Access, [public, restricted, secret]).",
        "memberchk(Access, [public, restricted, secret]).",
    ),
]


def exact_envelope(case: dict[str, Any]) -> dict[str, Any]:
    generated = {
        "case_id": case["id"],
        "facts": case["source_facts"],
        "status": case["expected_status"],
        "answer": "oracle fixture",
    }
    return {
        "model": "oracle-fixture",
        "response": json.dumps(generated, ensure_ascii=False),
        "done": True,
    }


def evaluate_guard(guard: Path, work: Path) -> list[dict[str, Any]]:
    failures = []
    for case in load_cases():
        result, timing = validate_with_prolog(
            case, exact_envelope(case), work / case["id"], guard=guard
        )
        if (
            not timing["ok"]
            or result.get("symbolic_status") != case["expected_status"]
            or result.get("action") != "accept"
        ):
            failures.append(
                {
                    "case_id": case["id"],
                    "expected": case["expected_status"],
                    "symbolic_status": result.get("symbolic_status"),
                    "action": result.get("action"),
                    "violations": result.get("violations", []),
                }
            )
    return failures


def run(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    source = GUARD.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        baseline_failures = evaluate_guard(GUARD, temporary / "baseline")
        if baseline_failures:
            raise SystemExit(f"Baseline rule suite failed: {baseline_failures}")
        mutants = []
        for name, original, replacement in MUTATIONS:
            if source.count(original) != 1:
                raise SystemExit(
                    f"Mutation anchor {name!r} occurs {source.count(original)} times"
                )
            mutant_path = temporary / f"{name}.pl"
            mutant_path.write_text(
                source.replace(original, replacement, 1), encoding="utf-8"
            )
            failures = evaluate_guard(mutant_path, temporary / name)
            mutants.append(
                {
                    "name": name,
                    "killed": bool(failures),
                    "killing_cases": [item["case_id"] for item in failures],
                    "failure_count": len(failures),
                }
            )
    killed = sum(mutant["killed"] for mutant in mutants)
    report = {
        "baseline_cases": len(load_cases()),
        "baseline_failures": baseline_failures,
        "mutants": mutants,
        "killed": killed,
        "survived": len(mutants) - killed,
        "mutation_score": round(killed / len(mutants), 6),
    }
    (output / "mutation-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if killed != len(mutants):
        raise SystemExit("Some rule mutants survived")
    return report


if __name__ == "__main__":
    run(Path(__file__).resolve().parents[1] / "engineering_runs" / "mutation-tests")
