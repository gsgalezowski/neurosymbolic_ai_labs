% Fakty wygenerowane z lokalnego HTR RAG.
% ok: prawdziwy wynik RAG; pozostałe przypadki to kontrole negatywne.

% test_case
test_case(ok).
test_case(no_scan_line).
test_case(wrong_source).
test_case(risky_audit).

% claim_person
claim_person(ok, 'Gregorczyk Piotr').
claim_person(no_scan_line, 'Gregorczyk Piotr').
claim_person(wrong_source, 'Gregorczyk Piotr').
claim_person(risky_audit, 'Gregorczyk Piotr').

% cited_source
cited_source(ok, '25.jpg', 1).
cited_source(no_scan_line, '25.jpg', 1).
cited_source(wrong_source, '99.jpg', 1).
cited_source(risky_audit, '25.jpg', 1).

% source_candidate
source_candidate(ok, '25.jpg', 1, 0.7592, yes).
source_candidate(no_scan_line, '25.jpg', 1, 0.7592, yes).
source_candidate(wrong_source, '25.jpg', 1, 0.7592, yes).
source_candidate(risky_audit, '25.jpg', 1, 0.7592, yes).

% htr_line
htr_line(ok, '25.jpg', 1, 4, 'Gregorczyk Piotr').
htr_line(wrong_source, '25.jpg', 1, 4, 'Gregorczyk Piotr').
htr_line(risky_audit, '25.jpg', 1, 4, 'Gregorczyk Piotr').

% audit_risk
audit_risk(ok, low).
audit_risk(no_scan_line, low).
audit_risk(wrong_source, low).
audit_risk(risky_audit, high).

% hallucination_alerts
hallucination_alerts(ok, 0).
hallucination_alerts(no_scan_line, 0).
hallucination_alerts(wrong_source, 0).
hallucination_alerts(risky_audit, 1).

% page_warnings
page_warnings(ok, 0).
page_warnings(no_scan_line, 0).
page_warnings(wrong_source, 0).
page_warnings(risky_audit, 0).
