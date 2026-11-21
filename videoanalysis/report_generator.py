# report_generator.py

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import os


def generate_graph(result):

    eye       = result["eye_scores"]
    attention = result["attention_scores"]
    movement  = result["movement_scores"]

    # Guard: nothing to plot
    if not eye and not attention and not movement:
        return None

    frames = list(range(len(eye)))

    # ── Style ────────────────────────────────────────────────────────────
    plt.rcParams.update({
        "font.family":       "DejaVu Sans",
        "font.size":         10,
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "axes.grid":         True,
        "grid.color":        "#e2e8f0",
        "grid.linewidth":    0.8,
        "grid.linestyle":    "--",
        "axes.facecolor":    "#ffffff",
        "figure.facecolor":  "#f8f9fb",
    })

    fig, ax = plt.subplots(figsize=(8, 3.6))

    # Show a marker every ~20 data points so lines stay readable
    step = max(1, len(frames) // 20)

    ax.plot(frames, eye,
            color="#1d6fa4", linewidth=2,
            label="Face Direction",
            markevery=step, marker="o", markersize=4,
            markerfacecolor="white", markeredgewidth=1.5)

    ax.plot(frames, attention,
            color="#0ea5e9", linewidth=2,
            label="ADOS Attention",
            markevery=step, marker="s", markersize=4,
            markerfacecolor="white", markeredgewidth=1.5)

    ax.plot(frames, movement,
            color="#64b5a0", linewidth=2,
            label="Repetitive Movement",   # ✅ updated label
            markevery=step, marker="^", markersize=4,
            markerfacecolor="white", markeredgewidth=1.5)

    # ── Risk zone shading ────────────────────────────────────────────────
    ax.axhspan(0,  40,  alpha=0.06, color="#ef4444", zorder=0)  # High risk
    ax.axhspan(40, 70,  alpha=0.06, color="#f59e0b", zorder=0)  # Moderate
    ax.axhspan(70, 100, alpha=0.06, color="#22c55e", zorder=0)  # Low risk

    # Zone labels on the right edge
    right = len(frames) * 1.005
    ax.text(right, 20,  "High",     fontsize=8, color="#ef4444", va="center", clip_on=False)
    ax.text(right, 55,  "Moderate", fontsize=8, color="#f59e0b", va="center", clip_on=False)
    ax.text(right, 85,  "Low",      fontsize=8, color="#22c55e", va="center", clip_on=False)

    ax.set_xlim(0, max(len(frames) - 1, 1))
    ax.set_ylim(0, 100)
    ax.set_xlabel("Frame (sampled every 5 frames)", fontsize=9, color="#4a5568")
    ax.set_ylabel("Score (0–100)",                  fontsize=9, color="#4a5568")
    ax.set_title("Frame-by-Frame Behavioral Scores",
                 fontsize=11, fontweight="bold", color="#0f1923", pad=12)

    ax.legend(loc="lower right", fontsize=9,
              framealpha=0.9, edgecolor="#e2e8f0",
              fancybox=False, borderpad=0.6)

    ax.tick_params(colors="#94a3b8", labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#e2e8f0")

    plt.tight_layout(pad=1.4)

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)
    path = os.path.join(static_dir, "graph.png")
    plt.savefig(path, dpi=140, bbox_inches="tight")
    plt.close()

    return "graph.png"