:- begin_tests(guard).

:- use_module(guard).
:- use_module(library(http/json)).

write_json(Path, Dict) :-
    setup_call_cleanup(
        open(Path, write, Stream, [encoding(utf8)]),
        json_write_dict(Stream, Dict, [width(0)]),
        close(Stream)
    ).

generated_response(Facts, Status, Envelope) :-
    atom_json_dict(Response, _{
        case_id:"T01",
        facts:Facts,
        status:Status,
        answer:"test"
    }, []),
    Envelope = _{response:Response, done:true}.

test(accept_consistent_record) :-
    tmp_file_stream(text, CasePath, CaseStream),
    close(CaseStream),
    tmp_file_stream(text, OllamaPath, OllamaStream),
    close(OllamaStream),
    tmp_file(neuro_guard, Base),
    Facts = [
        _{predicate:"born", args:["jan", 1900]},
        _{predicate:"died", args:["jan", 1980]}
    ],
    Case = _{id:"T01", domain:"person", source_facts:Facts},
    generated_response(Facts, "valid", Envelope),
    write_json(CasePath, Case),
    write_json(OllamaPath, Envelope),
    validate_files(CasePath, OllamaPath, Base),
    atom_concat(Base, '.json', ResultPath),
    setup_call_cleanup(
        open(ResultPath, read, Stream, [encoding(utf8)]),
        json_read_dict(Stream, Result),
        close(Stream)
    ),
    assertion(Result.action == "accept"),
    assertion(Result.symbolic_status == "valid").

test(correct_false_model_judgement) :-
    tmp_file_stream(text, CasePath, CaseStream),
    close(CaseStream),
    tmp_file_stream(text, OllamaPath, OllamaStream),
    close(OllamaStream),
    tmp_file(neuro_guard, Base),
    Facts = [
        _{predicate:"born", args:["jan", 1900]},
        _{predicate:"died", args:["jan", 1890]}
    ],
    Case = _{id:"T02", domain:"person", source_facts:Facts},
    generated_response(Facts, "valid", Envelope),
    write_json(CasePath, Case),
    write_json(OllamaPath, Envelope),
    validate_files(CasePath, OllamaPath, Base),
    atom_concat(Base, '.json', ResultPath),
    setup_call_cleanup(
        open(ResultPath, read, Stream, [encoding(utf8)]),
        json_read_dict(Stream, Result),
        close(Stream)
    ),
    assertion(Result.action == "correct"),
    assertion(Result.symbolic_status == "invalid").

test(reject_hallucinated_fact) :-
    tmp_file_stream(text, CasePath, CaseStream),
    close(CaseStream),
    tmp_file_stream(text, OllamaPath, OllamaStream),
    close(OllamaStream),
    tmp_file(neuro_guard, Base),
    Source = [_{predicate:"born", args:["jan", 1900]}],
    Produced = [
        _{predicate:"born", args:["jan", 1900]},
        _{predicate:"died", args:["jan", 1980]}
    ],
    Case = _{id:"T03", domain:"person", source_facts:Source},
    generated_response(Produced, "valid", Envelope),
    write_json(CasePath, Case),
    write_json(OllamaPath, Envelope),
    validate_files(CasePath, OllamaPath, Base),
    atom_concat(Base, '.json', ResultPath),
    setup_call_cleanup(
        open(ResultPath, read, Stream, [encoding(utf8)]),
        json_read_dict(Stream, Result),
        close(Stream)
    ),
    assertion(Result.action == "reject"),
    assertion(Result.unknown_facts \== []).

test(reject_unsupported_predicate) :-
    tmp_file_stream(text, CasePath, CaseStream),
    close(CaseStream),
    tmp_file_stream(text, OllamaPath, OllamaStream),
    close(OllamaStream),
    tmp_file(neuro_guard, Base),
    Facts = [_{predicate:"teleported", args:["jan", 2026]}],
    Case = _{id:"T04", domain:"person", source_facts:Facts},
    generated_response(Facts, "valid", Envelope),
    write_json(CasePath, Case),
    write_json(OllamaPath, Envelope),
    validate_files(CasePath, OllamaPath, Base),
    atom_concat(Base, '.json', ResultPath),
    setup_call_cleanup(
        open(ResultPath, read, Stream, [encoding(utf8)]),
        json_read_dict(Stream, Result),
        close(Stream)
    ),
    assertion(Result.action == "reject"),
    assertion(Result.unsupported_predicates \== []).

:- end_tests(guard).
