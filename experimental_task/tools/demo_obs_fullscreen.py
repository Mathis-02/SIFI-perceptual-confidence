"""Full-screen demonstration of the four audiovisual conditions."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from psychopy import prefs

# Audio preferences must be configured before importing PsychoPy sound modules.
prefs.hardware["audioLib"] = ["PTB"]
prefs.hardware["audioLatencyMode"] = 3

from psychopy import core, event, monitors, visual

from config import (
    FLASH_DURATION_MS,
    LAB_SCREEN_WIDTH_CM,
    LAB_VIEWING_DISTANCE_CM,
)
from core.stimuli import create_flash, create_tone
from core.timing import ms_to_frames
from core.window import create_fixation, create_window


# ============================================================
# Demonstration settings
# ============================================================

SOA_MS = 83

# Delay between the end of one condition and the start of the next.
INTER_CONDITION_S = 8.0

# Fixation after Space is pressed and before the first condition.
PRE_FIRST_CONDITION_S = 1.0

# Fixation after the last condition.
FINAL_FIXATION_S = 2.0

# Presentation order.
CONDITIONS = [
    "A1V1",
    "A1V1_A2",
    "A1V1_A2V2",
    "A1V1_V2",
]


def check_escape():
    """Stop the demonstration when Escape is pressed."""
    keys = event.getKeys(keyList=["escape"])
    if "escape" in keys:
        raise KeyboardInterrupt


def show_fixation_frames(win, fixation, n_frames):
    """Show the fixation cross for an exact number of frames."""
    for _ in range(max(0, int(n_frames))):
        check_escape()
        fixation.draw()
        win.flip()


def show_fixation_seconds(win, fixation, duration_s, frame_period):
    """Show fixation for an approximately specified duration."""
    n_frames = max(1, int(round(duration_s / frame_period)))
    show_fixation_frames(win, fixation, n_frames)


def present_first_av_event(
    win,
    fixation,
    flash,
    tone,
    flash_frames,
):
    """Present A1V1 with sound scheduled on the first flash frame."""
    for frame_index in range(flash_frames):
        check_escape()

        if frame_index == 0:
            beep_time = win.getFutureFlipTime(clock="ptb")
            tone.play(when=beep_time)

        fixation.draw()
        flash.draw()
        win.flip()


def present_second_beep(
    win,
    fixation,
    tone,
):
    """Present A2 alone."""
    check_escape()

    beep_time = win.getFutureFlipTime(clock="ptb")
    tone.play(when=beep_time)

    fixation.draw()
    win.flip()


def present_second_flash(
    win,
    fixation,
    flash,
    flash_frames,
    tone=None,
):
    """Present V2 alone, or A2V2 when a tone is provided."""
    for frame_index in range(flash_frames):
        check_escape()

        if tone is not None and frame_index == 0:
            beep_time = win.getFutureFlipTime(clock="ptb")
            tone.play(when=beep_time)

        fixation.draw()
        flash.draw()
        win.flip()


def present_condition(
    win,
    fixation,
    flash,
    tone,
    condition,
    flash_frames,
    isi_frames,
):
    """Present one condition without collecting a response."""
    valid_conditions = {
        "A1V1",
        "A1V1_A2",
        "A1V1_A2V2",
        "A1V1_V2",
    }

    if condition not in valid_conditions:
        raise ValueError(f"Unknown condition : {condition}")

    # The A1V1 event is shared by all four conditions.
    present_first_av_event(
        win=win,
        fixation=fixation,
        flash=flash,
        tone=tone,
        flash_frames=flash_frames,
    )

    # A1V1 has no second event.
    if condition == "A1V1":
        return

    # Blank interval between the first flash and the second event.
    show_fixation_frames(
        win=win,
        fixation=fixation,
        n_frames=isi_frames,
    )

    if condition == "A1V1_A2":
        present_second_beep(
            win=win,
            fixation=fixation,
            tone=tone,
        )

    elif condition == "A1V1_A2V2":
        present_second_flash(
            win=win,
            fixation=fixation,
            flash=flash,
            flash_frames=flash_frames,
            tone=tone,
        )

    elif condition == "A1V1_V2":
        present_second_flash(
            win=win,
            fixation=fixation,
            flash=flash,
            flash_frames=flash_frames,
            tone=None,
        )


def main():
    # Match the monitor definition used by the laboratory experiment.
    monitor = monitors.Monitor("lab_thinkpad_monitor")
    monitor.setWidth(LAB_SCREEN_WIDTH_CM)
    monitor.setDistance(LAB_VIEWING_DISTANCE_CM)
    monitor.setSizePix([1920, 1200])

    # Reuse the experiment window and refresh-rate measurement.
    win, frame_rate, frame_period, timing_info = create_window(monitor)

    tone = None

    try:
        win.mouseVisible = False

        fixation = create_fixation(win)
        flash_upper = create_flash(win, position="upper")
        flash_lower = create_flash(win, position="lower")
        tone = create_tone()

        flash_frames = max(
            1,
            ms_to_frames(FLASH_DURATION_MS, frame_period),
        )

        isi_ms = SOA_MS - FLASH_DURATION_MS
        isi_frames = ms_to_frames(isi_ms, frame_period)

        if isi_frames < 0:
            raise ValueError(
                f"ISI négatif : {isi_frames} frames. "
                f"SOA_MS={SOA_MS}, FLASH_DURATION_MS={FLASH_DURATION_MS}."
            )

        programmed_soa_ms = (
            flash_frames + isi_frames
        ) * frame_period * 1000.0

        print("--- Démonstration OBS plein écran ---")
        print(f"Fréquence mesurée : {frame_rate:.3f} Hz")
        print(f"Durée du flash : {flash_frames} frame(s)")
        print(f"ISI : {isi_frames} frame(s)")
        print(f"SOA demandé : {SOA_MS} ms")
        print(f"SOA programmé : {programmed_soa_ms:.3f} ms")

        start_text = visual.TextStim(
            win,
            text=(
                "Appuyez sur ESPACE pour lancer la démonstration.\n\n"
                "ÉCHAP permet de quitter."
            ),
            color="white",
            units="pix",
            height=32,
            wrapWidth=win.size[0] * 0.65,
            alignText="center",
        )

        start_text.draw()
        win.flip()

        event.clearEvents()
        keys = event.waitKeys(keyList=["space", "escape"])

        if "escape" in keys:
            return

        event.clearEvents()

        # Fixation before the first condition.
        show_fixation_seconds(
            win=win,
            fixation=fixation,
            duration_s=PRE_FIRST_CONDITION_S,
            frame_period=frame_period,
        )

        for condition_index, condition in enumerate(CONDITIONS):
            # Alternate flash position across successive conditions.
            flash = (
                flash_upper
                if condition_index % 2 == 0
                else flash_lower
            )

            present_condition(
                win=win,
                fixation=fixation,
                flash=flash,
                tone=tone,
                condition=condition,
                flash_frames=flash_frames,
                isi_frames=isi_frames,
            )

            # Maintient uniquement la croix pendant huit secondes.
            if condition_index < len(CONDITIONS) - 1:
                show_fixation_seconds(
                    win=win,
                    fixation=fixation,
                    duration_s=INTER_CONDITION_S,
                    frame_period=frame_period,
                )

        show_fixation_seconds(
            win=win,
            fixation=fixation,
            duration_s=FINAL_FIXATION_S,
            frame_period=frame_period,
        )

    except KeyboardInterrupt:
        print("Démonstration interrompue avec Échap.")

    finally:
        if tone is not None:
            try:
                tone.stop()
            except Exception:
                pass

        try:
            win.close()
        except Exception:
            pass

        core.quit()


if __name__ == "__main__":
    main()
