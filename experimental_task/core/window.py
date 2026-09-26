"""PsychoPy window creation and refresh-rate measurement."""

from psychopy import visual


def create_window(monitor):
    """Create the full-screen experiment window and measure frame duration."""
    window = visual.Window(
        fullscr=True,
        monitor=monitor,
        units="deg",
        waitBlanking=True,
        color="black",
        allowGUI=False,
        checkTiming=False,
        infoMsg="",
        winType="pyglet",
    )

    # Warm-up flips reduce the influence of window creation on the timing sample.
    window.mouseVisible = False
    for _ in range(120):
        window.flip()

    mean_ms, sd_ms, median_ms = window.getMsPerFrame(
        nFrames=120,
        showVisual=False,
        msg="",
    )

    # All frame-based timing uses this single measured period.
    if median_ms is None or median_ms <= 0:
        frame_period = 1.0 / 60.0
        frame_rate = 60.0
    else:
        frame_period = float(median_ms) / 1000.0
        frame_rate = 1.0 / frame_period

    timing_info = {
        "mean_ms": mean_ms,
        "sd_ms": sd_ms,
        "median_ms": median_ms,
        "frame_period_s": frame_period,
        "frame_rate_hz": frame_rate,
    }
    return window, frame_rate, frame_period, timing_info


def create_fixation(window):
    """Create the central fixation cross."""
    return visual.TextStim(
        win=window,
        text="+",
        height=1,
        color="white",
    )
