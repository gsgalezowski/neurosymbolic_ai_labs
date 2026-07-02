"""Uruchamia oryginalne reguły rules_v20.lp na kontrolowanych metadanych sieci."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "NeuroSymbolic-Pneumonia-Detection-main" / "code"
sys.path.insert(0, str(CODE))

import clingo

rules_path = CODE / "logic_rules" / "rules_v20.lp"
samples = [
    ("A_wysoki_wynik", 82, 120, 150, 80, 90, 60, 30),
    ("B_przy_krawedzi", 91, 2, 150, 80, 90, 60, 30),
    ("C_dolna_strefa", 35, 100, 260, 80, 90, 55, 25),
    ("D_czysta_czern", 88, 100, 260, 80, 90, 10, 25),
    ("E_za_niski_wynik", 20, 100, 260, 80, 90, 55, 25),
]
facts = [
    f"pred({i},{score},{x},{y},{w},{h},{intensity},{texture})."
    for i, (_, score, x, y, w, h, intensity, texture) in enumerate(samples)
]

ctl = clingo.Control()
ctl.load(str(rules_path))
ctl.add("base", [], "\n".join(facts))
ctl.ground([("base", [])])
valid = set()
ctl.solve(on_model=lambda m: valid.update(int(str(s.arguments[0])) for s in m.symbols(shown=True) if s.name == "valid"))

print("PNEUMONIA: statystyczna propozycja -> filtr ASP")
print("Reguly autorow: NeuroSymbolic-Pneumonia-Detection-main/code/logic_rules/rules_v20.lp")
for i, sample in enumerate(samples):
    decision = "VALID" if i in valid else "REJECT"
    print(f"{decision:6} | {sample[0]:20} | score={sample[1]:2d}% box=({sample[2]},{sample[3]},{sample[4]},{sample[5]}) intensity={sample[6]}")
print(f"Zatwierdzone: {len(valid)}/{len(samples)}; indeksy: {sorted(valid)}")
