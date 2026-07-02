# Dodatkowe laboratoria komponentowe

Ten folder zawiera małe skrypty sterujące użyte w artykule jako demonstracje różnych wariantów Neuro-Symbolic AI.

Nie są to pełne kopie cudzych repozytoriów. Skrypty zakładają, że odpowiednie projekty open source zostały pobrane obok katalogu `component-labs`, zgodnie ze strukturą użytą w artykule.

## Struktura oczekiwana przez skrypty

```text
repo-root/
  component-labs/
  pyaerial-main/
  qwed-verification-main/
  NeuroSymbolic-Pneumonia-Detection-main/
  steering_content_effects-main/
  torchlogic-main/
  ...
```

Jeżeli uruchamiasz skrypty z innej struktury katalogów, dostosuj zmienną `ROOT` albo ścieżki na początku danego pliku.

## Skrypty

| Skrypt | Cel |
|---|---|
| `run_pyaerial.py` | trening autoenkodera i ekstrakcja reguł z danych tabelarycznych |
| `run_qwed.py` | bezpieczny parser symboliczny jako granica zaufania |
| `run_pneumonia_asp.py` | izolowany test warstwy ASP projektu Pneumonia Detection |
| `run_visual_reasoning.py` | symboliczny executor na scenie Sort-of-CLEVR |
| `run_content_bias.py` | kontrola czterech grup danych o wiarygodności treści i poprawności formy |
| `run_ltn_wine.py` | uczenie predykatu w Logic Tensor Networks |
| `run_torchlogic_test.py` | testy predykatów TorchLogic |
| `run_rag_prolog_audit.py` | wariant lokalny RAG + Prolog użyty do zrzutu w artykule |

## Wyniki referencyjne

Dołączone zrzuty `*.png` pokazują rzeczywiste przebiegi użyte w artykule. Numeracja odpowiada selekcji materiałów wykorzystanych w tekście, dlatego nie musi tworzyć ciągłej sekwencji.

## Ważna uwaga o RAG

`run_rag_prolog_audit.py` wymaga lokalnego systemu HTR RAG i nie jest przeznaczony jako publiczny test bez danych. Czytelnikom bez dostępu do tego systemu należy polecić folder:

```text
../rag-prolog-source-gate/
```

Tam znajduje się wersja snapshotowa, która nie wymaga prywatnego RAG-a ani skanów.

## Instalacja zależności

Podstawowe zależności:

```powershell
pip install -r ../requirements.txt
```

Niektóre projekty mają własne wymagania. W takim przypadku instaluj zależności według instrukcji oryginalnego repozytorium.
