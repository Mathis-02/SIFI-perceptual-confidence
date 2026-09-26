from __future__ import annotations

import numpy as np
import pandas as pd


def auroc2_from_confidence_accuracy(confidence: pd.Series, accuracy: pd.Series) -> float:
    """Compute AUROC2 as P(conf_correct > conf_incorrect) + 0.5 ties.

    Returns NaN if there are no correct or no incorrect trials.
    """
    conf = pd.to_numeric(confidence, errors="coerce")
    acc = pd.to_numeric(accuracy, errors="coerce")
    valid = conf.notna() & acc.isin([0, 1])
    conf = conf[valid]
    acc = acc[valid]
    correct = conf[acc == 1].to_numpy()
    incorrect = conf[acc == 0].to_numpy()
    if len(correct) == 0 or len(incorrect) == 0:
        return np.nan
    greater = 0
    ties = 0
    total = len(correct) * len(incorrect)
    for c in correct:
        greater += np.sum(c > incorrect)
        ties += np.sum(c == incorrect)
    return float((greater + 0.5 * ties) / total)


def auroc2_by_participant_condition(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, g in df.groupby(["participant", "base_condition", "soa_type"], observed=True):
        participant, condition, soa = keys
        rows.append({
            "participant": participant,
            "base_condition": condition,
            "soa_type": soa,
            "n_trials": len(g),
            "n_correct": int((g["accuracy"] == 1).sum()),
            "n_incorrect": int((g["accuracy"] == 0).sum()),
            "auroc2": auroc2_from_confidence_accuracy(g["confidence"], g["accuracy"]),
        })
    return pd.DataFrame(rows)
