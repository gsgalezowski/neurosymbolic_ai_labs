# Główne laboratorium: Qwen/Llama + SWI-Prolog + LispWorks

To jest główny eksperyment opisany w artykule.

Architektura:

```text
rekord wejściowy
    -> lokalny LLM w Ollama
    -> kontrolowany JSON
    -> SWI-Prolog
    -> accept / correct / reject
    -> ślad audytowy
```

Python uruchamia serię pomiarową i zapisuje artefakty. Nie jest głównym kontrolerem merytorycznym. Kontrolę reguł wykonuje SWI-Prolog. LispWorks jest dołączony jako interaktywny wariant orkiestratora.

## Zawartość

- `cases.jsonl` — 30 rekordów testowych z pięciu domen.
- `guard.pl` — walidator faktów i reguł dziedzinowych w SWI-Prolog.
- `test_guard.pl` — testy jednostkowe bramki Prologa.
- `orchestrator.lisp` — interaktywny orkiestrator LispWorks.
- `engineering_study/` — runner eksperymentu, testy mutacyjne i fault injection.
- `engineering_runs/engineering-20260701-210539/` — referencyjny przebieg benchmarku.
- `visual-prolog-guard/` — porównawczy prototyp Visual Prolog, bez katalogów build.

## Wymagania

- Python 3.10 lub nowszy.
- SWI-Prolog.
- Ollama.
- Model `qwen2.5:7b`.
- Opcjonalnie model `llama3.2:latest`.

Sprawdzenie:

```powershell
python --version
swipl --version
ollama --version
ollama show qwen2.5:7b
```

Jeżeli `swipl` nie jest w `PATH`, ustaw zmienną środowiskową `SWIPL`:

```powershell
$env:SWIPL="C:\Program Files\swipl\bin\swipl.exe"
```

## Test bramki Prologa

```powershell
swipl -q -g "run_tests,halt" -s test_guard.pl
```

Test powinien zakończyć się bez błędów.

## Uruchomienie benchmarku

Jednomodelowo:

```powershell
python -m engineering_study.reproduce --models qwen2.5:7b --timeout 180
```

Porównanie dwóch modeli:

```powershell
python -m engineering_study.reproduce --models qwen2.5:7b llama3.2:latest --timeout 180
```

Runner wykonuje:

1. testy metodologiczne,
2. testy SWI-Prolog,
3. kontrolowane awarie,
4. testy mutacyjne reguł,
5. serię generacji przez Ollama,
6. obliczenie metryk,
7. zapis manifestu i pełnych śladów.

## Wynik referencyjny

Referencyjny przebieg:

```text
engineering_runs/engineering-20260701-210539/
```

Najważniejsze pliki:

- `metrics.json` — metryki zbiorcze,
- `metrics.csv` — metryki w tabeli,
- `results.csv` — wyniki per przypadek,
- `complete-trace-P04.json` — pełny ślad korekty,
- `manifest.json` — wersje, modele, seed, polecenie i skróty plików.

## Interpretacja

Eksperyment sprawdza, czy niezależna warstwa reguł może powstrzymać publikację odpowiedzi sprzecznej z faktami i regułami. Nie sprawdza prawdy encyklopedycznej. Fakty wejściowe są traktowane jako źródło zaufane.

## LispWorks

Wariant interaktywny:

```lisp
(load "orchestrator.lisp")
(neuro-qwen:run-experiment :limit 30)
```

W artykule LispWorks pokazuje klasyczną orkiestrację w duchu starego AI. Do pełnego benchmarku wystarczy runner Python + SWI-Prolog + Ollama.
