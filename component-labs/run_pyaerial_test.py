"""Uruchamia wskazany przez autorów test integracyjny PyAerial."""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[1] / "pyaerial-main"
command = [sys.executable, "-m", "pytest", "tests/test_robustness.py::TestEndToEndPipeline::test_categorical_data_pipeline", "-q"]
print("TEST KONTROLNY PYAERIAL")
print("Polecenie:", " ".join(command[1:]))
result = subprocess.run(command, cwd=repo, text=True)
raise SystemExit(result.returncode)
