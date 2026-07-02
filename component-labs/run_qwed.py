"""Kontrolowane sprawdzenie parsera symbolicznego QWED."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "qwed-verification-main" / "src"))

from qwed_new.core.safe_parser import safe_parse_expr


cases = [
    ("2*(5+10)", "poprawne wyrazenie"),
    ("(x+1)**2", "wyrazenie symboliczne"),
    ("__import__('os').system('whoami')", "proba wykonania kodu"),
    ("open('sekret.txt').read()", "proba odczytu pliku"),
]

print("QWED: deterministyczna granica zaufania")
for expression, label in cases:
    try:
        parsed = safe_parse_expr(expression)
        print(f"ACCEPT | {label:25} | {expression} -> {parsed}")
    except Exception as exc:
        reason = "niedozwolona konstrukcja: __import__" if "__import__" in str(exc) else "niedozwolona konstrukcja: open"
        print(f"BLOCK  | {label:25} | {expression} -> {reason}")
