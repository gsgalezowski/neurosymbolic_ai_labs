"""Create a publication chart from a completed engineering benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    metrics = json.loads((args.run_dir / "metrics.json").read_text(encoding="utf-8"))
    models = list(metrics)
    labels = [model.replace(":latest", "") for model in models]
    accuracy = [100 * metrics[model]["model_accuracy"] for model in models]
    coverage = [100 * metrics[model]["coverage"] for model in models]
    selective = [100 * metrics[model]["selective_accuracy"] for model in models]
    pipeline = [
        metrics[model]["latency_ms"]["pipeline"]["median"] / 1000 for model in models
    ]
    prolog = [
        metrics[model]["latency_ms"]["prolog_process"]["median"] for model in models
    ]

    figure, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    x = range(len(models))
    width = 0.24
    axes[0].bar([i - width for i in x], accuracy, width, label="Model accuracy")
    axes[0].bar(x, coverage, width, label="Coverage")
    axes[0].bar(
        [i + width for i in x], selective, width, label="Selective accuracy"
    )
    axes[0].set_ylim(0, 105)
    axes[0].set_ylabel("Percent")
    axes[0].set_xticks(list(x), labels)
    axes[0].set_title("Quality before and after the symbolic gate")
    axes[0].grid(axis="y", alpha=0.25)
    axes[0].legend(loc="lower left")

    axes[1].bar(labels, pipeline, color="#4C78A8")
    axes[1].set_ylabel("Median pipeline latency [s]")
    axes[1].set_title("End-to-end latency")
    axes[1].grid(axis="y", alpha=0.25)
    for index, value in enumerate(pipeline):
        axes[1].text(index, value + 0.05, f"{value:.2f}s", ha="center")
        axes[1].text(
            index,
            max(0.05, value * 0.48),
            f"Prolog {prolog[index]:.1f} ms",
            ha="center",
            color="white",
            fontweight="bold",
        )

    figure.tight_layout()
    output = args.output or args.run_dir / "engineering-results.png"
    figure.savefig(output, dpi=200)
    plt.close(figure)
    print(output)


if __name__ == "__main__":
    main()
