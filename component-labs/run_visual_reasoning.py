"""Wykonuje programy symboliczne na scenie w formacie projektu Sort-of-CLEVR."""
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "neuro-symbolic-ai-soc-master"))
from program_executor import ProgramExecutor

scene = pd.DataFrame([
    {"shape": "circle", "color": "red", "position": (40, 40)},
    {"shape": "rectangle", "color": "blue", "position": (180, 50)},
    {"shape": "circle", "color": "green", "position": (60, 180)},
    {"shape": "rectangle", "color": "yellow", "position": (175, 175)},
])
tests = [
    ("Ile jest okregow?", ["filter circle", "count"], 2),
    ("Jaki ksztalt ma niebieski obiekt?", ["filter blue", "query shape"], "rectangle"),
    ("Czy czerwony obiekt jest po lewej?", ["filter red", "query position", "isleft"], "yes"),
    ("Jaki ksztalt jest najblizej czerwonego?", ["filter red", "relate closest", "query shape"], "rectangle"),
]
executor = ProgramExecutor()
print("SORT-OF-CLEVR: scena symboliczna -> program -> odpowiedz")
print(scene.to_string(index=True))
for question, program, expected in tests:
    result = executor(scene, program)
    status = "PASS" if result == expected else "FAIL"
    print(f"{status} | {question}")
    print(f"       program: {' -> '.join(program)} | wynik={result!r} | oczekiwano={expected!r}")
