"""Mały, deterministyczny przebieg PyAerial na danych pogodowych."""
from pathlib import Path
import json
import sys

import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pyaerial-main"))

from aerial.model import train
from aerial.rule_extraction import generate_rules


data = pd.DataFrame(
    {
        "pogoda": ["slonce", "slonce", "deszcz", "deszcz", "chmury"] * 8,
        "temperatura": ["cieplo", "cieplo", "zimno", "zimno", "lagodnie"] * 8,
        "spacer": ["tak", "tak", "nie", "nie", "tak"] * 8,
    }
)

print("PYAERIAL: siec neuronowa -> reguly symboliczne")
print(f"Rekordy: {len(data)}; kolumny: {', '.join(data.columns)}")
torch.manual_seed(42)
model = train(data, epochs=5, show_progress=False)
result = generate_rules(
    model,
    target_classes=["spacer"],
    min_rule_frequency=0.10,
    min_rule_strength=0.30,
)
rules = sorted(result["rules"], key=lambda x: x.get("confidence", 0), reverse=True)
print(f"Wydobyte reguly klasyfikacyjne: {len(rules)}")
for number, rule in enumerate(rules[:8], 1):
    left = " AND ".join(f"{x['feature']}={x['value']}" for x in rule["antecedents"])
    right = rule["consequent"]
    print(
        f"{number}. {left} -> {right['feature']}={right['value']} "
        f"(support={rule['support']:.3f}, confidence={rule['confidence']:.3f})"
    )

out = Path(__file__).with_name("pyaerial_result.json")
out.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print("Pelny wynik JSON: laboratoria_replikacja/pyaerial_result.json")
