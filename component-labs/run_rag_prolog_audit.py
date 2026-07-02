import json
import os
import subprocess
from pathlib import Path

import requests


BASE_URL = "http://127.0.0.1:5000"
WORKSPACE_ID = "htrrag"
QUERY = "Gregorczyk Piotr"
EXPECTED_DOCUMENT = "25.jpg"
EXPECTED_PAGE = 1
MIN_SCORE = 0.50
GPROLOG = Path(os.environ.get("GPROLOG", "gprolog"))

HERE = Path(__file__).resolve().parent
FACTS = HERE / "rag_observation_facts.pl"
RULES = HERE / "rag_source_audit.pl"
REPORT = HERE / "rag_prolog_audit_result.json"


def prolog_atom(value: str) -> str:
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def post_json(path: str, payload: dict, timeout: int = 60) -> dict:
    r = requests.post(f"{BASE_URL}{path}", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def get_json(path: str, params: dict, timeout: int = 30) -> dict:
    r = requests.get(f"{BASE_URL}{path}", params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def find_expected_source(search_result: dict) -> dict:
    for source in search_result.get("sources", []):
        label = source.get("document_label") or source.get("document")
        if label == EXPECTED_DOCUMENT and int(source.get("page") or 1) == EXPECTED_PAGE:
            return source
    raise RuntimeError(f"Brak oczekiwanego źródła {EXPECTED_DOCUMENT}, s. {EXPECTED_PAGE}")


def scan_contains_person(document_id: str) -> tuple[bool, int | None, dict]:
    data = get_json(
        "/api/htr/scan-view",
        {"document_id": document_id, "workspace_id": WORKSPACE_ID},
    )
    for idx, line in enumerate(data.get("htr_lines") or [], start=1):
        if (line.get("text") or "").strip() == QUERY:
            return True, idx, data
    return False, None, data


def risk_atom(summary: dict) -> str:
    value = (summary.get("overall_support_risk") or "").strip().lower()
    return "low" if value == "niska" else "not_low"


def write_facts(search_result: dict, source: dict, line_no: int) -> None:
    summary = search_result.get("source_audit", {}).get("summary", {})
    score = float(source.get("score") or 0.0)
    alerts = int(summary.get("hallucination_alerts") or 0)
    warnings = int(summary.get("page_warnings") or 0)
    risk = risk_atom(summary)

    rows = {
        "test_case": [
            "test_case(ok).",
            "test_case(no_scan_line).",
            "test_case(wrong_source).",
            "test_case(risky_audit).",
        ],
        "claim_person": [
            f"claim_person(ok, {prolog_atom(QUERY)}).",
            f"claim_person(no_scan_line, {prolog_atom(QUERY)}).",
            f"claim_person(wrong_source, {prolog_atom(QUERY)}).",
            f"claim_person(risky_audit, {prolog_atom(QUERY)}).",
        ],
        "cited_source": [
            f"cited_source(ok, {prolog_atom(EXPECTED_DOCUMENT)}, {EXPECTED_PAGE}).",
            f"cited_source(no_scan_line, {prolog_atom(EXPECTED_DOCUMENT)}, {EXPECTED_PAGE}).",
            f"cited_source(wrong_source, {prolog_atom('99.jpg')}, {EXPECTED_PAGE}).",
            f"cited_source(risky_audit, {prolog_atom(EXPECTED_DOCUMENT)}, {EXPECTED_PAGE}).",
        ],
        "source_candidate": [
            f"source_candidate(ok, {prolog_atom(EXPECTED_DOCUMENT)}, {EXPECTED_PAGE}, {score:.4f}, yes).",
            f"source_candidate(no_scan_line, {prolog_atom(EXPECTED_DOCUMENT)}, {EXPECTED_PAGE}, {score:.4f}, yes).",
            f"source_candidate(wrong_source, {prolog_atom(EXPECTED_DOCUMENT)}, {EXPECTED_PAGE}, {score:.4f}, yes).",
            f"source_candidate(risky_audit, {prolog_atom(EXPECTED_DOCUMENT)}, {EXPECTED_PAGE}, {score:.4f}, yes).",
        ],
        "htr_line": [
            f"htr_line(ok, {prolog_atom(EXPECTED_DOCUMENT)}, {EXPECTED_PAGE}, {line_no}, {prolog_atom(QUERY)}).",
            f"htr_line(wrong_source, {prolog_atom(EXPECTED_DOCUMENT)}, {EXPECTED_PAGE}, {line_no}, {prolog_atom(QUERY)}).",
            f"htr_line(risky_audit, {prolog_atom(EXPECTED_DOCUMENT)}, {EXPECTED_PAGE}, {line_no}, {prolog_atom(QUERY)}).",
        ],
        "audit_risk": [
            f"audit_risk(ok, {risk}).",
            f"audit_risk(no_scan_line, {risk}).",
            f"audit_risk(wrong_source, {risk}).",
            "audit_risk(risky_audit, high).",
        ],
        "hallucination_alerts": [
            f"hallucination_alerts(ok, {alerts}).",
            f"hallucination_alerts(no_scan_line, {alerts}).",
            f"hallucination_alerts(wrong_source, {alerts}).",
            "hallucination_alerts(risky_audit, 1).",
        ],
        "page_warnings": [
            f"page_warnings(ok, {warnings}).",
            f"page_warnings(no_scan_line, {warnings}).",
            f"page_warnings(wrong_source, {warnings}).",
            f"page_warnings(risky_audit, {warnings}).",
        ],
    }

    facts = [
        "% Fakty wygenerowane z lokalnego HTR RAG.",
        "% ok: prawdziwy wynik RAG; pozostałe przypadki to kontrole negatywne.",
        "",
    ]
    for group_name, group_rows in rows.items():
        facts.append(f"% {group_name}")
        facts.extend(group_rows)
        facts.append("")
    FACTS.write_text("\n".join(facts), encoding="utf-8")


def run_prolog() -> str:
    executable = str(GPROLOG) if GPROLOG.exists() else None
    if executable is None:
        import shutil
        executable = shutil.which(str(GPROLOG))
    if executable is None:
        raise FileNotFoundError(f"Nie znaleziono GNU Prolog: {GPROLOG}")
    env = os.environ.copy()
    env["LINEDIT"] = "gui=no"
    proc = subprocess.run(
        [
            executable,
            "--consult-file",
            str(RULES),
            "--query-goal",
            "run_audit,halt",
        ],
        cwd=HERE,
        text=True,
        capture_output=True,
        timeout=30,
        env=env,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        raise RuntimeError(output)
    return output


def main() -> None:
    search_result = post_json(
        "/api/search",
        {
            "query": QUERY,
            "top_k": 5,
            "workspace_id": WORKSPACE_ID,
            "answer_language": "pl",
            "audit": True,
        },
        timeout=90,
    )
    source = find_expected_source(search_result)
    has_line, line_no, scan_data = scan_contains_person(source["document_id"])
    if not has_line or line_no is None:
        raise RuntimeError(f"Skan {EXPECTED_DOCUMENT} nie zawiera linii HTR: {QUERY}")

    write_facts(search_result, source, line_no)
    prolog_output = run_prolog()

    summary = search_result.get("source_audit", {}).get("summary", {})
    report = {
        "query": QUERY,
        "answer": search_result.get("answer"),
        "document": EXPECTED_DOCUMENT,
        "page": EXPECTED_PAGE,
        "score": source.get("score"),
        "document_id": source.get("document_id"),
        "htr_model": scan_data.get("htr_model"),
        "htr_line_number": line_no,
        "audit_summary": summary,
        "prolog_output": prolog_output,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("RAG -> Prolog source audit")
    print(f"query: {QUERY}")
    print(f"cited source: {EXPECTED_DOCUMENT}, page {EXPECTED_PAGE}")
    print(f"retrieval score: {float(source.get('score') or 0):.4f}")
    print(f"HTR line {line_no}: {QUERY}")
    print(
        "audit:",
        summary.get("overall_support_risk"),
        "hallucination_alerts=" + str(summary.get("hallucination_alerts")),
        "page_warnings=" + str(summary.get("page_warnings")),
    )
    print()
    print(prolog_output.strip())
    print()
    print(f"saved: {REPORT.name}")
    if "CASE ok: ACCEPT" not in prolog_output:
        raise RuntimeError("Prolog nie zaakceptował przypadku pozytywnego")
    for case in ("no_scan_line", "wrong_source", "risky_audit"):
        if f"CASE {case}: REJECT" not in prolog_output:
            raise RuntimeError(f"Prolog nie odrzucił kontroli negatywnej: {case}")


if __name__ == "__main__":
    main()
