% Neuro-symboliczna bramka źródłowa dla lokalnego HTR RAG.
% GNU Prolog 1.5.0.
%
% Plik rag_observation_facts.pl jest generowany przez run_rag_prolog_audit.py
% na podstawie prawdziwej odpowiedzi RAG i podglądu HTR skanu.

:- include('rag_observation_facts.pl').

has_cited_source(Case) :-
    cited_source(Case, Document, Page),
    source_candidate(Case, Document, Page, Score, yes),
    Score >= 0.50.

has_scan_line(Case) :-
    claim_person(Case, Person),
    cited_source(Case, Document, Page),
    htr_line(Case, Document, Page, _LineNo, Person).

audit_clean(Case) :-
    audit_risk(Case, low),
    hallucination_alerts(Case, 0),
    page_warnings(Case, 0).

accepted(Case) :-
    test_case(Case),
    has_cited_source(Case),
    has_scan_line(Case),
    audit_clean(Case).

rejection_reason(Case, missing_or_weak_cited_source) :-
    test_case(Case),
    \+ has_cited_source(Case).

rejection_reason(Case, missing_scan_line) :-
    test_case(Case),
    \+ has_scan_line(Case).

rejection_reason(Case, audit_not_clean) :-
    test_case(Case),
    \+ audit_clean(Case).

write_reasons([]).
write_reasons([R|Rs]) :-
    write(R),
    ( Rs = [] -> true ; write(', '), write_reasons(Rs) ).

run_case(Case) :-
    write('CASE '), write(Case), write(': '),
    ( accepted(Case) ->
        write('ACCEPT')
    ;
        write('REJECT reasons=['),
        findall(R, rejection_reason(Case, R), Reasons),
        write_reasons(Reasons),
        write(']')
    ),
    nl.

run_audit :-
    forall(test_case(Case), run_case(Case)).
