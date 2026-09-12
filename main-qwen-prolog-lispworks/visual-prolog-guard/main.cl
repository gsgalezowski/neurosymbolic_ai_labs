class main
    open core

predicates
    run : runnable.
    personStatus : (integer Born, integer Died) -> string Status.
    archiveStatus : (string Title, string Reference, integer StartYear, integer EndYear, string Access) -> string Status.
    administrationStatus : (integer Age, integer MinimumAge, string Submitted, string Deadline, integer Fee) -> string Status.

end class main
