"""Controlled fault injection; every infrastructure failure must fail closed."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from engineering_study.runner import (
    DEFAULT_SWIPL,
    fail_closed_guard,
    final_decision,
    load_cases,
    ollama_generate,
    validate_with_prolog,
)


class SlowHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        time.sleep(1.0)
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"response":"{}"}')
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            pass

    def log_message(self, *_args: Any) -> None:
        pass


def envelope(case: dict[str, Any], response: str) -> dict[str, Any]:
    return {"model": "fault-injection", "response": response, "done": True}


def run(output: Path) -> list[dict[str, Any]]:
    output.mkdir(parents=True, exist_ok=True)
    cases = load_cases()
    valid_case = cases[0]
    results: list[dict[str, Any]] = []

    server = ThreadingHTTPServer(("127.0.0.1", 0), SlowHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _, timing = ollama_generate(
        "fault-model",
        valid_case,
        endpoint=f"http://127.0.0.1:{server.server_port}/api/generate",
        timeout=0.1,
    )
    server.shutdown()
    timeout_guard, _ = fail_closed_guard(timing["error"])
    timeout_decision = final_decision(
        valid_case["expected_status"], None, timeout_guard
    )
    results.append(
        {
            "fault": "ollama_timeout",
            "observed": timeout_decision["final_action"],
            "passed": timeout_decision["final_action"] == "rejected",
            "detail": timing["error"],
        }
    )

    malformed = envelope(valid_case, "{this is not JSON")
    with TemporaryDirectory() as directory:
        guard, timing = validate_with_prolog(
            valid_case, malformed, Path(directory) / "malformed"
        )
    results.append(
        {
            "fault": "malformed_model_json",
            "observed": guard["action"],
            "passed": guard["action"] == "reject",
            "detail": "; ".join(guard["violations"]),
        }
    )

    good_generated = {
        "case_id": valid_case["id"],
        "facts": valid_case["source_facts"],
        "status": valid_case["expected_status"],
        "answer": "valid",
    }
    with TemporaryDirectory() as directory:
        guard, timing = validate_with_prolog(
            valid_case,
            envelope(valid_case, json.dumps(good_generated)),
            Path(directory) / "missing-swipl",
            swipl=Path(directory) / "missing-swipl.exe",
        )
    results.append(
        {
            "fault": "swipl_unavailable",
            "observed": guard["action"],
            "passed": guard["action"] == "reject" and not timing["ok"],
            "detail": "SWI-Prolog executable unavailable: <temporary-directory>\\missing-swipl.exe",
        }
    )

    unknown_case = {
        "id": "X01",
        "domain": "person",
        "source_facts": [{"predicate": "teleported", "args": ["jan", 2026]}],
        "expected_status": "invalid",
    }
    unknown_generated = {
        "case_id": "X01",
        "facts": unknown_case["source_facts"],
        "status": "valid",
        "answer": "valid",
    }
    with TemporaryDirectory() as directory:
        guard, _ = validate_with_prolog(
            unknown_case,
            envelope(unknown_case, json.dumps(unknown_generated)),
            Path(directory) / "unknown-predicate",
            swipl=DEFAULT_SWIPL,
        )
    results.append(
        {
            "fault": "unsupported_predicate",
            "observed": guard["action"],
            "passed": (
                guard["action"] == "reject"
                and bool(guard.get("unsupported_predicates"))
            ),
            "detail": json.dumps(guard, ensure_ascii=False),
        }
    )

    report = {
        "tests": results,
        "passed": sum(item["passed"] for item in results),
        "total": len(results),
    }
    (output / "fault-injection.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if report["passed"] != report["total"]:
        raise SystemExit("Fault injection failed")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return results


if __name__ == "__main__":
    run(Path(__file__).resolve().parents[1] / "engineering_runs" / "fault-injection")
