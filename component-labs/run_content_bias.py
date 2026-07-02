"""Audyt czterech kontrolowanych ćwiartek zbioru content-effects."""
from pathlib import Path
import json
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "steering_content_effects-main" / "dataset"
files = sorted(DATA.glob("syllogistic_reasoning_binary_*.json"))
print("CONTENT EFFECTS: wiarygodnosc tresci kontra poprawnosc logiczna")
print("plik                              rekordy  plausible  valid  schematy")
for path in files:
    rows = json.loads(path.read_text(encoding="utf-8"))
    schemas = Counter(r["schema"] for r in rows)
    plausible = sum(bool(r["plausibility"]) for r in rows)
    valid = sum(bool(r["validity"]) for r in rows)
    print(f"{path.stem.replace('syllogistic_reasoning_binary_',''):34} {len(rows):6d} {plausible:10d} {valid:6d} {len(schemas):8d}")

example = json.loads(files[0].read_text(encoding="utf-8"))[0]
print("\nPrzyklad konfliktu: tresc brzmi wiarygodnie, ale wniosek jest niewazny")
print("P1:", example["premise1"])
print("P2:", example["premise2"])
print("W :", example["conclusion"])
print("plausibility=", example["plausibility"], "validity=", example["validity"])
print("Lacznie rekordow:", sum(len(json.loads(p.read_text(encoding='utf-8'))) for p in files))
