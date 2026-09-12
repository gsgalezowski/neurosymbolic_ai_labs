# Weryfikacja inżynierska laboratorium

## Jedno polecenie

```powershell
.\run_engineering_study.ps1 --models qwen2.5:7b llama3.2:latest
```

Polecenie wykonuje kolejno:

1. testy metodologii runnera, w tym test braku `expected_status` w promptach;
2. testy jednostkowe bramki SWI-Prolog;
3. cztery kontrolowane awarie z wymaganą decyzją `reject`;
4. 12 mutantów reguł uruchamianych na wszystkich 30 rekordach;
5. 60 rzeczywistych generacji przez lokalne API Ollamy;
6. obliczenie metryk i przedziałów Wilsona 95%;
7. zapis manifestu, surowych artefaktów i kompletnego śladu przypadku.

## Referencyjne przebiegi

Pakiet zawiera dwa pełne przebiegi 60-generacyjne opisane w artykule:

`engineering_runs/engineering-20260615-210630/`
`engineering_runs/engineering-20260701-210539/`

Pierwszy katalog odpowiada przebiegowi referencyjnemu, a drugi audytowi
powtórzeniowemu. Każdy przebieg obejmuje 30 rekordów przetworzonych przez
dwa modele, czyli 60 generacji.

## Wyniki

| Model | Accuracy LLM | 95% CI | Coverage | Selective accuracy | Selective risk | Korekty | Odrzucenia |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5:7b | 73,3% | 55,6-85,8% | 100,0% | 100,0% | 0,0% | 8 | 0 |
| llama3.2:latest | 56,7% | 39,2-72,6% | 96,7% | 100,0% | 0,0% | 12 | 1 |

W pierwszym przebiegu Llama uzyskała 60,0% trafności, 96,7% coverage,
11 korekt i 1 odrzucenie. W audycie powtórzeniowym uzyskała 56,7%
trafności, 96,7% coverage, 12 korekt i 1 odrzucenie.

Nie należy interpretować 100% selective accuracy jako dowodu kompletności.
Próba liczy 30 rekordów, a dolna granica przedziału Wilsona wynosi 88,6% dla
30 publikacji Qwena i 88,3% dla 29 publikacji Llamy.

## Audyt pojedynczego przypadku

`complete-trace-P04.json` łączy:

- rekord wejściowy;
- request wysłany do Ollamy;
- surową kopertę odpowiedzi;
- sparsowany obiekt modelu;
- wynik SWI-Prolog;
- końcową decyzję publikacyjną i czasy etapów.

Każdy z 60 przypadków ma dodatkowo osobny katalog zawierający `request.json`,
`ollama-envelope.json`, `generated.json`, `guard.json`, `guard.decision` i
`trace.json`.

## Fault injection

Raport `fault-injection.json` dokumentuje:

- timeout kontrolowanego serwera HTTP udającego Ollamę;
- odpowiedź modelu z uszkodzonym JSON;
- nieistniejącą ścieżkę do `swipl.exe`;
- predykat spoza listy dozwolonej dla domeny.

Wszystkie cztery scenariusze zakończyły się odrzuceniem odpowiedzi.

## Mutation testing

Raport `mutation-report.json` zawiera 12 zmian kierunku porównań lub warunków
reguł. Każdy mutant został uruchomiony jako rzeczywisty plik Prologa na
30 rekordach. Zabito 12/12 mutantów, więc mutation score wynosi 100%.

## Uczciwość metodologiczna

Wcześniejszy przebieg `runs/run-3990485808/` zawierał w promptach pole
`expected_status`. Został zachowany jako historia rozwoju, ale nie jest
podstawą porównania modeli. Finalny runner usuwa etykietę przed wysłaniem
rekordu, a zachowanie to jest chronione testem jednostkowym.
