:- module(guard, [main/0, validate_files/3]).

:- use_module(library(http/json)).
:- use_module(library(lists)).

main :-
    current_prolog_flag(argv, Argv),
    (   Argv = [CaseFile, OllamaFile, OutputBase]
    ->  validate_files(CaseFile, OllamaFile, OutputBase)
    ;   format(user_error,
               'usage: swipl -q -s guard.pl -g main -t halt -- CASE OLLAMA OUTPUT_BASE~n',
               []),
        halt(2)
    ).

validate_files(CaseFile, OllamaFile, OutputBase) :-
    catch(
        validate_files_(CaseFile, OllamaFile, OutputBase),
        Error,
        ( message_to_string(Error, Message),
          error_result(Message, Result),
          write_outputs(OutputBase, Result),
          halt(1)
        )
    ).

validate_files_(CaseFile, OllamaFile, OutputBase) :-
    read_json_file(CaseFile, Case),
    read_json_file(OllamaFile, Envelope),
    generated_dict(Envelope, Generated),
    validate(Case, Generated, Result),
    write_outputs(OutputBase, Result).

read_json_file(Path, Dict) :-
    setup_call_cleanup(
        open(Path, read, Stream, [encoding(utf8)]),
        json_read_dict(Stream, Dict),
        close(Stream)
    ).

generated_dict(Envelope, Generated) :-
    get_dict(response, Envelope, ResponseText),
    atom_string(ResponseAtom, ResponseText),
    atom_json_dict(ResponseAtom, Generated, []).

validate(Case, Generated, Result) :-
    source_facts(Case, Source),
    generated_facts(Generated, Produced),
    subtract(Source, Produced, Missing),
    subtract(Produced, Source, Unknown),
    text_atom(Case.domain, Domain),
    unsupported_predicates(Domain, Source, Unsupported),
    rule_violations(Domain, Source, RuleViolations0),
    sort(RuleViolations0, RuleViolations),
    symbolic_status(RuleViolations, SymbolicStatus),
    model_status(Generated, ModelStatus),
    decide(Missing, Unknown, Unsupported,
           SymbolicStatus, ModelStatus, Action),
    maplist(term_text, Missing, MissingText),
    maplist(term_text, Unknown, UnknownText),
    maplist(term_text, Unsupported, UnsupportedText),
    maplist(term_text, RuleViolations, ViolationText),
    Result = _{
        case_id: Case.id,
        domain: Case.domain,
        action: Action,
        symbolic_status: SymbolicStatus,
        model_status: ModelStatus,
        missing_facts: MissingText,
        unknown_facts: UnknownText,
        unsupported_predicates: UnsupportedText,
        violations: ViolationText
    }.

term_text(Term, Text) :-
    term_string(Term, Text, [quoted(true), numbervars(true)]).

source_facts(Case, Facts) :-
    maplist(normalize_fact, Case.source_facts, Facts0),
    sort(Facts0, Facts).

generated_facts(Generated, Facts) :-
    is_dict(Generated),
    get_dict(facts, Generated, RawFacts),
    is_list(RawFacts),
    maplist(normalize_fact, RawFacts, Facts0),
    sort(Facts0, Facts).

normalize_fact(Dict, fact(Predicate, Args)) :-
    get_dict(predicate, Dict, Predicate0),
    text_atom(Predicate0, Predicate),
    get_dict(args, Dict, Args0),
    is_list(Args0),
    maplist(normalize_arg, Args0, Args).

normalize_arg(Value, Value) :-
    number(Value),
    !.
normalize_arg(Value, Atom) :-
    text_atom(Value, Atom).

text_atom(Value, Atom) :-
    ( string(Value) -> atom_string(Atom, Value)
    ; atom(Value) -> Atom = Value
    ).

model_status(Generated, Status) :-
    get_dict(status, Generated, Raw),
    text_atom(Raw, Status),
    memberchk(Status, [valid, invalid]).

symbolic_status([], valid).
symbolic_status([_|_], invalid).

decide(Missing, Unknown, Unsupported, _, _, reject) :-
    ( Missing \= [] ; Unknown \= [] ; Unsupported \= [] ),
    !.
decide([], [], [], Status, Status, accept) :-
    !.
decide([], [], [], _, _, correct).

unsupported_predicates(Domain, Facts, Unsupported) :-
    findall(
        unsupported_predicate(Predicate),
        ( member(fact(Predicate, _), Facts),
          \+ allowed_predicate(Domain, Predicate)
        ),
        Unsupported0
    ),
    sort(Unsupported0, Unsupported).

allowed_predicate(person, born).
allowed_predicate(person, died).
allowed_predicate(family, born).
allowed_predicate(family, parent).
allowed_predicate(document, created).
allowed_predicate(document, modified).
allowed_predicate(document, valid_from).
allowed_predicate(document, valid_to).
allowed_predicate(archive, access).
allowed_predicate(archive, end_year).
allowed_predicate(archive, reference).
allowed_predicate(archive, start_year).
allowed_predicate(archive, title).
allowed_predicate(administration, applicant_age).
allowed_predicate(administration, deadline).
allowed_predicate(administration, fee).
allowed_predicate(administration, minimum_age).
allowed_predicate(administration, submitted).

rule_violations(person, Facts, Violations) :-
    !,
    findall(V, person_violation(Facts, V), Violations).
rule_violations(family, Facts, Violations) :-
    !,
    findall(V, family_violation(Facts, V), Violations).
rule_violations(document, Facts, Violations) :-
    !,
    findall(V, document_violation(Facts, V), Violations).
rule_violations(archive, Facts, Violations) :-
    !,
    findall(V, archive_violation(Facts, V), Violations).
rule_violations(administration, Facts, Violations) :-
    !,
    findall(V, administration_violation(Facts, V), Violations).
rule_violations(Domain, _, [unknown_domain(Domain)]).

has_fact(Facts, Predicate, Args) :-
    memberchk(fact(Predicate, Args), Facts).

person_violation(Facts, death_before_birth(Person)) :-
    has_fact(Facts, born, [Person, Born]),
    has_fact(Facts, died, [Person, Died]),
    Died < Born.
person_violation(Facts, birth_in_future(Person)) :-
    has_fact(Facts, born, [Person, Born]),
    Born > 2026.
person_violation(Facts, implausible_lifespan(Person)) :-
    has_fact(Facts, born, [Person, Born]),
    has_fact(Facts, died, [Person, Died]),
    Died - Born > 125.

family_violation(Facts, self_parent(Person)) :-
    has_fact(Facts, parent, [Person, Person]).
family_violation(Facts, parent_too_young(Parent, Child)) :-
    has_fact(Facts, parent, [Parent, Child]),
    has_fact(Facts, born, [Parent, ParentYear]),
    has_fact(Facts, born, [Child, ChildYear]),
    ParentYear + 12 > ChildYear.
family_violation(Facts, parent_born_after_child(Parent, Child)) :-
    has_fact(Facts, parent, [Parent, Child]),
    has_fact(Facts, born, [Parent, ParentYear]),
    has_fact(Facts, born, [Child, ChildYear]),
    ParentYear > ChildYear.

document_violation(Facts, modified_before_created(Document)) :-
    has_fact(Facts, created, [Document, Created]),
    has_fact(Facts, modified, [Document, Modified]),
    Modified @< Created.
document_violation(Facts, validity_interval_reversed(Document)) :-
    has_fact(Facts, valid_from, [Document, Start]),
    has_fact(Facts, valid_to, [Document, End]),
    End @< Start.

archive_violation(Facts, archival_interval_reversed(Unit)) :-
    has_fact(Facts, start_year, [Unit, Start]),
    has_fact(Facts, end_year, [Unit, End]),
    End < Start.
archive_violation(Facts, invalid_access_level(Unit, Access)) :-
    has_fact(Facts, access, [Unit, Access]),
    \+ memberchk(Access, [public, restricted, secret]).
archive_violation(Facts, missing_reference(Unit)) :-
    archive_unit(Facts, Unit),
    \+ has_fact(Facts, reference, [Unit, _]).
archive_violation(Facts, missing_title(Unit)) :-
    archive_unit(Facts, Unit),
    \+ has_fact(Facts, title, [Unit, _]).

archive_unit(Facts, Unit) :-
    has_fact(Facts, start_year, [Unit, _]),
    !.
archive_unit(Facts, Unit) :-
    has_fact(Facts, end_year, [Unit, _]),
    !.
archive_unit(Facts, Unit) :-
    has_fact(Facts, access, [Unit, _]).

administration_violation(Facts, below_minimum_age(Person, Procedure)) :-
    has_fact(Facts, applicant_age, [Person, Age]),
    has_fact(Facts, minimum_age, [Procedure, Minimum]),
    Age < Minimum.
administration_violation(Facts, submitted_after_deadline(Application)) :-
    has_fact(Facts, submitted, [Application, Submitted]),
    has_fact(Facts, deadline, [Application, Deadline]),
    Submitted @> Deadline.
administration_violation(Facts, negative_fee(Application)) :-
    has_fact(Facts, fee, [Application, Fee]),
    Fee < 0.

error_result(Message, _{
    case_id: unknown,
    domain: unknown,
    action: reject,
    symbolic_status: error,
    model_status: error,
    missing_facts: [],
    unknown_facts: [],
    unsupported_predicates: [],
    violations: [Message]
}).

write_outputs(Base, Result) :-
    atom_concat(Base, '.json', JsonPath),
    atom_concat(Base, '.decision', DecisionPath),
    setup_call_cleanup(
        open(JsonPath, write, Json, [encoding(utf8)]),
        json_write_dict(Json, Result, [width(0)]),
        close(Json)
    ),
    setup_call_cleanup(
        open(DecisionPath, write, Decision, [encoding(utf8)]),
        write_decision(Decision, Result),
        close(Decision)
    ).

write_decision(Stream, Result) :-
    format(Stream, 'case_id=~w~n', [Result.case_id]),
    format(Stream, 'domain=~w~n', [Result.domain]),
    format(Stream, 'action=~w~n', [Result.action]),
    format(Stream, 'symbolic_status=~w~n', [Result.symbolic_status]),
    format(Stream, 'model_status=~w~n', [Result.model_status]),
    atomic_list_concat(Result.violations, ',', Violations),
    format(Stream, 'violations=~w~n', [Violations]).
