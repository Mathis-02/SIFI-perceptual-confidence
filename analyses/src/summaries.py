from __future__ import annotations

import numpy as np
import pandas as pd


def _sem(x: pd.Series) -> float:
    x = x.dropna()
    if len(x) <= 1:
        return np.nan
    return float(x.std(ddof=1) / np.sqrt(len(x)))


def summarize_response2(df: pd.DataFrame) -> pd.DataFrame:
    """Response-2 rates by participant, base condition and SOA."""
    return (
        df.groupby(["participant", "base_condition", "soa_type"], observed=True)
        .agg(
            n_trials=("response2", "count"),
            response2_rate=("response2", "mean"),
            mean_confidence=("confidence", "mean"),
            accuracy=("accuracy", "mean"),
        )
        .reset_index()
    )


def summarize_response2_group(participant_summary: pd.DataFrame) -> pd.DataFrame:
    return (
        participant_summary.groupby(["base_condition", "soa_type"], observed=True)
        .agg(
            n_participants=("participant", "nunique"),
            mean_response2_rate=("response2_rate", "mean"),
            sem_response2_rate=("response2_rate", _sem),
            mean_confidence=("mean_confidence", "mean"),
            sem_confidence=("mean_confidence", _sem),
            mean_accuracy=("accuracy", "mean"),
            sem_accuracy=("accuracy", _sem),
        )
        .reset_index()
    )


def summarize_illusion_rates(df: pd.DataFrame) -> pd.DataFrame:
    """Illusion rates by participant, illusion type and SOA for incongruent conditions."""
    sub = df[df["illusion_type"].isin(["fission", "fusion"])].copy()
    return (
        sub.groupby(["participant", "illusion_type", "soa_type"], observed=True)
        .agg(
            n_trials=("illusion", "count"),
            illusion_rate=("illusion", "mean"),
            mean_confidence=("confidence", "mean"),
        )
        .reset_index()
    )


def summarize_illusion_group(illusion_summary: pd.DataFrame) -> pd.DataFrame:
    return (
        illusion_summary.groupby(["illusion_type", "soa_type"], observed=True)
        .agg(
            n_participants=("participant", "nunique"),
            mean_illusion_rate=("illusion_rate", "mean"),
            sem_illusion_rate=("illusion_rate", _sem),
            mean_confidence=("mean_confidence", "mean"),
            sem_confidence=("mean_confidence", _sem),
        )
        .reset_index()
    )


def summarize_matched_confidence(df: pd.DataFrame) -> pd.DataFrame:
    """Confidence summaries for matched percept analyses."""
    sub = df[df["matched_percept"].isin(["one", "two"]) & df["percept_origin"].isin(["illusory", "congruent"])].copy()
    return (
        sub.groupby(["participant", "matched_percept", "percept_origin", "base_condition", "soa_type"], observed=True)
        .agg(
            n_trials=("confidence", "count"),
            mean_confidence=("confidence", "mean"),
            median_confidence=("confidence", "median"),
            sd_confidence=("confidence", "std"),
        )
        .reset_index()
    )


def summarize_correct_incorrect_confidence(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["participant", "base_condition", "soa_type", "accuracy"], observed=True)
        .agg(
            n_trials=("confidence", "count"),
            mean_confidence=("confidence", "mean"),
            median_confidence=("confidence", "median"),
        )
        .reset_index()
    )
