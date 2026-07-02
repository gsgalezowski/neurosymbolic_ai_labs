# Neuro-Symbolic AI — pakiet replikacyjny laboratoriów

Ten folder jest przygotowany jako materiał do publikacji na GitHubie dla czytelników artykułu o Neuro-Symbolic AI.

Zawiera trzy grupy eksperymentów:

1. `main-qwen-prolog-lispworks/` — główny eksperyment z artykułu: lokalny LLM generuje kontrolowany JSON, a SWI-Prolog sprawdza fakty i reguły dziedzinowe. LispWorks jest wariantem interaktywnego orkiestratora.
2. `component-labs/` — mniejsze laboratoria komponentowe użyte w artykule: PyAerial, QWED, filtr ASP, Sort-of-CLEVR, Logic Tensor Networks, TorchLogic oraz lokalny wariant kontroli RAG przez Prolog.
3. `rag-prolog-source-gate/` — samodzielny snapshot eksperymentu RAG + Prolog. Nie zawiera prywatnego systemu RAG ani skanów.

## Najważniejszy eksperyment

Główne laboratorium znajduje się w:

```text
main-qwen-prolog-lispworks/
```

To ono odpowiada za tezę artykułu: nowe AI proponuje odpowiedź, a stara warstwa symboliczna kontroluje, czy odpowiedź wolno opublikować.

W skrócie:

- Ollama uruchamia lokalne modele `qwen2.5:7b` i `llama3.2:latest`,
- model generuje JSON zgodny ze schematem,
- SWI-Prolog porównuje fakty wejściowe i wygenerowane,
- reguły dziedzinowe wykrywają naruszenia,
- orkiestrator podejmuje decyzję `accept`, `correct` albo `reject`,
- pełny ślad audytowy jest zapisywany w `engineering_runs/`.

## Minimalne wymagania

Do głównego eksperymentu:

- Windows,
- Python 3.10 lub nowszy,
- SWI-Prolog,
- Ollama,
- modele Ollama: `qwen2.5:7b` oraz opcjonalnie `llama3.2:latest`.

Do wariantu interaktywnego:

- LispWorks Personal 8.0.1 lub zgodny LispWorks z obsługą `COMM:OPEN-TCP-STREAM`.

Do laboratoriów komponentowych wymagane są dodatkowe zależności opisane w `component-labs/README.md`.

## Szybki start: główny eksperyment

1. Uruchom Ollama.
2. Pobierz model:

```powershell
ollama pull qwen2.5:7b
```

3. Sprawdź SWI-Prolog:

```powershell
swipl --version
```

Jeżeli `swipl` nie jest w `PATH`, ustaw:

```powershell
$env:SWIPL="C:\Program Files\swipl\bin\swipl.exe"
```

4. Przejdź do folderu głównego eksperymentu:

```powershell
cd main-qwen-prolog-lispworks
```

5. Uruchom testy Prologa:

```powershell
swipl -q -g "run_tests,halt" -s test_guard.pl
```

6. Uruchom pełny przebieg inżynierski:

```powershell
python -m engineering_study.reproduce --models qwen2.5:7b --timeout 180
```

Pełny wariant porównawczy:

```powershell
python -m engineering_study.reproduce --models qwen2.5:7b llama3.2:latest --timeout 180
```

## Wyniki referencyjne

Dołączony przebieg referencyjny:

```text
main-qwen-prolog-lispworks/engineering_runs/engineering-20260701-210539/
```

Zawiera:

- `metrics.json`,
- `metrics.csv`,
- `results.csv`,
- `manifest.json`,
- `complete-trace-P04.json`,
- osobne katalogi dla przypadków modeli.

Wynik opisany w artykule:

| Model | Accuracy LLM | Coverage | Selective accuracy | Korekty | Odrzucenia |
|---|---:|---:|---:|---:|---:|
| qwen2.5:7b | 73,3% | 100,0% | 100,0% | 8 | 0 |
| llama3.2:latest | 56,7% | 96,7% | 100,0% | 12 | 1 |

To nie jest dowód, że Prolog „zna prawdę o świecie”. Prolog sprawdza zgodność z podanymi faktami i regułami. Jeżeli źródło wejściowe jest błędne albo brakuje reguły, walidator może zaakceptować błędny wynik.

## Co nie jest częścią repozytorium

Repozytorium nie zawiera:

- prywatnego systemu RAG,
- skanów ksiąg metrykalnych,
- kluczy API,
- dużych cudzych repozytoriów jako kopii ZIP,
- roboczych eksportów artykułu.

Tam, gdzie laboratorium korzysta z projektu open source innego autora, instrukcja wskazuje, jaki projekt trzeba pobrać osobno.

## Struktura

```text
github_neurosymbolic_ai_labs/
  main-qwen-prolog-lispworks/
  component-labs/
  rag-prolog-source-gate/
  README.md
  requirements.txt
  .gitignore
```

## Licencja i cytowanie

Ten pakiet zawiera autorskie skrypty replikacyjne i minimalne dane kontrolne przygotowane do artykułu. Cudze projekty open source należy pobierać z ich oryginalnych repozytoriów i używać zgodnie z ich licencjami.
