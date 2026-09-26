"""Descriptive end-of-session summaries for acquisition quality control.

This module intentionally contains no inferential statistics. It reports the
illusion rates, associated confidence ratings, blockwise stability, and timing
quality needed to verify a completed acquisition session.
"""

import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean, pstdev
from typing import Any, Iterable, Mapping

CONDITION_SUMMARY_HEADER = [
    "participant",
    "design_mode",
    "condition",
    "base_condition",
    "soa_type",
    "soa_ms",
    "illusion_type",
    "n_trials_logged",
    "n_trials_valid",
    "n_trial_errors",
    "illusion_rate",
    "mean_confidence",
    "mean_confidence_illusion",
    "mean_confidence_no_illusion",
    "response1_rate",
    "response2_rate",
    "block_illusion_rate_sd",
    "block_mean_confidence_sd",
    "dropped_frames_any_pct",
    "dropped_frames_total",
    "mean_visual_soa_error_ms",
    "max_abs_visual_soa_error_ms",
    "mean_audio_scheduled_error_ms",
    "max_abs_audio_scheduled_error_ms",
    "mean_isi_error_ms",
    "max_abs_isi_error_ms",
]

BLOCK_SUMMARY_HEADER = [
    "participant",
    "design_mode",
    "block",
    "condition",
    "base_condition",
    "soa_type",
    "soa_ms",
    "illusion_type",
    "n_trials_logged",
    "n_trials_valid",
    "n_trial_errors",
    "illusion_rate",
    "mean_confidence",
    "mean_confidence_illusion",
    "mean_confidence_no_illusion",
    "dropped_frames_any_pct",
    "dropped_frames_total",
]


@dataclass(frozen=True)
class SessionSummary:
    condition_rows: list[dict[str, Any]]
    block_rows: list[dict[str, Any]]
    timing_metrics: dict[str, Any]


def _number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _mean(values: Iterable[float | None]) -> float | None:
    valid = [value for value in values if value is not None]
    return fmean(valid) if valid else None


def _population_sd(values: Iterable[float | None]) -> float | None:
    valid = [value for value in values if value is not None]
    if not valid:
        return None
    return 0.0 if len(valid) == 1 else pstdev(valid)


def _rate(flags: Iterable[bool]) -> float | None:
    values = list(flags)
    return fmean(float(flag) for flag in values) if values else None


def _max_abs(values: Iterable[float | None]) -> float | None:
    valid = [abs(value) for value in values if value is not None]
    return max(valid) if valid else None


def _difference_ms(row: dict[str, str], measured: str, programmed: str) -> float | None:
    measured_value = _number(row.get(measured))
    programmed_value = _number(row.get(programmed))
    if measured_value is None or programmed_value is None:
        return None
    return (measured_value - programmed_value) * 1000.0


def _illusion_flag(base_condition: str, response: str) -> bool | None:
    if base_condition == "A1V1_A2":
        return response == "2"
    if base_condition == "A1V1_V2":
        return response == "1"
    return None


def _illusion_type(base_condition: str, stored_type: str) -> str:
    if stored_type in {"fission", "fusion"}:
        return stored_type
    if base_condition == "A1V1_A2":
        return "fission"
    if base_condition == "A1V1_V2":
        return "fusion"
    return "none"


def _valid_trials(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("response", "").strip() in {"1", "2"}]


def _summarize_group(rows: list[dict[str, str]]) -> dict[str, Any]:
    valid_rows = _valid_trials(rows)
    base_condition = rows[0].get("base_condition", "") if rows else ""
    illusion_flags = [
        _illusion_flag(base_condition, row.get("response", "").strip())
        for row in valid_rows
    ]
    defined_illusion_flags = [flag for flag in illusion_flags if flag is not None]

    confidence_values = [_number(row.get("confidence")) for row in valid_rows]
    confidence_illusion = [
        _number(row.get("confidence"))
        for row, flag in zip(valid_rows, illusion_flags)
        if flag is True
    ]
    confidence_no_illusion = [
        _number(row.get("confidence"))
        for row, flag in zip(valid_rows, illusion_flags)
        if flag is False
    ]

    dropped_values = [_number(row.get("dropped_frames_total")) for row in valid_rows]
    dropped_valid = [value for value in dropped_values if value is not None]

    visual_errors = [
        _difference_ms(
            row,
            "soa_visual_flip_measured_s",
            "soa_visual_programmed_s",
        )
        for row in valid_rows
    ]
    audio_errors = [
        _difference_ms(
            row,
            "soa_audio_scheduled_s",
            "soa_audio_programmed_s",
        )
        for row in valid_rows
    ]
    isi_errors = [
        _difference_ms(
            row,
            "isi_blank_measured_s",
            "isi_blank_programmed_s",
        )
        for row in valid_rows
    ]

    return {
        "n_trials_logged": len(rows),
        "n_trials_valid": len(valid_rows),
        "n_trial_errors": sum(bool(row.get("error", "").strip()) for row in rows),
        "illusion_rate": (
            _rate(defined_illusion_flags) if defined_illusion_flags else None
        ),
        "mean_confidence": _mean(confidence_values),
        "mean_confidence_illusion": _mean(confidence_illusion),
        "mean_confidence_no_illusion": _mean(confidence_no_illusion),
        "response1_rate": _rate(
            row.get("response", "").strip() == "1" for row in valid_rows
        ),
        "response2_rate": _rate(
            row.get("response", "").strip() == "2" for row in valid_rows
        ),
        "dropped_frames_any_pct": (
            100.0 * _rate(value > 0 for value in dropped_valid)
            if dropped_valid
            else None
        ),
        "dropped_frames_total": sum(dropped_valid) if dropped_valid else 0.0,
        "mean_visual_soa_error_ms": _mean(visual_errors),
        "max_abs_visual_soa_error_ms": _max_abs(visual_errors),
        "mean_audio_scheduled_error_ms": _mean(audio_errors),
        "max_abs_audio_scheduled_error_ms": _max_abs(audio_errors),
        "mean_isi_error_ms": _mean(isi_errors),
        "max_abs_isi_error_ms": _max_abs(isi_errors),
    }


def _read_trials(trials_path: str | Path) -> list[dict[str, str]]:
    with Path(trials_path).open(newline="", encoding="utf-8-sig") as file_obj:
        reader = csv.DictReader(file_obj)
        required = {"participant", "block", "condition", "base_condition", "response"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            fields = ", ".join(sorted(missing))
            raise ValueError(f"Trials file is missing required columns: {fields}.")
        return list(reader)


def build_session_summary(
    trials_path: str | Path,
    design_mode: str,
) -> SessionSummary:
    """Build condition, block, and timing summaries from a trial CSV."""
    rows = _read_trials(trials_path)
    participant = rows[0].get("participant", "") if rows else ""

    by_condition: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_block_condition: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)

    for row in rows:
        condition = row.get("condition", "")
        block = row.get("block", "")
        by_condition[condition].append(row)
        by_block_condition[(block, condition)].append(row)

    block_rows: list[dict[str, Any]] = []
    for (block, condition), group in sorted(
        by_block_condition.items(),
        key=lambda item: (_number(item[0][0]) or math.inf, item[0][1]),
    ):
        first = group[0]
        metrics = _summarize_group(group)
        block_rows.append(
            {
                "participant": participant,
                "design_mode": design_mode,
                "block": block,
                "condition": condition,
                "base_condition": first.get("base_condition", ""),
                "soa_type": first.get("soa_type", ""),
                "soa_ms": first.get("soa_ms", ""),
                "illusion_type": _illusion_type(
                    first.get("base_condition", ""),
                    first.get("illusion_type", ""),
                ),
                **{
                    key: metrics[key]
                    for key in BLOCK_SUMMARY_HEADER
                    if key in metrics
                },
            }
        )

    condition_rows: list[dict[str, Any]] = []
    for condition, group in by_condition.items():
        first = group[0]
        metrics = _summarize_group(group)
        condition_block_rows = [
            row for row in block_rows if row["condition"] == condition
        ]
        metrics["block_illusion_rate_sd"] = _population_sd(
            row.get("illusion_rate") for row in condition_block_rows
        )
        metrics["block_mean_confidence_sd"] = _population_sd(
            row.get("mean_confidence") for row in condition_block_rows
        )

        condition_rows.append(
            {
                "participant": participant,
                "design_mode": design_mode,
                "condition": condition,
                "base_condition": first.get("base_condition", ""),
                "soa_type": first.get("soa_type", ""),
                "soa_ms": first.get("soa_ms", ""),
                "illusion_type": _illusion_type(
                    first.get("base_condition", ""),
                    first.get("illusion_type", ""),
                ),
                **metrics,
            }
        )

    condition_rows.sort(
        key=lambda row: (
            {"fission": 0, "fusion": 1, "none": 2}.get(row["illusion_type"], 3),
            {"short": 0, "standard": 1, "none": 2}.get(row["soa_type"], 3),
            row["condition"],
        )
    )

    all_metrics = _summarize_group(rows)
    valid_rows = _valid_trials(rows)
    timing_metrics = {
        "n_trials_logged": len(rows),
        "n_trials_valid": len(valid_rows),
        "n_trial_errors": all_metrics["n_trial_errors"],
        "n_trials_with_dropped_frames": sum(
            (_number(row.get("dropped_frames_total")) or 0.0) > 0
            for row in valid_rows
        ),
        "dropped_frames_any_pct": all_metrics["dropped_frames_any_pct"],
        "dropped_frames_total": all_metrics["dropped_frames_total"],
        "dropped_fixation_total": sum(
            _number(row.get("dropped_fixation")) or 0.0 for row in valid_rows
        ),
        "dropped_stim1_total": sum(
            _number(row.get("dropped_stim1")) or 0.0 for row in valid_rows
        ),
        "dropped_isi_total": sum(
            _number(row.get("dropped_isi")) or 0.0 for row in valid_rows
        ),
        "dropped_stim2_total": sum(
            _number(row.get("dropped_stim2")) or 0.0 for row in valid_rows
        ),
        "dropped_poststim_total": sum(
            _number(row.get("dropped_poststim")) or 0.0 for row in valid_rows
        ),
        "mean_visual_soa_error_ms": all_metrics["mean_visual_soa_error_ms"],
        "max_abs_visual_soa_error_ms": all_metrics["max_abs_visual_soa_error_ms"],
        "mean_audio_scheduled_error_ms": all_metrics[
            "mean_audio_scheduled_error_ms"
        ],
        "max_abs_audio_scheduled_error_ms": all_metrics[
            "max_abs_audio_scheduled_error_ms"
        ],
        "mean_isi_error_ms": all_metrics["mean_isi_error_ms"],
        "max_abs_isi_error_ms": all_metrics["max_abs_isi_error_ms"],
    }

    return SessionSummary(
        condition_rows=condition_rows,
        block_rows=block_rows,
        timing_metrics=timing_metrics,
    )


def _write_rows(
    output_path: str | Path,
    header: list[str],
    rows: list[dict[str, Any]],
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    field: "" if row.get(field) is None else row.get(field, "")
                    for field in header
                }
            )


def save_session_summary(
    summary: SessionSummary,
    condition_summary_path: str | Path,
    block_summary_path: str | Path,
) -> None:
    """Save long-format condition and block summaries."""
    _write_rows(
        condition_summary_path,
        CONDITION_SUMMARY_HEADER,
        summary.condition_rows,
    )
    _write_rows(block_summary_path, BLOCK_SUMMARY_HEADER, summary.block_rows)


def _format_number(value: Any, digits: int = 2, suffix: str = "") -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.{digits}f}{suffix}"


def format_session_summary(
    summary: SessionSummary,
    display_metrics: Mapping[str, Any] | None = None,
) -> str:
    """Return a compact summary suitable for the experimenter console."""
    timing = summary.timing_metrics
    lines = [
        "",
        "SESSION SUMMARY",
        "=" * 72,
        (
            f"Valid trials: {timing['n_trials_valid']} / "
            f"{timing['n_trials_logged']} | Logged errors: "
            f"{timing['n_trial_errors']}"
        ),
        "",
        "ILLUSION CONDITIONS",
        (
            "Condition                         N    Rate    Conf. illusion  "
            "Conf. no illusion  Block SD"
        ),
    ]

    illusion_rows = [
        row for row in summary.condition_rows if row["illusion_type"] != "none"
    ]
    if not illusion_rows:
        lines.append("No fission or fusion condition in the selected design.")
    else:
        for row in illusion_rows:
            lines.append(
                f"{row['condition']:<32} "
                f"{row['n_trials_valid']:>3}  "
                f"{_format_number(row['illusion_rate'] * 100 if row['illusion_rate'] is not None else None, 1, '%'):>7}  "
                f"{_format_number(row['mean_confidence_illusion'], 1):>14}  "
                f"{_format_number(row['mean_confidence_no_illusion'], 1):>17}  "
                f"{_format_number(row['block_illusion_rate_sd'], 3):>8}"
            )

    display_metrics = display_metrics or {}
    lines.extend(["", "TIMING QUALITY"])

    frame_rate = _number(display_metrics.get("framerate"))
    frame_median_ms = _number(display_metrics.get("frame_median_ms"))
    frame_sd_ms = _number(display_metrics.get("frame_sd_ms"))
    if frame_rate is not None:
        lines.append(f"Measured refresh rate: {frame_rate:.3f} Hz")
    if frame_median_ms is not None:
        lines.append(
            "Frame duration, median / SD: "
            f"{frame_median_ms:.3f} ms / "
            f"{_format_number(frame_sd_ms, 3, ' ms')}"
        )

    lines.extend(
        [
            (
                "Trials with dropped frames: "
                f"{timing['n_trials_with_dropped_frames']} "
                f"({_format_number(timing['dropped_frames_any_pct'], 2, '%')})"
            ),
            f"Total estimated dropped frames: {timing['dropped_frames_total']:.0f}",
            (
                "Visual SOA error, mean / max absolute: "
                f"{_format_number(timing['mean_visual_soa_error_ms'], 3, ' ms')} / "
                f"{_format_number(timing['max_abs_visual_soa_error_ms'], 3, ' ms')}"
            ),
            (
                "Scheduled audio SOA error, mean / max absolute: "
                f"{_format_number(timing['mean_audio_scheduled_error_ms'], 3, ' ms')} / "
                f"{_format_number(timing['max_abs_audio_scheduled_error_ms'], 3, ' ms')}"
            ),
            (
                "Blank ISI error, mean / max absolute: "
                f"{_format_number(timing['mean_isi_error_ms'], 3, ' ms')} / "
                f"{_format_number(timing['max_abs_isi_error_ms'], 3, ' ms')}"
            ),
            "=" * 72,
        ]
    )
    return "\n".join(lines)
