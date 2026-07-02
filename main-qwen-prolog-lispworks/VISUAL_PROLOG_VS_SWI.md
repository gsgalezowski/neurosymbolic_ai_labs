# Visual Prolog 11 a SWI-Prolog w laboratorium

## Wynik praktycznej próby

Visual Prolog 11:

- poprawnie otworzył projekt w IDE;
- skompilował natywny program x86 i x64;
- wykrył na etapie kompilacji niezadeklarowany predykat `contains/2`;
- uruchomił typowaną bramkę dla reguł osoby, archiwum i administracji;
- ma bibliotekę `pfc\web\json`, więc pełny port walidatora jest możliwy.

Prototyp znajduje się w `visual-prolog-guard/`.

## Porównanie

| Kryterium | SWI-Prolog | Visual Prolog 11 |
|---|---|---|
| Pełna bramka z laboratorium | działa dla 30 rekordów | prototyp reprezentatywnych reguł |
| JSON | `library(http/json)`, bardzo krótki kod | PFC JSON, wymaga typowanych klas i projektu |
| Integracja z LispWorks | pojedynczy skrypt `guard.pl` | natywny EXE i DLL runtime |
| Kontrola typów | głównie w czasie wykonania | kompilator statyczny |
| Czas startu, średnia 10 prób | ok. 17 ms | ok. 21 ms |
| Budowanie | brak etapu kompilacji | pierwsza kompilacja ok. 37 s |
| IDE | skromne / konsolowe | rozbudowane IDE, debugger, coverage |
| Reprodukowalność artykułu | bardzo dobra, open source | dobra po instalacji Personal Edition; wymaga osobnego środowiska projektowego |
| Wartość wizualna | niska | wysoka |

Aktywację zweryfikowano 15 czerwca 2026 r. Pasek tytułu IDE pokazuje
`Visual Prolog 11 Personal Edition`, bez wcześniejszego oznaczenia
`Unregistered`.

## Rekomendacja

Nie zastępować SWI-Prologu w głównym eksperymencie tylko ze względów
estetycznych. Obecna bramka SWI jest kompletna, przetestowana i łatwa do
odtworzenia przez czytelnika.

Visual Prolog warto wykorzystać w artykule jako:

1. ramkę porównawczą o statycznym typowaniu systemów symbolicznych;
2. zrzut profesjonalnego IDE z kodem reguł;
3. demonstrację natywnego, kompilowanego guardraila;
4. kierunek rozwoju, jeśli walidator ma zostać dostarczony jako zamknięty EXE.

Najlepszy układ publikacyjny:

`LispWorks + Qwen + SWI-Prolog` jako reprodukowalny eksperyment główny,
a `Visual Prolog 11` jako porównawczy prototyp przemysłowy.

## Co zwiększy wartość praktyczną artykułu

Najsilniejsze rozszerzenie nie polega na dodaniu kolejnego języka, lecz na
pokazaniu zachowania systemu w warunkach zbliżonych do wdrożenia:

1. udostępnić czytelnikowi jeden przypadek od wejścia JSON aż do decyzji i
   śladu audytowego;
2. dodać testy mutacyjne, które celowo usuwają lub odwracają reguły Prologa;
3. zmierzyć opóźnienie Qwen, walidatora i całego potoku osobno;
4. zasymulować timeout Ollamy, błąd JSON i niedostępność Prologa;
5. raportować accuracy, coverage, selective risk oraz liczbę korekt i odrzuceń;
6. porównać ten sam kontrakt danych na dwóch lokalnych modelach;
7. dołączyć wersje programów, seed, prompty, dane i polecenie odtwarzające wynik.
