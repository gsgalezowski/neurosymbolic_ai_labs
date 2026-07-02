"""Lokalna adaptacja notebooka LTN Binary Classification z repozytorium."""
from pathlib import Path
import random
import numpy as np
import pandas as pd
import torch
import ltn
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
random.seed(42); np.random.seed(42); torch.manual_seed(42)
df = pd.read_csv(ROOT / "Neuro-Symbolic-AI-main" / "wine_dataset.csv")
df = df.drop(columns=["quality"])
y = (df["style"] == "red").astype(np.float32).to_numpy()
X = df.drop(columns=["style"]).astype(np.float32).to_numpy()
X = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-8)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
Xtr, Xte = torch.tensor(Xtr, device=device), torch.tensor(Xte, device=device)
ytr_t = torch.tensor(ytr, dtype=torch.bool, device=device)

class Model(torch.nn.Module):
    def __init__(self):
        super().__init__(); self.net = torch.nn.Sequential(torch.nn.Linear(11,32),torch.nn.ReLU(),torch.nn.Linear(32,1),torch.nn.Sigmoid())
    def forward(self,x): return self.net(x)

A = ltn.Predicate(Model().to(device))
Not = ltn.Connective(ltn.fuzzy_ops.NotStandard())
Forall = ltn.Quantifier(ltn.fuzzy_ops.AggregPMeanError(p=2), quantifier="f")
SatAgg = ltn.fuzzy_ops.SatAgg()
opt = torch.optim.Adam(A.parameters(), lr=0.01)

print("LTN WINE: predykat neuronowy uczony przez formule logiczna")
print(f"Rekordy={len(df)}, train={len(Xtr)}, test={len(Xte)}, cechy={X.shape[1]}")
for epoch in range(31):
    opt.zero_grad()
    pos = ltn.Variable("positive", Xtr[ytr_t])
    neg = ltn.Variable("negative", Xtr[~ytr_t])
    sat = SatAgg(Forall(pos, A(pos)), Forall(neg, Not(A(neg))))
    loss = 1.0 - sat
    loss.backward(); opt.step()
    if epoch in (0, 5, 10, 20, 30):
        with torch.no_grad():
            pred = (A.model(Xte).squeeze().cpu().numpy() >= 0.5).astype(int)
        print(f"epoch={epoch:2d} sat={sat.item():.4f} loss={loss.item():.4f} test_accuracy={accuracy_score(yte,pred):.4f}")
print("Formula: forall(x_red, A(x_red)) AND forall(x_white, NOT A(x_white))")
print("Urzadzenie:", device)
