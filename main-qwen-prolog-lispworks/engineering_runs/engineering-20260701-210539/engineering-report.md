# Engineering study results

Run directory: `engineering_runs/engineering-20260701-210539`

## Model comparison

| Model | Accuracy | 95% CI | Coverage | Selective accuracy | Selective risk | Corrected | Rejected | Pipeline median | Pipeline p95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `qwen2.5:7b` | 73.3% | 55.6%-85.8% | 100.0% | 100.0% | 0.0% | 8 | 0 | 3862.9 ms | 6097.3 ms |
| `llama3.2:latest` | 56.7% | 39.2%-72.6% | 96.7% | 100.0% | 0.0% | 12 | 1 | 2394.8 ms | 3455.4 ms |

## Reproduction

The manifest contains program versions, model inventory, command, seed and SHA-256 hashes.
Raw requests, Ollama envelopes, generated JSON, Prolog outputs and traces are retained per case.
