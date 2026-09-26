"""Incremental trial-level CSV logging."""

import csv
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

TRIALS_HEADER = [
    "participant",
    "block",
    "trial",
    "condition",
    "base_condition",
    "soa_type",
    "soa_ms",
    "position",
    "response",
    "rt",
    "correct_answer",
    "accuracy",
    "illusion",
    "illusion_type",
    "fission_illusion",
    "fusion_illusion",
    "confidence",
    "confidence_mode",
    "rt_conf",
    "fixation_programmed_s",
    "fixation_measured_s",
    "flash_frames",
    "isi_frames",
    "flash1_onset_time",
    "flash1_offset_time",
    "isi_blank_start_time",
    "isi_blank_end_time",
    "flash2_onset_time",
    "flash2_offset_time",
    "beep1_scheduled_ptb_time",
    "beep1_flip_proxy_time",
    "beep2_scheduled_ptb_time",
    "beep2_flip_proxy_time",
    "soa_visual_programmed_s",
    "soa_visual_flip_measured_s",
    "soa_audio_programmed_s",
    "soa_audio_scheduled_s",
    "soa_audio_flip_proxy_s",
    "isi_blank_programmed_s",
    "isi_blank_measured_s",
    "dropped_fixation",
    "dropped_stim1",
    "dropped_isi",
    "dropped_stim2",
    "dropped_poststim",
    "dropped_frames_total",
    "trial_total_s",
    "error",
]


class TrialLogger:
    """Write one trial at a time and flush after every row."""

    def __init__(self, trials_path: str | Path):
        self.trials_path = Path(trials_path)
        self.trials_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.trials_path.open(
            "w", newline="", encoding="utf-8"
        )
        self._writer = csv.DictWriter(
            self._file,
            fieldnames=TRIALS_HEADER,
            extrasaction="raise",
        )
        self._writer.writeheader()
        self._file.flush()

    def log_trial(self, row: Mapping[str, Any] | Sequence[Any]) -> None:
        """Write a complete trial row.

        Mappings are preferred because they make column assignments explicit.
        Positional sequences remain accepted for backward compatibility.
        """
        if isinstance(row, Mapping):
            unknown = set(row) - set(TRIALS_HEADER)
            if unknown:
                names = ", ".join(sorted(unknown))
                raise ValueError(f"Unknown trial fields: {names}.")
            output = {field: row.get(field, "") for field in TRIALS_HEADER}
        else:
            if len(row) != len(TRIALS_HEADER):
                raise ValueError(
                    f"Row has {len(row)} columns but the trial header has "
                    f"{len(TRIALS_HEADER)}."
                )
            output = dict(zip(TRIALS_HEADER, row))

        self._writer.writerow(output)
        self._file.flush()

    def log_error(
        self,
        participant_id: str,
        block_index: int,
        trial_index: int,
        condition: str,
        position: str,
        error_message: str,
        *,
        base_condition: str = "",
        soa_type: str = "",
        soa_ms: Any = "",
    ) -> None:
        """Record a failed trial without discarding the rest of the session."""
        self.log_trial(
            {
                "participant": participant_id,
                "block": block_index,
                "trial": trial_index,
                "condition": condition,
                "base_condition": base_condition,
                "soa_type": soa_type,
                "soa_ms": soa_ms,
                "position": position,
                "error": error_message,
            }
        )

    def close(self) -> None:
        if self._file.closed:
            return
        try:
            self._file.flush()
        finally:
            self._file.close()

    def __enter__(self) -> "TrialLogger":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
