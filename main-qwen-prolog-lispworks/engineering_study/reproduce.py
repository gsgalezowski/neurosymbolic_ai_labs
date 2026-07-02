"""One-command reproduction of tests, fault injection and model benchmark."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from engineering_study import fault_injection, mutation_tests
from engineering_study.runner import DEFAULT_SWIPL, ROOT, run_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models", nargs="+", default=["qwen2.5:7b", "llama3.2:latest"]
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output-root", type=Path, default=ROOT / "engineering_runs"
    )
    args = parser.parse_args()
    session = args.output_root / datetime.now().strftime("verification-%Y%m%d-%H%M%S")
    session.mkdir(parents=True)

    python_unit = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "engineering_study.test_runner",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    (session / "python-unit-tests.txt").write_text(
        python_unit.stdout + python_unit.stderr, encoding="utf-8"
    )
    if python_unit.returncode:
        raise SystemExit("Python methodology tests failed")

    unit = subprocess.run(
        [
            str(DEFAULT_SWIPL),
            "-q",
            "-s",
            str(ROOT / "test_guard.pl"),
            "-g",
            "run_tests",
            "-t",
            "halt",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    (session / "swipl-unit-tests.txt").write_text(
        unit.stdout + unit.stderr, encoding="utf-8"
    )
    if unit.returncode:
        raise SystemExit("SWI-Prolog unit tests failed")

    fault_injection.run(session)
    mutation_tests.run(session)
    benchmark = run_benchmark(
        args.models,
        args.output_root,
        seed=args.seed,
        timeout=args.timeout,
        limit=args.limit,
    )
    report = {
        "python_unit_tests": "passed",
        "swipl_unit_tests": "passed",
        "fault_injection": str(session / "fault-injection.json"),
        "mutation_testing": str(session / "mutation-report.json"),
        "benchmark": str(benchmark),
    }
    (session / "reproduction-result.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
