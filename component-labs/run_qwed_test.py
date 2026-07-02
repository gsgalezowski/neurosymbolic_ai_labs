"""Uruchamia pakiet testów bezpiecznego parsera QWED."""
from pathlib import Path
import os
import subprocess
import sys

repo = Path(__file__).resolve().parents[1] / "qwed-verification-main"
env = os.environ.copy()
env["PYTHONPATH"] = str(repo / "src")
command = [sys.executable, "-m", "pytest", "tests/security/test_safe_parser.py", "-q"]
print("TEST KONTROLNY QWED SAFE PARSER")
print("Polecenie:", " ".join(command[1:]))
result = subprocess.run(command, cwd=repo, env=env, text=True)
raise SystemExit(result.returncode)
