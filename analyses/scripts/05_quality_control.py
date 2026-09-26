from __future__ import annotations

"""Quality-control outputs for the SIFI multisensory participant analysis pipeline.

This script does not change the analysis data. It creates diagnostic tables and
figures that document trial counts, participant-level patterns and block-wise
stability. These outputs are intended for checks/appendices, not as primary
confirmatory analyses.
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PROCESSED_DIR, OUTPUTS_DIR  # noqa: E402

DATA_FILE = PROCESSED_DIR / "model_ready_trials.csv"
OUT_TABLES = OUTPUTS_DIR / "tables" / "quality_control"
OUT_FIGURES = OUTPUTS_DIR / "figures" / "quality_control"
OUT_REPORTS = OUTPUTS_DIR / "reports"


def _ensure_dirs() -> None:
    OUT_TABLES.mkdir(parents=True, exist_ok=True)
    OUT_FIGURES.mkdir(parents=True, exist_ok=True)
    OUT_REPORTS.mkdir(parents=True, exist_ok=True)


def _to_num(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def _sem(values: pd.Series) -> float:
    x = pd.to_numeric(values, errors="coerce").dropna()
    if len(x) <= 1:
        return np.nan
    return float(x.std(ddof=1) / np.sqrt(len(x)))


def _save_csv(df: pd.DataFrame, filename: str) -> None:
    df.to_csv(OUT_TABLES / filename, index=False, encoding="utf-8-sig")


def make_trial_count_tables(df: pd.DataFrame) -> None:
    group_cols = ["participant", "base_condition", "soa_type"]
    trials = (
        df.groupby(group_cols, dropna=False, observed=True)
        .agg(
            n_trials=("participant", "size"),
            n_response_missing=("response2", lambda x: int(pd.to_numeric(x, errors="coerce").isna().sum())),
            n_confidence_missing=("confidence", lambda x: int(pd.to_numeric(x, errors="coerce").isna().sum())),
            response2_rate=("response2", "mean"),
            illusion_rate=("illusion", "mean"),
            mean_confidence=("confidence", "mean"),
        )
        .reset_index()
    )
    trials["response2_rate_percent"] = 100 * trials["response2_rate"]
    trials["illusion_rate_percent"] = 100 * trials["illusion_rate"]
    _save_csv(trials, "trials_by_participant_condition_soa.csv")

    participants = (
        df.groupby("participant", dropna=False, observed=True)
        .agg(
            n_trials=("participant", "size"),
            n_conditions=("base_condition", "nunique"),
            n_blocks=("block", "nunique") if "block" in df.columns else ("participant", "size"),
            response2_rate=("response2", "mean"),
            illusion_rate=("illusion", "mean"),
            mean_confidence=("confidence", "mean"),
            sd_confidence=("confidence", "std"),
            n_response_missing=("response2", lambda x: int(pd.to_numeric(x, errors="coerce").isna().sum())),
            n_confidence_missing=("confidence", lambda x: int(pd.to_numeric(x, errors="coerce").isna().sum())),
        )
        .reset_index()
    )
    participants["response2_rate_percent"] = 100 * participants["response2_rate"]
    participants["illusion_rate_percent"] = 100 * participants["illusion_rate"]
    _save_csv(participants, "participant_global_quality_control.csv")


def make_matched_trial_count_table(df: pd.DataFrame) -> None:
    rows: list[dict[str, object]] = []
    for soa in ["standard", "short"]:
        congruent = df[
            (df["matched_percept"] == "two")
            & (df["percept_origin"] == "congruent")
            & (df["soa_type"] == soa)
            & df["confidence"].notna()
        ]
        illusory = df[
            (df["matched_percept"] == "two")
            & (df["percept_origin"] == "illusory")
            & (df["soa_type"] == soa)
            & df["confidence"].notna()
        ]
        rows.append(
            {
                "analysis": "Fission: reported 2 flashes",
                "soa": soa,
                "n_participants_congruent": congruent["participant"].nunique(),
                "n_participants_illusory": illusory["participant"].nunique(),
                "n_trials_congruent": len(congruent),
                "n_trials_illusory": len(illusory),
            }
        )

    congruent_one = df[
        (df["matched_percept"] == "one")
        & (df["percept_origin"] == "congruent")
        & df["confidence"].notna()
    ]
    for soa in ["standard", "short"]:
        illusory = df[
            (df["matched_percept"] == "one")
            & (df["percept_origin"] == "illusory")
            & (df["soa_type"] == soa)
            & df["confidence"].notna()
        ]
        rows.append(
            {
                "analysis": "Fusion: reported 1 flash",
                "soa": soa,
                "n_participants_congruent": congruent_one["participant"].nunique(),
                "n_participants_illusory": illusory["participant"].nunique(),
                "n_trials_congruent": len(congruent_one),
                "n_trials_illusory": len(illusory),
            }
        )

    _save_csv(pd.DataFrame(rows), "matched_percept_confidence_trial_counts.csv")


def plot_group_block_illusion(df: pd.DataFrame) -> None:
    if not {"participant", "block", "illusion_type", "soa_type", "illusion"}.issubset(df.columns):
        return
    sub = df[
        df["illusion_type"].isin(["fission", "fusion"])
        & df["soa_type"].isin(["standard", "short"])
        & df["block"].notna()
        & df["illusion"].notna()
    ].copy()
    if sub.empty:
        return

    summary = (
        sub.groupby(["participant", "block", "illusion_type", "soa_type"], observed=True)
        .agg(illusion_rate=("illusion", "mean"))
        .reset_index()
    )
    group = (
        summary.groupby(["block", "illusion_type", "soa_type"], observed=True)
        .agg(mean=("illusion_rate", "mean"), sem=("illusion_rate", _sem))
        .reset_index()
    )
    group["cell"] = group["illusion_type"].astype(str) + " " + group["soa_type"].astype(str)

    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    for cell, cdat in group.groupby("cell", observed=True):
        cdat = cdat.sort_values("block")
        ax.errorbar(cdat["block"], cdat["mean"], yerr=cdat["sem"], marker="o", capsize=3, label=cell)
    ax.set_xlabel("Block")
    ax.set_ylabel("Illusion rate")
    ax.set_ylim(-0.02, 1.05)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="0.92")
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(OUT_FIGURES / "qc_block_evolution_illusion_group.pdf", bbox_inches="tight")
    fig.savefig(OUT_FIGURES / "qc_block_evolution_illusion_group.svg", bbox_inches="tight")
    plt.close(fig)


def plot_group_block_confidence(df: pd.DataFrame) -> None:
    if not {"participant", "block", "matched_percept", "percept_origin", "confidence"}.issubset(df.columns):
        return
    sub = df[
        df["block"].notna()
        & df["confidence"].notna()
        & df["matched_percept"].isin(["one", "two"])
        & df["percept_origin"].isin(["congruent", "illusory"])
    ].copy()
    if sub.empty:
        return
    summary = (
        sub.groupby(["participant", "block", "matched_percept", "percept_origin"], observed=True)
        .agg(mean_confidence=("confidence", "mean"))
        .reset_index()
    )
    group = (
        summary.groupby(["block", "matched_percept", "percept_origin"], observed=True)
        .agg(mean=("mean_confidence", "mean"), sem=("mean_confidence", _sem))
        .reset_index()
    )
    group["cell"] = group["matched_percept"].astype(str) + " " + group["percept_origin"].astype(str)

    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    for cell, cdat in group.groupby("cell", observed=True):
        cdat = cdat.sort_values("block")
        ax.errorbar(cdat["block"], cdat["mean"], yerr=cdat["sem"], marker="o", capsize=3, label=cell)
    ax.set_xlabel("Block")
    ax.set_ylabel("Mean confidence (%)")
    ax.set_ylim(45, 102)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="0.92")
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(OUT_FIGURES / "qc_block_evolution_confidence_group.pdf", bbox_inches="tight")
    fig.savefig(OUT_FIGURES / "qc_block_evolution_confidence_group.svg", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    _ensure_dirs()
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Run scripts/01_prepare_data.py first. Missing file: {DATA_FILE}")
    df = pd.read_csv(DATA_FILE)
    df = _to_num(df, ["block", "trial", "response2", "illusion", "accuracy", "confidence", "rt", "rt_conf"])

    make_trial_count_tables(df)
    make_matched_trial_count_table(df)
    plot_group_block_illusion(df)
    plot_group_block_confidence(df)

    report = [
        "QUALITY CONTROL REPORT",
        "======================",
        "",
        f"Rows: {len(df)}",
        f"Participants: {df['participant'].nunique() if 'participant' in df.columns else 'NA'}",
        "",
        "Generated tables:",
        "- outputs/tables/quality_control/trials_by_participant_condition_soa.csv",
        "- outputs/tables/quality_control/participant_global_quality_control.csv",
        "- outputs/tables/quality_control/matched_percept_confidence_trial_counts.csv",
        "",
        "Generated figures:",
        "- outputs/figures/quality_control/qc_block_evolution_illusion_group.pdf",
        "- outputs/figures/quality_control/qc_block_evolution_confidence_group.pdf",
        "",
        "Use these outputs as diagnostics/appendix material, not as primary confirmatory tests.",
    ]
    (OUT_REPORTS / "quality_control_report.txt").write_text("\n".join(report), encoding="utf-8")
    print("Quality-control tables, figures, and report saved.")


if __name__ == "__main__":
    main()
