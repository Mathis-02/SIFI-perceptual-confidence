from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_response2_rates(response2_summary: pd.DataFrame, outpath: Path) -> None:
    """
    Publication-style descriptive plot for response '2 flashes' rates.

    Expected input:
    one row per participant x base_condition x soa_type, with a response2 rate column.

    The plot is descriptive: it shows individual participant rates and group mean ± SEM.
    """

    data = response2_summary.copy()

    # ------------------------------------------------------------
    # Detect rate column automatically
    # ------------------------------------------------------------
    candidate_cols = [
        "response2_rate",
        "prop_response2",
        "mean_response2",
        "rate",
        "response2",
    ]

    rate_col = None
    for col in candidate_cols:
        if col in data.columns:
            rate_col = col
            break

    if rate_col is None:
        raise ValueError(
            "No response-rate column found. Expected one of: "
            f"{candidate_cols}. Available columns are: {list(data.columns)}"
        )

    # ------------------------------------------------------------
    # Convert to percentage if values are proportions
    # ------------------------------------------------------------
    if data[rate_col].max() <= 1.01:
        data["plot_rate"] = data[rate_col] * 100
    else:
        data["plot_rate"] = data[rate_col]

    # ------------------------------------------------------------
    # Condition order
    # ------------------------------------------------------------
    order = [
        ("A1V1", "none"),
        ("A1V1_A2", "short"),
        ("A1V1_A2", "standard"),
        ("A1V1_A2V2", "short"),
        ("A1V1_A2V2", "standard"),
        ("A1V1_V2", "short"),
        ("A1V1_V2", "standard"),
    ]

    labels = {
         ("A1V1", "none"): "A1V1",
        ("A1V1_A2", "short"): "A1V1_A2\ncourt",
        ("A1V1_A2", "standard"): "A1V1_A2\nstandard",
        ("A1V1_A2V2", "short"): "A1V1_A2V2\ncourt",
        ("A1V1_A2V2", "standard"): "A1V1_A2V2\nstandard",
        ("A1V1_V2", "short"): "A1V1_V2\ncourt",
        ("A1V1_V2", "standard"): "A1V1_V2\nstandard",
    }

    # Wider spacing avoids overlapping tick labels.
    xpos = {
        ("A1V1", "none"): 0.0,
        ("A1V1_A2", "short"): 1.6,
        ("A1V1_A2", "standard"): 2.6,
        ("A1V1_A2V2", "short"): 4.4,
        ("A1V1_A2V2", "standard"): 5.8,
        ("A1V1_V2", "short"): 7.8,
        ("A1V1_V2", "standard"): 8.8,
    }

    colors = {
        ("A1V1", "none"): "#7f7f7f",
        ("A1V1_A2", "short"): "#E69F00",
        ("A1V1_A2", "standard"): "#E69F00",
        ("A1V1_A2V2", "short"): "#1B9E77",
        ("A1V1_A2V2", "standard"): "#1B9E77",
        ("A1V1_V2", "short"): "#8E44AD",
        ("A1V1_V2", "standard"): "#8E44AD",
    }

    # ------------------------------------------------------------
    # Figure
    # ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11.0, 5.7))

    # Vertical separators between conceptual blocks.
    for vline_x in [0.8, 3.5, 6.8]:
        ax.axvline(vline_x, color="#d0d0d0", lw=1.1, zorder=0)

    # ------------------------------------------------------------
    # Plot individual points and mean ± SEM
    # ------------------------------------------------------------
    n_map = {}

    for cond in order:
        cond_name, soa = cond

        subset = data[
            (data["base_condition"] == cond_name)
            & (data["soa_type"] == soa)
        ].copy()

        if subset.empty:
            continue

        y = subset["plot_rate"].dropna().to_numpy()
        x = xpos[cond]
        color = colors[cond]

        n_map[cond] = len(y)

        # Deterministic jitter: stable across runs.
        if len(y) > 1:
            jitter = np.linspace(-0.10, 0.10, len(y))
        else:
            jitter = np.array([0.0])

        ax.scatter(
            np.full(len(y), x) + jitter,
            y,
            s=44,
            color=color,
            alpha=0.75,
            edgecolor="none",
            zorder=3,
        )

        mean_y = np.mean(y)
        sem_y = np.std(y, ddof=1) / np.sqrt(len(y)) if len(y) > 1 else 0.0

        ax.errorbar(
            x,
            mean_y,
            yerr=sem_y,
            fmt="o",
            color="black",
            markersize=6.5,
            capsize=4.5,
            elinewidth=1.9,
            capthick=1.9,
            zorder=4,
        )

    

    # ------------------------------------------------------------
    # Axes and labels
    # ------------------------------------------------------------
    ax.set_xlim(-0.6, 9.4)
    ax.set_ylim(-3, 104)

    ax.set_ylabel('Taux de réponses « 2 flashs » (%)', fontsize=13)
    ax.set_xlabel("Condition / SOA", fontsize=13)

    xticks = [xpos[c] for c in order]
    xticklabels = [labels[c] for c in order]

    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, fontsize=10)

    

    # ------------------------------------------------------------
    # Style
    # ------------------------------------------------------------
    ax.grid(axis="y", color="#e6e6e6", linewidth=0.8)
    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.2)
    ax.spines["bottom"].set_linewidth(1.2)

    ax.tick_params(axis="both", width=1.2, length=5, labelsize=11)

    fig.tight_layout()
    _save(fig, outpath)


def plot_illusion_rates(df: pd.DataFrame, out_path: Path) -> None:
    """
    Publication-style plot of illusion rates by illusion type and SOA.

    Expected input columns:
    - participant
    - illusion_type: "fission" or "fusion"
    - soa_type: "standard" or "short"
    - illusion_rate
    """

    import numpy as np
    import matplotlib.pyplot as plt

    required = {"participant", "illusion_type", "soa_type", "illusion_rate"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for plot_illusion_rates: {missing}")

    plot_df = df.copy()
    plot_df["participant"] = plot_df["participant"].astype(str)
    plot_df["illusion_type"] = plot_df["illusion_type"].astype(str)
    plot_df["soa_type"] = plot_df["soa_type"].astype(str)
    plot_df["illusion_rate"] = pd.to_numeric(plot_df["illusion_rate"], errors="coerce")

    plot_df = plot_df.dropna(subset=["participant", "illusion_type", "soa_type", "illusion_rate"])

    # Keep only expected cells.
    plot_df = plot_df[
        plot_df["illusion_type"].isin(["fission", "fusion"])
        & plot_df["soa_type"].isin(["standard", "short"])
    ].copy()

    if plot_df.empty:
        raise ValueError("No data available for illusion-rate plot after filtering.")

    # Order: standard then short, because it shows the effect of shortening SOA.
    soa_order = ["standard", "short"]
    illusion_order = ["fission", "fusion"]

    colors = {
        "fission": "#D89000",
        "fusion": "#7B3294",
    }

    # Group summary at participant level.
    group_summary = (
        plot_df
        .groupby(["illusion_type", "soa_type"], as_index=False)
        .agg(
            mean=("illusion_rate", "mean"),
            sd=("illusion_rate", "std"),
            n_participants=("participant", "nunique"),
        )
    )
    group_summary["sem"] = group_summary["sd"] / np.sqrt(group_summary["n_participants"])

    # Style.
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.labelsize": 10,
        "axes.titlesize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
    })

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(5.6, 3.4),
        sharey=True,
        gridspec_kw={"wspace": 0.18},
    )

    for ax, illusion_type in zip(axes, illusion_order):
        sub = plot_df[plot_df["illusion_type"] == illusion_type].copy()
        color = colors[illusion_type]

        x_positions = {"standard": 0, "short": 1}

        # Lines per participant.
        for participant, pdat in sub.groupby("participant"):
            pdat = pdat.set_index("soa_type")

            if all(soa in pdat.index for soa in soa_order):
                y = [pdat.loc[soa, "illusion_rate"] for soa in soa_order]
                x = [x_positions[soa] for soa in soa_order]

                ax.plot(
                    x,
                    y,
                    color="0.80",
                    linewidth=0.65,
                    alpha=0.45,
                    zorder=1,
                )
        # Individual points.
        rng = np.random.default_rng(123)
        for soa in soa_order:
            sdat = sub[sub["soa_type"] == soa]
            x = x_positions[soa]
            jitter = rng.normal(0, 0.035, size=len(sdat))

            ax.scatter(
                np.full(len(sdat), x) + jitter,
                sdat["illusion_rate"],
                s=24,
                color=color,
                alpha=0.50,
                edgecolor="none",
                zorder=2,
            )

        # Mean ± SEM.
        for soa in soa_order:
            row = group_summary[
                (group_summary["illusion_type"] == illusion_type)
                & (group_summary["soa_type"] == soa)
            ]

            if row.empty:
                continue

            row = row.iloc[0]
            x = x_positions[soa]

            ax.errorbar(
                x,
                row["mean"],
                yerr=row["sem"],
                fmt="o",
                markersize=5.0,
                color="black",
                ecolor="black",
                elinewidth=1.15,
                capsize=3,
                capthick=1.15,
                zorder=4,
            )

        # Optional: put N once inside each panel, not under each condition.
        n_participants = sub["participant"].nunique()
        ax.text(
            0.02,
            0.94,
            f"N={n_participants}",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=8,
            color="0.35",
        )

        ax.set_title(illusion_type.capitalize())
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["standard", "short"])
        ax.set_xlim(-0.35, 1.35)
        ax.set_ylim(-0.02, 1.05)

        ax.grid(axis="y", color="0.92", linewidth=0.7)
        ax.grid(axis="x", visible=False)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.tick_params(axis="x", length=0)
        ax.tick_params(axis="y", direction="out", length=3)

    axes[0].set_ylabel("Illusion rate")
    fig.supxlabel("SOA", y=0.02, fontsize=10)

    fig.tight_layout(rect=(0, 0.04, 1, 1))

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(out_path, bbox_inches="tight")

    # Also save SVG version for vector editing.
    svg_path = out_path.with_suffix(".svg")
    fig.savefig(svg_path, bbox_inches="tight")

    plt.close(fig)
