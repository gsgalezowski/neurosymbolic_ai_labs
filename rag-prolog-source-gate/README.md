# RAG + Prolog Source Gate

Minimalne laboratorium neuro-symboliczne do artykułu o kontrolowaniu odpowiedzi RAG regułami symbolicznymi.

Pakiet nie zawiera systemu RAG, bazy wektorowej ani skanów ksiąg. Zamiast tego zawiera mały snapshot faktów wyprowadzonych z jednego przebiegu RAG/HTR:

- pytanie: `Gregorczyk Piotr`,
- źródło wskazane przez RAG: `25.jpg`, strona `1`,
- linia HTR potwierdzająca wpis: `Gregorczyk Piotr`,
- audyt źródłowy: niskie ryzyko, zero alertów halucynacji, zero ostrzeżeń stron.

Celem laboratorium jest pokazanie, że odpowiedź wygenerowana przez RAG może zostać przepuszczona dalej tylko wtedy, gdy przejdzie jawną kontrolę Prologa.

## Co jest testowane

Reguły Prologa akceptują przypadek tylko wtedy, gdy spełnione są trzy warunki:

1. odpowiedź wskazuje cytowane źródło obecne w wynikach wyszukiwania,
2. cytowany dokument i strona zawierają linię HTR z szukaną osobą,
3. audyt źródłowy nie zgłasza ryzyka.

W snapshotcie są cztery przypadki:

| Przypadek | Oczekiwany wynik | Sens kontroli |
|---|---:|---|
| `ok` | `ACCEPT` | źródło, linia HTR i audyt są poprawne |
| `no_scan_line` | `REJECT` | brakuje potwierdzenia w linii HTR |
| `wrong_source` | `REJECT` | odpowiedź cytuje inny dokument niż kandydat źródłowy |
| `risky_audit` | `REJECT` | audyt sygnalizuje ryzyko |

## Wymagania

- Python 3.10 lub nowszy,
- jeden z interpreterów Prologa:
  - GNU Prolog, albo
  - SWI-Prolog.

Skrypt automatycznie próbuje znaleźć `gprolog`, `gprolog.exe`, `swipl` albo `swipl.exe` w `PATH`. Na Windowsie można też podać ścieżkę ręcznie.

## Uruchomienie

W katalogu tego laboratorium:

```powershell
python run_snapshot_audit.py
```

Jeśli Prolog nie jest w `PATH`, podaj ścieżkę:

```powershell
python run_snapshot_audit.py --prolog "<ścieżka-do-gprolog.exe>"
```

albo dla SWI-Prolog:

```powershell
python run_snapshot_audit.py --prolog "C:\Program Files\swipl\bin\swipl.exe"
```

## Oczekiwany wynik

```text
RAG snapshot -> Prolog source gate
query: Gregorczyk Piotr
cited source: 25.jpg, page 1
retrieval score: 0.7592
HTR line 4: Gregorczyk Piotr
audit: low hallucination_alerts=0 page_warnings=0

CASE ok: ACCEPT
CASE no_scan_line: REJECT reasons=[missing_scan_line]
CASE wrong_source: REJECT reasons=[missing_or_weak_cited_source, missing_scan_line]
CASE risky_audit: REJECT reasons=[audit_not_clean]
```

## Jak użyć własnych danych

1. Skopiuj `sample_observation.json` do nowego pliku, np. `my_observation.json`.
2. Zmień pola:
   - `query`,
   - `expected_document`,
   - `expected_page`,
   - `source_candidate`,
   - `htr_line`,
   - `audit`.
3. Uruchom:

```powershell
python run_snapshot_audit.py --input my_observation.json
```

## Co ten przykład pokazuje

To nie jest benchmark RAG ani test jakości OCR. To mały test architektoniczny:

- RAG/HTR dostarcza kandydatów i ślady źródłowe,
- Prolog niezależnie sprawdza warunki dopuszczenia odpowiedzi,
- brak dowodu źródłowego powoduje odrzucenie odpowiedzi.

W prawdziwym systemie `sample_observation.json` byłby generowany automatycznie po zapytaniu do RAG i po otwarciu skanu HTR. W tym repozytorium zostaje tylko snapshot, aby czytelnik mógł odtworzyć samą bramkę symboliczną bez dostępu do prywatnej bazy RAG.
