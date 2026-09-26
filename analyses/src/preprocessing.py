from __future__ import annotations

import re
import numpy as np
import pandas as pd

from src.config import (
    FISSION_CONDITION,
    FUSION_CONDITION,
    CONGRUENT_ONE_CONDITION,
    CONGRUENT_TWO_CONDITION,
    KNOWN_BASE_CONDITIONS,
    SOA_NONE_LABEL,
)


def _to_numeric_response(value) -> float:
    """Convert responses like 1, 2, '1', '2 flashes' to numeric values when possible."""
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    text = str(value).strip().lower()
    match = re.search(r"[12]", text)
    if match:
        return float(match.group(0))
    return np.nan


def _infer_base_condition(condition: str) -> str:
    """Infer base condition by removing common SOA suffixes when base_condition is absent."""
    if pd.isna(condition):
        return np.nan
    c = str(condition).strip()
    if c in KNOWN_BASE_CONDITIONS:
        return c
    # Remove common suffixes such as _short, _standard, _long, -short, etc.
    for suffix in ["_short", "_standard", "_long", "-short", "-standard", "-long"]:
        if c.endswith(suffix):
            candidate = c[: -len(suffix)]
            if candidate in KNOWN_BASE_CONDITIONS:
                return candidate
    # Fallback: find a known condition included in the string, longest first.
    for base in sorted(KNOWN_BASE_CONDITIONS, key=len, reverse=True):
        if base in c:
            return base
    return c


def _infer_soa_type(row: pd.Series) -> str:
    """Infer SOA type from existing columns or condition names."""
    base = row.get("base_condition", np.nan)
    if base == CONGRUENT_ONE_CONDITION:
        return SOA_NONE_LABEL

    for col in ["soa_type", "soa_label", "SOA_type"]:
        if col in row.index and pd.notna(row[col]):
            value = str(row[col]).strip().lower()
            if value and value not in {"nan", "none", "na"}:
                return value

    condition = str(row.get("condition", "")).lower()
    if "short" in condition:
        return "short"
    if "standard" in condition:
        return "standard"
    if "long" in condition:
        return "standard"

    # Infer from numeric SOA if available.
    for col in ["soa_ms", "SOA_ms", "soa", "SOA"]:
        if col in row.index and pd.notna(row[col]):
            try:
                val = float(row[col])
            except Exception:
                continue
            if val < 65:
                return "short"
            return "standard"

    return "unknown"


def _infer_soa_ms(row: pd.Series) -> float:
    for col in ["soa_ms", "SOA_ms", "soa", "SOA"]:
        if col in row.index and pd.notna(row[col]):
            try:
                return float(row[col])
            except Exception:
                pass
    soa_type = row.get("soa_type", np.nan)
    if soa_type == "short":
        return 50.0
    if soa_type == "standard":
        return 83.0
    return np.nan


def prepare_trials(raw: pd.DataFrame) -> pd.DataFrame:
    """Create a clean model-ready trial table from raw trial CSVs."""
    df = raw.copy()

    # Basic identifiers.
    df["participant"] = df["participant"].astype(str)
    df["condition"] = df["condition"].astype(str).str.strip()

    if "base_condition" not in df.columns:
        df["base_condition"] = df["condition"].apply(_infer_base_condition)
    else:
        df["base_condition"] = df["base_condition"].fillna(df["condition"].apply(_infer_base_condition))
        df["base_condition"] = df["base_condition"].astype(str).str.strip()

    # SOA harmonisation.
    df["soa_type"] = df.apply(_infer_soa_type, axis=1)
    df["soa_ms_clean"] = df.apply(_infer_soa_ms, axis=1)

    # Response and confidence.
    df["response_num"] = df["response"].apply(_to_numeric_response)
    df["response2"] = np.where(df["response_num"] == 2, 1,
                         np.where(df["response_num"] == 1, 0, np.nan))

    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce")

    # Correct answer: use existing column when valid, otherwise infer from base condition.
    if "correct_answer" in df.columns:
        df["correct_answer_num"] = df["correct_answer"].apply(_to_numeric_response)
    else:
        df["correct_answer_num"] = np.nan

    inferred_correct = {
        CONGRUENT_ONE_CONDITION: 1,
        FISSION_CONDITION: 1,
        FUSION_CONDITION: 2,
        CONGRUENT_TWO_CONDITION: 2,
    }
    inferred = df["base_condition"].map(inferred_correct).astype(float)
    df["correct_answer_num"] = df["correct_answer_num"].fillna(inferred)

    if "accuracy" in df.columns:
        df["accuracy"] = pd.to_numeric(df["accuracy"], errors="coerce")
    else:
        df["accuracy"] = np.nan
    inferred_acc = np.where(df["response_num"] == df["correct_answer_num"], 1,
                     np.where(df["response_num"].isin([1, 2]), 0, np.nan))
    df["accuracy"] = df["accuracy"].fillna(pd.Series(inferred_acc, index=df.index))

    # Illusion recoding for incongruent conditions.
    df["illusion_type"] = pd.Series(
        np.select(
            [df["base_condition"].eq(FISSION_CONDITION), df["base_condition"].eq(FUSION_CONDITION)],
            ["fission", "fusion"],
            default=None,
        ),
        index=df.index,
        dtype="object",
    )
    df["illusion"] = np.nan
    fission_mask = df["base_condition"].eq(FISSION_CONDITION)
    fusion_mask = df["base_condition"].eq(FUSION_CONDITION)
    df.loc[fission_mask, "illusion"] = df.loc[fission_mask, "response2"]
    df.loc[fusion_mask, "illusion"] = 1 - df.loc[fusion_mask, "response2"]

    # Matched-percept confidence origin.
    df["matched_percept"] = pd.Series(pd.NA, index=df.index, dtype="object")
    df["percept_origin"] = pd.Series(pd.NA, index=df.index, dtype="object")

    # Percept 'two flashes': fission illusory vs congruent two.
    mask = df["base_condition"].eq(FISSION_CONDITION) & df["response2"].eq(1)
    df.loc[mask, "matched_percept"] = "two"
    df.loc[mask, "percept_origin"] = "illusory"

    mask = df["base_condition"].eq(CONGRUENT_TWO_CONDITION) & df["response2"].eq(1)
    df.loc[mask, "matched_percept"] = "two"
    df.loc[mask, "percept_origin"] = "congruent"

    # Percept 'one flash': fusion illusory vs congruent one.
    mask = df["base_condition"].eq(FUSION_CONDITION) & df["response2"].eq(0)
    df.loc[mask, "matched_percept"] = "one"
    df.loc[mask, "percept_origin"] = "illusory"

    mask = df["base_condition"].eq(CONGRUENT_ONE_CONDITION) & df["response2"].eq(0)
    df.loc[mask, "matched_percept"] = "one"
    df.loc[mask, "percept_origin"] = "congruent"

    # Useful ordering variables.
    condition_order = [
        CONGRUENT_ONE_CONDITION,
        FISSION_CONDITION,
        FUSION_CONDITION,
        CONGRUENT_TWO_CONDITION,
    ]
    df["base_condition"] = pd.Categorical(df["base_condition"], categories=condition_order, ordered=True)
    df["soa_type"] = pd.Categorical(df["soa_type"], categories=[SOA_NONE_LABEL, "short", "standard", "unknown"], ordered=True)

    # Cell-level condition variable used by the v2 response2 manipulation-check model.
    # A1V1 has no physical SOA, so it remains a single cell rather than being
    # assigned an artificial SOA.
    df["condition_cell"] = df["base_condition"].astype(str)
    has_physical_soa = df["soa_type"].astype(str).isin(["standard", "short"])
    df.loc[has_physical_soa, "condition_cell"] = (
        df.loc[has_physical_soa, "base_condition"].astype(str)
        + "_"
        + df.loc[has_physical_soa, "soa_type"].astype(str)
    )
    df.loc[df["base_condition"].astype(str).eq(CONGRUENT_ONE_CONDITION), "condition_cell"] = CONGRUENT_ONE_CONDITION

    return df
