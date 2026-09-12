implement main
    open core

clauses
    run() :-
        stdio::write("Visual Prolog 11 - Neuro-Symbolic Guard\n"),
        stdio::write("=========================================\n"),
        stdio::writef("P01 person 1880-1950: %\n", personStatus(1880, 1950)),
        stdio::writef("P02 person 1880-1875: %\n", personStatus(1880, 1875)),
        stdio::writef(
            "A04 archive without reference: %\n",
            archiveStatus("Maps", "", 1800, 1850, "public")
        ),
        stdio::writef(
            "R04 submitted after deadline: %\n",
            administrationStatus(20, 18, "2026-05-20", "2026-05-15", 100)
        ),
        stdio::write("\nDecisions are deterministic and statically typed.\n").

clauses
    personStatus(Born, Died) = "invalid: death_before_birth" :-
        Died < Born,
        !.
    personStatus(Born, Died) = "invalid: implausible_lifespan" :-
        Died - Born > 125,
        !.
    personStatus(_, _) = "valid".

clauses
    archiveStatus(_, "", _, _, _) = "invalid: missing_reference" :-
        !.
    archiveStatus("", _, _, _, _) = "invalid: missing_title" :-
        !.
    archiveStatus(_, _, StartYear, EndYear, _) = "invalid: archival_interval_reversed" :-
        EndYear < StartYear,
        !.
    archiveStatus(_, _, _, _, Access) = "invalid: invalid_access_level" :-
        Access <> "public",
        Access <> "restricted",
        Access <> "secret",
        !.
    archiveStatus(_, _, _, _, _) = "valid".

clauses
    administrationStatus(Age, MinimumAge, _, _, _) = "invalid: below_minimum_age" :-
        Age < MinimumAge,
        !.
    administrationStatus(_, _, Submitted, Deadline, _) = "invalid: submitted_after_deadline" :-
        Submitted > Deadline,
        !.
    administrationStatus(_, _, _, _, Fee) = "invalid: negative_fee" :-
        Fee < 0,
        !.
    administrationStatus(_, _, _, _, _) = "valid".

end implement main

goal
    console::runUtf8(main::run).
