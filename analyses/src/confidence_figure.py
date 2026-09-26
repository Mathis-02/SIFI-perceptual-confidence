from __future__ import annotations

from pathlib import Path

import pandas as pd


def plot_confidence_composite_abcd(
    trials_df: pd.DataFrame,
    matched_summary: pd.DataFrame,
    outpath: Path,
) -> None:
    """
    Create the four-panel confidence figure used in the thesis.

    A. Confidence in conditions with one physically presented flash.
    B. Confidence in conditions with two physically presented flashes.
    C. Matched confidence for trials reported as two flashes.
    D. Matched confidence for trials reported as one flash.

    Required columns in trials_df:
    - participant
    - base_condition
    - soa_type
    - response2
    - confidence

    Required columns in matched_summary:
    - participant
    - matched_percept
    - percept_origin
    - soa_type
    - mean_confidence
    """

    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from pathlib import Path

    # ------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------

    required_trials = {
        "participant",
        "base_condition",
        "soa_type",
        "response2",
        "confidence",
    }

    required_matched = {
        "participant",
        "matched_percept",
        "percept_origin",
        "soa_type",
        "mean_confidence",
    }

    missing_trials = required_trials - set(trials_df.columns)
    missing_matched = required_matched - set(matched_summary.columns)

    if missing_trials:
        raise ValueError(
            f"Missing required columns in trials_df: {missing_trials}. "
            f"Available columns are: {list(trials_df.columns)}"
        )

    if missing_matched:
        raise ValueError(
            f"Missing required columns in matched_summary: {missing_matched}. "
            f"Available columns are: {list(matched_summary.columns)}"
        )

    # ------------------------------------------------------------
    # Prepare trial-level summaries for panels A and B
    # ------------------------------------------------------------

    trials = trials_df.copy()

    trials["participant"] = trials["participant"].astype(str)
    trials["base_condition"] = trials["base_condition"].astype(str)
    trials["soa_type"] = trials["soa_type"].astype(str).str.lower()
    trials["response2"] = pd.to_numeric(trials["response2"], errors="coerce")
    trials["confidence"] = pd.to_numeric(trials["confidence"], errors="coerce")

    trials = trials.dropna(
        subset=[
            "participant",
            "base_condition",
            "soa_type",
            "response2",
            "confidence",
        ]
    )

    if trials["confidence"].max() <= 1.01:
        trials["plot_confidence"] = trials["confidence"] * 100
    else:
        trials["plot_confidence"] = trials["confidence"]

    global_summary = (
        trials
        .groupby(
            ["participant", "base_condition", "soa_type", "response2"],
            as_index=False,
        )
        .agg(mean_confidence=("plot_confidence", "mean"))
    )

    # ------------------------------------------------------------
    # Prepare matched-percept summaries for panels C and D
    # ------------------------------------------------------------

    matched = matched_summary.copy()

    matched["participant"] = matched["participant"].astype(str)
    matched["matched_percept"] = matched["matched_percept"].astype(str).str.lower()
    matched["percept_origin"] = matched["percept_origin"].astype(str).str.lower()
    matched["soa_type"] = matched["soa_type"].astype(str).str.lower()
    matched["mean_confidence"] = pd.to_numeric(
        matched["mean_confidence"],
        errors="coerce",
    )

    matched = matched.dropna(
        subset=[
            "participant",
            "matched_percept",
            "percept_origin",
            "soa_type",
            "mean_confidence",
        ]
    )

    if matched["mean_confidence"].max() <= 1.01:
        matched["plot_confidence"] = matched["mean_confidence"] * 100
    else:
        matched["plot_confidence"] = matched["mean_confidence"]

    # ------------------------------------------------------------
    # Plot style
    # ------------------------------------------------------------

    colors = {
        "A1V1": "#7f7f7f",
        "A1V1_A2": "#D89000",
        "A1V1_A2V2": "#009E73",
        "A1V1_V2": "#7B3294",
        "mean": "#222222",
        "line": "#D6D6D6",
    }

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8.0,
        "axes.labelsize": 8.5,
        "axes.titlesize": 9.5,
        "xtick.labelsize": 7.0,
        "ytick.labelsize": 8.0,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
    })

    fig = plt.figure(figsize=(9.2, 7.1))

    gs = fig.add_gridspec(
        2,
        2,
        height_ratios=[0.86, 1.05],
        width_ratios=[1.0, 1.0],
        hspace=0.44,
        wspace=0.22,
    )

    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1], sharey=ax_a)
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1], sharey=ax_c)

    rng = np.random.default_rng(123)

    # ------------------------------------------------------------
    # Helper for global panels A and B
    # ------------------------------------------------------------

    def draw_global_panel(
        ax,
        conditions,
        title,
        panel_letter,
        show_ylabel=True,
    ):
        block_spacing = 1.55
        within_spacing = 0.42

        xticks = []
        xticklabels = []
        group_centers = []
        group_labels = []
        group_base_conditions = []

        response_labels = {
            0: "1f",
            1: "2f",
        }

        for i, (base_condition, soa_type, condition_label) in enumerate(conditions):
            center = i * block_spacing
            x_response1 = center - within_spacing / 2
            x_response2 = center + within_spacing / 2

            group_centers.append(center)
            group_labels.append(condition_label)
            group_base_conditions.append(base_condition)

            # Connect each participant across one- and two-flash reports
            # within the same experimental condition.
            cell_condition = global_summary[
                (global_summary["base_condition"] == base_condition)
                & (global_summary["soa_type"] == soa_type)
                & (global_summary["response2"].isin([0, 1]))
            ].copy()

            wide_condition = cell_condition.pivot_table(
                index="participant",
                columns="response2",
                values="mean_confidence",
                aggfunc="mean",
            )

            if {0, 1}.issubset(wide_condition.columns):
                wide_condition = wide_condition.dropna(subset=[0, 1])

                for _, row in wide_condition.iterrows():
                    ax.plot(
                        [x_response1, x_response2],
                        [row[0], row[1]],
                        color=colors["line"],
                        linewidth=0.50,
                        alpha=0.35,
                        zorder=1,
                    )
            for response_value, x in [(0, x_response1), (1, x_response2)]:
                cell = global_summary[
                    (global_summary["base_condition"] == base_condition)
                    & (global_summary["soa_type"] == soa_type)
                    & (global_summary["response2"] == response_value)
                ].copy()

                if cell.empty:
                    continue

                color = colors.get(base_condition, "#7f7f7f")
                y = cell["mean_confidence"].to_numpy()
                jitter = rng.normal(0, 0.030, size=len(cell))

                ax.scatter(
                    np.full(len(cell), x) + jitter,
                    y,
                    s=20,
                    color=color,
                    alpha=0.58,
                    edgecolor="none",
                    zorder=2,
                )

                mean = np.mean(y)
                sem = np.std(y, ddof=1) / np.sqrt(len(y)) if len(y) > 1 else 0.0

                ax.errorbar(
                    x,
                    mean,
                    yerr=sem,
                    fmt="o",
                    color=colors["mean"],
                    ecolor=colors["mean"],
                    markersize=4.4,
                    elinewidth=1.05,
                    capsize=2.8,
                    capthick=1.05,
                    zorder=4,
                )

            xticks.extend([x_response1, x_response2])
            xticklabels.extend([response_labels[0], response_labels[1]])

            if i > 0:
                sep_x = center - block_spacing / 2
                ax.axvline(sep_x, color="0.84", linewidth=0.75, zorder=0)

        ymin, ymax = 42, 103
        ax.set_ylim(ymin, ymax)
        ax.set_yticks([50, 60, 70, 80, 90, 100])

        left_lim = -0.75
        right_lim = (len(conditions) - 1) * block_spacing + 0.75
        ax.set_xlim(left_lim, right_lim)

        ax.set_title(title, pad=6)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels)

        condition_label_y = ymin + 1.2
        for center, label, base_cond in zip(
            group_centers,
            group_labels,
            group_base_conditions,
        ):
            ax.text(
                center,
                condition_label_y,
                label,
                ha="center",
                va="bottom",
                fontsize=6.8,
                color=colors.get(base_cond, "0.25"),
            )

        if show_ylabel:
            ax.set_ylabel("Confiance moyenne (%)")
        else:
            plt.setp(ax.get_yticklabels(), visible=False)

        ax.set_xlabel("Percept rapporté", labelpad=8)

        ax.grid(axis="y", color="0.92", linewidth=0.65)
        ax.grid(axis="x", visible=False)
        ax.set_axisbelow(True)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.tick_params(axis="x", length=0, pad=3)
        ax.tick_params(axis="y", direction="out", length=3)

        ax.text(
            -0.12,
            1.04,
            panel_letter,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    # ------------------------------------------------------------
    # Helper for panel C: reported percept = two flashes
    # ------------------------------------------------------------

    def draw_matched_two_panel(ax):
        fission = matched[
            (matched["matched_percept"] == "two")
            & (matched["percept_origin"].isin(["congruent", "illusory"]))
            & (matched["soa_type"].isin(["standard", "short"]))
        ].copy()

        cells = [
            ("standard", "congruent", 0.00, "A1V1_A2V2\nstandard", "A1V1_A2V2"),
            ("standard", "illusory", 0.45, "A1V1_A2\nstandard", "A1V1_A2"),
            ("short", "congruent", 1.35, "A1V1_A2V2\ncourt", "A1V1_A2V2"),
            ("short", "illusory", 1.80, "A1V1_A2\ncourt", "A1V1_A2"),
        ]

        x_map = {
            (soa, origin): x
            for soa, origin, x, _, _ in cells
        }

        for soa in ["standard", "short"]:
            sub_soa = fission[fission["soa_type"] == soa].copy()

            wide = sub_soa.pivot_table(
                index="participant",
                columns="percept_origin",
                values="plot_confidence",
                aggfunc="mean",
            )

            if {"congruent", "illusory"}.issubset(wide.columns):
                wide = wide.dropna(subset=["congruent", "illusory"])

                for _, row in wide.iterrows():
                    ax.plot(
                        [
                            x_map[(soa, "congruent")],
                            x_map[(soa, "illusory")],
                        ],
                        [
                            row["congruent"],
                            row["illusory"],
                        ],
                        color=colors["line"],
                        linewidth=0.55,
                        alpha=0.45,
                        zorder=1,
                    )

        for soa, origin, x, _, base_condition in cells:
            cell = fission[
                (fission["soa_type"] == soa)
                & (fission["percept_origin"] == origin)
            ].copy()

            if cell.empty:
                continue

            y = cell["plot_confidence"].to_numpy()
            jitter = rng.normal(0, 0.022, size=len(cell))
            color = colors[base_condition]

            ax.scatter(
                np.full(len(cell), x) + jitter,
                y,
                s=20,
                color=color,
                alpha=0.58,
                edgecolor="none",
                zorder=2,
            )

            mean = np.mean(y)
            sem = np.std(y, ddof=1) / np.sqrt(len(y)) if len(y) > 1 else 0.0

            ax.errorbar(
                x,
                mean,
                yerr=sem,
                fmt="o",
                color=colors["mean"],
                ecolor=colors["mean"],
                markersize=4.5,
                elinewidth=1.05,
                capsize=2.8,
                capthick=1.05,
                zorder=4,
            )

        ax.axvline(0.90, color="0.84", linewidth=0.75, zorder=0)

        ax.set_title('Percept rapporté « 2 flashs »', pad=6)
        ax.set_xticks([x for _, _, x, _, _ in cells])
        ax.set_xticklabels([label for _, _, _, label, _ in cells])
        ax.set_ylabel("Confiance moyenne (%)")
        ax.set_xlabel("Condition / SOA", labelpad=7)

        ax.text(
            -0.12,
            1.04,
            "C",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    # ------------------------------------------------------------
    # Helper for panel D: reported percept = one flash
    # ------------------------------------------------------------

    def draw_matched_one_panel(ax):
        fusion = matched[
            (matched["matched_percept"] == "one")
            & (matched["percept_origin"].isin(["congruent", "illusory"]))
        ].copy()

        cells = [
            ("none", "congruent", 0.00, "A1V1", "A1V1"),
            ("standard", "illusory", 1.05, "A1V1_V2\nstandard", "A1V1_V2"),
            ("short", "illusory", 1.70, "A1V1_V2\ncourt", "A1V1_V2"),
        ]

        x_map = {
            (soa, origin): x
            for soa, origin, x, _, _ in cells
        }

        physical = fusion[fusion["percept_origin"] == "congruent"].copy()

        physical_by_participant = (
            physical
            .groupby("participant")["plot_confidence"]
            .mean()
        )

        for soa in ["standard", "short"]:
            illusory = fusion[
                (fusion["soa_type"] == soa)
                & (fusion["percept_origin"] == "illusory")
            ].copy()

            illusory_by_participant = (
                illusory
                .groupby("participant")["plot_confidence"]
                .mean()
            )

            common_participants = sorted(
                set(physical_by_participant.index)
                & set(illusory_by_participant.index)
            )

            for participant in common_participants:
                ax.plot(
                    [
                        x_map[("none", "congruent")],
                        x_map[(soa, "illusory")],
                    ],
                    [
                        physical_by_participant.loc[participant],
                        illusory_by_participant.loc[participant],
                    ],
                    color=colors["line"],
                    linewidth=0.55,
                    alpha=0.26,
                    zorder=1,
                )

        for soa, origin, x, _, base_condition in cells:
            cell = fusion[
                (fusion["soa_type"] == soa)
                & (fusion["percept_origin"] == origin)
            ].copy()

            if cell.empty and soa == "none" and origin == "congruent":
                cell = fusion[fusion["percept_origin"] == "congruent"].copy()

            if cell.empty:
                continue

            cell = (
                cell
                .groupby("participant", as_index=False)["plot_confidence"]
                .mean()
            )

            y = cell["plot_confidence"].to_numpy()
            jitter = rng.normal(0, 0.022, size=len(cell))
            color = colors[base_condition]

            ax.scatter(
                np.full(len(cell), x) + jitter,
                y,
                s=20,
                color=color,
                alpha=0.58,
                edgecolor="none",
                zorder=2,
            )

            mean = np.mean(y)
            sem = np.std(y, ddof=1) / np.sqrt(len(y)) if len(y) > 1 else 0.0

            ax.errorbar(
                x,
                mean,
                yerr=sem,
                fmt="o",
                color=colors["mean"],
                ecolor=colors["mean"],
                markersize=4.5,
                elinewidth=1.05,
                capsize=2.8,
                capthick=1.05,
                zorder=4,
            )

        ax.set_title('Percept rapporté « 1 flash »', pad=6)
        ax.set_xticks([x for _, _, x, _, _ in cells])
        ax.set_xticklabels([label for _, _, _, label, _ in cells])
        ax.set_xlabel("Condition / SOA", labelpad=7)

        plt.setp(ax.get_yticklabels(), visible=False)

        ax.text(
            -0.12,
            1.04,
            "D",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    # ------------------------------------------------------------
    # Draw panels
    # ------------------------------------------------------------

    one_flash_conditions = [
        ("A1V1", "none", "A1V1"),
        ("A1V1_A2", "short", "A1V1_A2\ncourt"),
        ("A1V1_A2", "standard", "A1V1_A2\nstandard"),
    ]

    two_flash_conditions = [
        ("A1V1_A2V2", "short", "A1V1_A2V2\ncourt"),
        ("A1V1_A2V2", "standard", "A1V1_A2V2\nstandard"),
        ("A1V1_V2", "short", "A1V1_V2\ncourt"),
        ("A1V1_V2", "standard", "A1V1_V2\nstandard"),
    ]

    draw_global_panel(
        ax_a,
        one_flash_conditions,
        "Stimulation physique : 1 flash",
        "A",
        show_ylabel=True,
    )

    draw_global_panel(
        ax_b,
        two_flash_conditions,
        "Stimulation physique : 2 flashs",
        "B",
        show_ylabel=False,
    )

    draw_matched_two_panel(ax_c)
    draw_matched_one_panel(ax_d)

    # ------------------------------------------------------------
    # Shared formatting for panels C and D
    # ------------------------------------------------------------

    for ax in [ax_c, ax_d]:
        ax.set_ylim(43, 102)
        ax.set_yticks([50, 60, 70, 80, 90, 100])

        ax.grid(axis="y", color="0.92", linewidth=0.65)
        ax.grid(axis="x", visible=False)
        ax.set_axisbelow(True)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.tick_params(axis="x", length=0, pad=3)
        ax.tick_params(axis="y", direction="out", length=3)

    # ------------------------------------------------------------
    # Global legend
    # ------------------------------------------------------------

    legend_handles = [
        plt.Line2D(
            [0], [0],
            marker="o",
            linestyle="none",
            markerfacecolor=colors["A1V1"],
            markeredgecolor="none",
            markersize=6,
            label="A1V1",
        ),
        plt.Line2D(
            [0], [0],
            marker="o",
            linestyle="none",
            markerfacecolor=colors["A1V1_A2"],
            markeredgecolor="none",
            markersize=6,
            label="A1V1_A2",
        ),
        plt.Line2D(
            [0], [0],
            marker="o",
            linestyle="none",
            markerfacecolor=colors["A1V1_A2V2"],
            markeredgecolor="none",
            markersize=6,
            label="A1V1_A2V2",
        ),
        plt.Line2D(
            [0], [0],
            marker="o",
            linestyle="none",
            markerfacecolor=colors["A1V1_V2"],
            markeredgecolor="none",
            markersize=6,
            label="A1V1_V2",
        ),
        plt.Line2D(
            [0], [0],
            marker="o",
            linestyle="none",
            markerfacecolor=colors["mean"],
            markeredgecolor=colors["mean"],
            markersize=6,
            label="Moyenne ± SEM",
        ),
    ]

    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.995),
        ncol=5,
        frameon=False,
        fontsize=8.5,
        columnspacing=1.2,
        handletextpad=0.4,
    )

    # ------------------------------------------------------------
    # Save the manuscript figure
    # ------------------------------------------------------------

    outpath = Path(outpath)
    outpath.parent.mkdir(parents=True, exist_ok=True)

    fig.tight_layout(rect=(0, 0, 1, 0.94))

    fig.savefig(outpath, bbox_inches="tight")

    plt.close(fig)