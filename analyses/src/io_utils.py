from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from src.config import (
    TRIALS_DIR,
    PROCESSED_DIR,
    FIGURES_DIR,
    TABLES_DIR,
    REPORTS_DIR,
    PERCEPTUAL_FIGURES_DIR,
    CONFIDENCE_FIGURES_DIR,
    DIAGNOSTIC_FIGURES_DIR,
    DESCRIPTIVE_TABLES_DIR,
    MODEL_TABLES_DIR,
    RAW_TRIALS_PATTERN,
)


def ensure_directories() -> None:
    """Create all output directories if they do not exist."""
    for path in [
        TRIALS_DIR,
        PROCESSED_DIR,
        FIGURES_DIR,
        TABLES_DIR,
        REPORTS_DIR,
        PERCEPTUAL_FIGURES_DIR,
        CONFIDENCE_FIGURES_DIR,
        DIAGNOSTIC_FIGURES_DIR,
        DESCRIPTIVE_TABLES_DIR,
        MODEL_TABLES_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def list_trial_files(trials_dir: Path = TRIALS_DIR) -> list[Path]:
    """Return all trial CSV files found in data/trials/."""
    return sorted(trials_dir.glob(RAW_TRIALS_PATTERN))


def infer_participant_from_filename(path: Path) -> str:
    """Infer a participant id from a filename when the CSV lacks a participant column."""
    name = path.stem
    suffix = "_trials"
    if name.endswith(suffix):
        name = name[: -len(suffix)]
    return name


def load_trial_file(path: Path) -> pd.DataFrame:
    """Load a single trial CSV and add source metadata."""
    df = pd.read_csv(path)
    df["source_file"] = path.name
    if "participant" not in df.columns:
        df["participant"] = infer_participant_from_filename(path)
    return df


def load_all_trials(trials_dir: Path = TRIALS_DIR) -> pd.DataFrame:
    """Load and concatenate all *_trials.csv files."""
    files = list_trial_files(trials_dir)
    if not files:
        raise FileNotFoundError(
            f"No files matching {RAW_TRIALS_PATTERN!r} found in {trials_dir}. "
            "Place your CSV files in data/trials/."
        )
    dfs = [load_trial_file(path) for path in files]
    return pd.concat(dfs, ignore_index=True, sort=False)


def save_csv(df: pd.DataFrame, path: Path, index: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check_required_columns(df: pd.DataFrame, required: Iterable[str]) -> list[str]:
    """Return missing columns from df."""
    return [col for col in required if col not in df.columns]
