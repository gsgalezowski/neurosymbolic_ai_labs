"""Uruchamia testy predykatów logicznych TorchLogic."""
from pathlib import Path
import subprocess, sys
repo = Path(__file__).resolve().parents[1] / "torchlogic-main"
cmd = [sys.executable, "-m", "pytest", "tests/nn/test_base_predicates.py", "-q"]
print("TORCHLOGIC: test predykatow Neural Reasoning Network", flush=True)
print("Polecenie:", " ".join(cmd[1:]), flush=True)
result = subprocess.run(cmd, cwd=repo, text=True)
raise SystemExit(result.returncode)
