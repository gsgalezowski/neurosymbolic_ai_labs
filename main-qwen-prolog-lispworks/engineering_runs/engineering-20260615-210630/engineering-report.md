# Engineering study results

Run directory: `engineering_runs/engineering-20260615-210630`

## Model comparison

| Model | Accuracy | 95% CI | Coverage | Selective accuracy | Selective risk | Corrected | Rejected | Pipeline median | Pipeline p95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `qwen2.5:7b` | 73.3% | 55.6%-85.8% | 100.0% | 100.0% | 0.0% | 8 | 0 | 3855.9 ms | 6003.5 ms |
| `llama3.2:latest` | 60.0% | 42.3%-75.4% | 96.7% | 100.0% | 0.0% | 11 | 1 | 2424.6 ms | 3429.0 ms |

## Reproduction

The manifest contains program versions, model inventory, command, seed and SHA-256 hashes.
Raw requests, Ollama envelopes, generated JSON, Prolog outputs and traces are retained per case.
