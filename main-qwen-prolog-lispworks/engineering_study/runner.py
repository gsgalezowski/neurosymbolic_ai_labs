"""Run real Ollama models through the real SWI-Prolog guard."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "cases.jsonl"
GUARD = ROOT / "guard.pl"
DEFAULT_SWIPL = Path(os.environ.get("SWIPL", "swipl"))
DEFAULT_ENDPOINT = "http://127.0.0.1:11434/api/generate"

RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "case_id": {"type": "string"},
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "predicate": {"type": "string"},
                    "args": {
                        "type": "array",
                        "items": {"anyOf": [{"type": "string"}, {"type": "number"}]},
                    },
                },
                "required": ["predicate", "args"],
            },
        },
        "status": {"type": "string", "enum": ["valid", "invalid"]},
        "answer": {"type": "string"},
    },
    "required": ["case_id", "facts", "status", "answer"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slug(text: str) -> str:
    return "".join(char if char.isalnum() or char in "-_." else "_" for char in text)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_cases(path: Path = CASES) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


def prompt_for(case: dict[str, Any]) -> str:
    model_input = {
        "id": case["id"],
        "domain": case["domain"],
        "question": case.get("question", ""),
        "source_facts": case["source_facts"],
    }
    return (
        "You normalize a source record into facts. Return only the JSON object "
        "required by the supplied schema. Copy every source_facts item exactly, "
        "without adding, deleting, renaming or changing any fact. Set case_id "
        "from the source. Decide whether the record is logically valid. Use "
        "status valid or invalid and give a short ASCII English answer.\n"
        "SOURCE RECORD:\n"
        + json.dumps(model_input, ensure_ascii=True, separators=(",", ":"))
    )


def request_payload(model: str, case: dict[str, Any], seed: int) -> dict[str, Any]:
    return {
        "model": model,
        "prompt": prompt_for(case),
        "stream": False,
        "format": RESPONSE_SCHEMA,
        "options": {"temperature": 0, "seed": seed},
    }


def ollama_generate(
    model: str,
    case: dict[str, Any],
    *,
    endpoint: str = DEFAULT_ENDPOINT,
    timeout: float = 180.0,
    seed: int = 42,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    payload = request_payload(model, case, seed)
    body = json.dumps(payload, ensure_ascii=True).encode("ascii")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            envelope = json.loads(response.read().decode("utf-8"))
        return envelope, {
            "ok": True,
            "error": "",
            "wall_ms": (time.perf_counter() - started) * 1000,
        }
    except (TimeoutError, socket.timeout, urllib.error.URLError, json.JSONDecodeError) as exc:
        return None, {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "wall_ms": (time.perf_counter() - started) * 1000,
        }


def fail_closed_guard(error: str, elapsed_ms: float = 0.0) -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        {
            "case_id": "unknown",
            "domain": "unknown",
            "action": "reject",
            "symbolic_status": "error",
            "model_status": "error",
            "missing_facts": [],
            "unknown_facts": [],
            "unsupported_predicates": [],
            "violations": [error],
        },
        {"ok": False, "error": error, "wall_ms": elapsed_ms, "returncode": None},
    )


def validate_with_prolog(
    case: dict[str, Any],
    envelope: dict[str, Any],
    artifact_dir: Path,
    *,
    swipl: Path = DEFAULT_SWIPL,
    guard: Path = GUARD,
    timeout: float = 30.0,
) -> tuple[dict[str, Any], dict[str, Any]]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    case_path = artifact_dir / "case.json"
    envelope_path = artifact_dir / "ollama-envelope.json"
    output_base = artifact_dir / "guard"
    case_path.write_text(json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8")
    envelope_path.write_text(
        json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    started = time.perf_counter()
    swipl_executable = str(swipl) if swipl.is_file() else shutil.which(str(swipl))
    if not swipl_executable:
        return fail_closed_guard(f"SWI-Prolog executable unavailable: {swipl}")
    try:
        completed = subprocess.run(
            [
                swipl_executable,
                "-q",
                "-s",
                str(guard),
                "-g",
                "main",
                "-t",
                "halt",
                "--",
                str(case_path),
                str(envelope_path),
                str(output_base),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        elapsed = (time.perf_counter() - started) * 1000
        return fail_closed_guard(f"{type(exc).__name__}: {exc}", elapsed)
    elapsed = (time.perf_counter() - started) * 1000
    result_path = output_base.with_suffix(".json")
    if not result_path.is_file():
        return fail_closed_guard(
            f"Guard produced no JSON; returncode={completed.returncode}; "
            f"stderr={completed.stderr.strip()}",
            elapsed,
        )
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return fail_closed_guard(f"Invalid guard JSON: {exc}", elapsed)
    return result, {
        "ok": completed.returncode == 0,
        "error": completed.stderr.strip(),
        "wall_ms": elapsed,
        "returncode": completed.returncode,
    }


def parse_generated(envelope: dict[str, Any] | None) -> tuple[dict[str, Any] | None, str]:
    if not envelope or not isinstance(envelope.get("response"), str):
        return None, "missing Ollama response field"
    try:
        generated = json.loads(envelope["response"])
    except json.JSONDecodeError as exc:
        return None, f"model response is not JSON: {exc}"
    if not isinstance(generated, dict):
        return None, "model response is not an object"
    return generated, ""


def final_decision(
    expected: str,
    generated: dict[str, Any] | None,
    guard: dict[str, Any],
) -> dict[str, Any]:
    model_status = generated.get("status") if generated else None
    model_correct = model_status == expected
    action = guard.get("action", "reject")
    if action == "accept":
        published_status = model_status
        final_action = "accepted"
    elif action == "correct" and guard.get("symbolic_status") in {"valid", "invalid"}:
        published_status = guard["symbolic_status"]
        final_action = "corrected"
    else:
        published_status = None
        final_action = "rejected"
    return {
        "model_status": model_status,
        "model_correct": model_correct,
        "guard_action": action,
        "final_action": final_action,
        "published_status": published_status,
        "published_correct": (
            published_status == expected if published_status is not None else None
        ),
    }


def run_case(
    model: str,
    case: dict[str, Any],
    run_dir: Path,
    *,
    endpoint: str = DEFAULT_ENDPOINT,
    timeout: float = 180.0,
    seed: int = 42,
    swipl: Path = DEFAULT_SWIPL,
    guard: Path = GUARD,
) -> dict[str, Any]:
    artifact_dir = run_dir / slug(model) / case["id"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    payload = request_payload(model, case, seed)
    (artifact_dir / "request.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    pipeline_started = time.perf_counter()
    envelope, ollama_timing = ollama_generate(
        model, case, endpoint=endpoint, timeout=timeout, seed=seed
    )
    generated, parse_error = parse_generated(envelope)
    if envelope is not None:
        (artifact_dir / "ollama-envelope.json").write_text(
            json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    if generated is not None:
        (artifact_dir / "generated.json").write_text(
            json.dumps(generated, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    if envelope is None or generated is None:
        guard_result, prolog_timing = fail_closed_guard(
            ollama_timing["error"] or parse_error
        )
    else:
        guard_result, prolog_timing = validate_with_prolog(
            case, envelope, artifact_dir, swipl=swipl, guard=guard
        )
    decision = final_decision(case["expected_status"], generated, guard_result)
    trace = {
        "timestamp_utc": utc_now(),
        "model": model,
        "case_id": case["id"],
        "domain": case["domain"],
        "expected_status": case["expected_status"],
        **decision,
        "parse_error": parse_error,
        "symbolic_status": guard_result.get("symbolic_status"),
        "violations": guard_result.get("violations", []),
        "ollama_ok": ollama_timing["ok"],
        "ollama_wall_ms": round(ollama_timing["wall_ms"], 3),
        "ollama_total_ms": round((envelope or {}).get("total_duration", 0) / 1e6, 3),
        "ollama_load_ms": round((envelope or {}).get("load_duration", 0) / 1e6, 3),
        "ollama_prompt_eval_ms": round(
            (envelope or {}).get("prompt_eval_duration", 0) / 1e6, 3
        ),
        "ollama_eval_ms": round((envelope or {}).get("eval_duration", 0) / 1e6, 3),
        "prompt_tokens": (envelope or {}).get("prompt_eval_count"),
        "generated_tokens": (envelope or {}).get("eval_count"),
        "prolog_ok": prolog_timing["ok"],
        "prolog_wall_ms": round(prolog_timing["wall_ms"], 3),
        "pipeline_wall_ms": round((time.perf_counter() - pipeline_started) * 1000, 3),
    }
    (artifact_dir / "trace.json").write_text(
        json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return trace


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> list[float]:
    if total == 0:
        return [0.0, 0.0]
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total)
        / denominator
    )
    return [round(max(0.0, centre - margin), 6), round(min(1.0, centre + margin), 6)]


def percentile(values: list[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def metrics_for(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    model_correct = sum(row["model_correct"] for row in rows)
    published = [row for row in rows if row["published_status"] is not None]
    published_correct = sum(row["published_correct"] for row in published)
    corrected = sum(row["final_action"] == "corrected" for row in rows)
    rejected = sum(row["final_action"] == "rejected" for row in rows)
    def timing(name: str) -> dict[str, float]:
        values = [float(row[name]) for row in rows]
        return {
            "median": round(percentile(values, 0.5), 3),
            "p95": round(percentile(values, 0.95), 3),
        }

    return {
        "cases": total,
        "model_accuracy": round(model_correct / total, 6) if total else 0.0,
        "model_accuracy_ci95_wilson": wilson(model_correct, total),
        "published": len(published),
        "coverage": round(len(published) / total, 6) if total else 0.0,
        "selective_accuracy": (
            round(published_correct / len(published), 6) if published else 0.0
        ),
        "selective_accuracy_ci95_wilson": wilson(published_correct, len(published)),
        "selective_risk": (
            round(1 - published_correct / len(published), 6) if published else 0.0
        ),
        "corrections": corrected,
        "correction_rate": round(corrected / total, 6) if total else 0.0,
        "rejections": rejected,
        "rejection_rate": round(rejected / total, 6) if total else 0.0,
        "latency_ms": {
            "ollama_wall": timing("ollama_wall_ms"),
            "ollama_reported_total": timing("ollama_total_ms"),
            "ollama_load": timing("ollama_load_ms"),
            "prompt_evaluation": timing("ollama_prompt_eval_ms"),
            "token_generation": timing("ollama_eval_ms"),
            "prolog_process": timing("prolog_wall_ms"),
            "pipeline": timing("pipeline_wall_ms"),
        },
    }


def command_output(command: list[str]) -> str:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        ).stdout.strip() or subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        ).stderr.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"{type(exc).__name__}: {exc}"


def write_manifest(
    run_dir: Path, models: list[str], seed: int, command: list[str]
) -> dict[str, Any]:
    manifest = {
        "created_utc": utc_now(),
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python": sys.version,
        "ollama_version": command_output(["ollama", "--version"]),
        "ollama_models": command_output(["ollama", "list"]),
        "swipl_version": command_output([str(DEFAULT_SWIPL), "--version"]),
        "models": models,
        "seed": seed,
        "endpoint": DEFAULT_ENDPOINT,
        "command": command,
        "files": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in [CASES, GUARD, Path(__file__), ROOT / "engineering_study" / "reproduce.py"]
        },
        "environment": {
            "processor": platform.processor(),
            "python_executable": sys.executable,
        },
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def write_results(run_dir: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    fields = list(rows[0]) if rows else []
    with (run_dir / "results.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_model[row["model"]].append(row)
    metrics = {model: metrics_for(items) for model, items in by_model.items()}
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (run_dir / "metrics.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "model",
                "cases",
                "model_accuracy",
                "coverage",
                "selective_accuracy",
                "selective_risk",
                "corrections",
                "rejections",
                "pipeline_median_ms",
                "pipeline_p95_ms",
                "prolog_median_ms",
                "prolog_p95_ms",
            ]
        )
        for model, metric in metrics.items():
            writer.writerow(
                [
                    model,
                    metric["cases"],
                    metric["model_accuracy"],
                    metric["coverage"],
                    metric["selective_accuracy"],
                    metric["selective_risk"],
                    metric["corrections"],
                    metric["rejections"],
                    metric["latency_ms"]["pipeline"]["median"],
                    metric["latency_ms"]["pipeline"]["p95"],
                    metric["latency_ms"]["prolog_process"]["median"],
                    metric["latency_ms"]["prolog_process"]["p95"],
                ]
            )
    return metrics


def write_engineering_report(
    run_dir: Path, metrics: dict[str, Any], models: list[str]
) -> None:
    lines = [
        "# Engineering study results",
        "",
        f"Run directory: `{run_dir}`",
        "",
        "## Model comparison",
        "",
        "| Model | Accuracy | 95% CI | Coverage | Selective accuracy | Selective risk | Corrected | Rejected | Pipeline median | Pipeline p95 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model in models:
        item = metrics[model]
        accuracy_ci = item["model_accuracy_ci95_wilson"]
        lines.append(
            f"| `{model}` | {item['model_accuracy']:.1%} | "
            f"{accuracy_ci[0]:.1%}-{accuracy_ci[1]:.1%} | "
            f"{item['coverage']:.1%} | {item['selective_accuracy']:.1%} | "
            f"{item['selective_risk']:.1%} | {item['corrections']} | "
            f"{item['rejections']} | "
            f"{item['latency_ms']['pipeline']['median']:.1f} ms | "
            f"{item['latency_ms']['pipeline']['p95']:.1f} ms |"
        )
    lines.extend(
        [
            "",
            "## Reproduction",
            "",
            "The manifest contains program versions, model inventory, command, seed and SHA-256 hashes.",
            "Raw requests, Ollama envelopes, generated JSON, Prolog outputs and traces are retained per case.",
        ]
    )
    (run_dir / "engineering-report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def run_benchmark(
    models: list[str],
    output_root: Path,
    *,
    seed: int = 42,
    timeout: float = 180.0,
    limit: int | None = None,
) -> Path:
    cases = load_cases()
    if limit is not None:
        cases = cases[:limit]
    run_dir = output_root / datetime.now().strftime("engineering-%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True)
    write_manifest(run_dir, models, seed, sys.argv)
    rows: list[dict[str, Any]] = []
    for model in models:
        for index, case in enumerate(cases, 1):
            print(f"[{model}] {index:02}/{len(cases)} {case['id']}", flush=True)
            rows.append(
                run_case(model, case, run_dir, timeout=timeout, seed=seed)
            )
            write_results(run_dir, rows)
    metrics = write_results(run_dir, rows)
    exemplar = next(
        (
            row
            for row in rows
            if row["model"] == models[0] and row["final_action"] == "corrected"
        ),
        rows[0],
    )
    exemplar_dir = run_dir / slug(exemplar["model"]) / exemplar["case_id"]
    bundle = {
        "source_case": json.loads((exemplar_dir / "case.json").read_text(encoding="utf-8")),
        "ollama_request": json.loads(
            (exemplar_dir / "request.json").read_text(encoding="utf-8")
        ),
        "raw_ollama_envelope": (
            json.loads(
                (exemplar_dir / "ollama-envelope.json").read_text(encoding="utf-8")
            )
            if (exemplar_dir / "ollama-envelope.json").is_file()
            else None
        ),
        "generated_object": (
            json.loads((exemplar_dir / "generated.json").read_text(encoding="utf-8"))
            if (exemplar_dir / "generated.json").is_file()
            else None
        ),
        "prolog_result": (
            json.loads((exemplar_dir / "guard.json").read_text(encoding="utf-8"))
            if (exemplar_dir / "guard.json").is_file()
            else None
        ),
        "final_trace": exemplar,
    }
    (run_dir / f"complete-trace-{exemplar['case_id']}.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_engineering_report(run_dir, metrics, models)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(run_dir)
    return run_dir
