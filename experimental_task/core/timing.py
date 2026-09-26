"""Timing conversion helpers."""


def ms_to_frames(duration_ms: float, frame_period_s: float) -> int:
    """Convert a duration in milliseconds to the nearest whole frame count.

    The conversion intentionally uses Python's standard rounding behavior to
    preserve the timing choices used in the original task.
    """
    if frame_period_s <= 0:
        raise ValueError("frame_period_s must be greater than zero.")

    duration_s = float(duration_ms) / 1000.0
    return int(round(duration_s / float(frame_period_s)))
