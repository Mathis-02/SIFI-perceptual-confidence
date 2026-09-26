"""Session metadata storage and participant identifier validation."""

import csv
import math
import os
import re
from pathlib import Path
from typing import Any, Mapping

SESSION_HEADER = [
    "participant",
    "date_start",
    "date_end",
    "completed",
    "abort_reason",
    "rng_seed",
    "code_version",
    "design_mode",
    "n_blocks",
    "trials_per_block",
    "trials_total",
    "standard_soa_ms",
    "short_soa_ms",
    "debug_mode",
    "pilot_mode",
    "lab_mode",
    "confidence_mode",
    "framerate",
    "frame_period",
    "resolution",
    "screen_width_cm",
    "pixels_per_cm",
    "viewing_distance_cm",
    "viewing_distance_method",
    "viewing_distance_n_valid",
    "viewing_distance_iqr_cm",
    "viewing_distance_notes",
    "flash_frames",
    "standard_isi_frames",
    "standard_soa_programmed_s",
    "standard_isi_programmed_s",
    "frame_median_ms",
    "frame_sd_ms",
    "frame_mean_ms",
    "n_trials_logged",
    "n_trials_valid",
    "n_trial_errors",
    "n_trials_with_dropped_frames",
    "dropped_frames_any_pct",
    "dropped_frames_total",
    "dropped_fixation_total",
    "dropped_stim1_total",
    "dropped_isi_total",
    "dropped_stim2_total",
    "dropped_poststim_total",
    "mean_visual_soa_error_ms",
    "max_abs_visual_soa_error_ms",
    "mean_audio_scheduled_error_ms",
    "max_abs_audio_scheduled_error_ms",
    "mean_isi_error_ms",
    "max_abs_isi_error_ms",
]

_INVALID_PARTICIPANT_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_participant_id(raw_participant_id: str) -> str:
    """Return a filesystem-safe participant identifier.

    Spaces and unsupported characters are replaced with underscores. The
    result must retain at least one alphanumeric character.
    """
    cleaned = _INVALID_PARTICIPANT_CHARS.sub("_", raw_participant_id.strip())
    cleaned = cleaned.strip("._-")

    if not cleaned or not any(char.isalnum() for char in cleaned):
        raise ValueError("Participant ID must contain an alphanumeric character.")
    return cleaned


def _csv_value(value: Any) -> Any:
    if isinstance(value, float) and math.isnan(value):
        return ""
    return value


def write_session_csv(
    session_path: str | Path,
    values: Mapping[str, Any],
    *,
    atomic: bool,
) -> None:
    """Write the single-row session metadata file."""
    path = Path(session_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    output_path = path.with_suffix(path.suffix + ".tmp") if atomic else path

    with output_path.open("w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=SESSION_HEADER)
        writer.writeheader()
        writer.writerow(
            {field: _csv_value(values.get(field, "")) for field in SESSION_HEADER}
        )
        file_obj.flush()
        os.fsync(file_obj.fileno())

    if atomic:
        os.replace(output_path, path)
