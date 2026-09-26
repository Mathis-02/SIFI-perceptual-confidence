"""Photodiode and audio timing validation utility."""

from psychopy import prefs
prefs.hardware["audioLib"] = ["PTB"]
prefs.hardware["audioLatencyMode"] = 3

import csv
import os
import sys
from datetime import datetime

from psychopy import core, event, visual
from psychopy.hardware import keyboard

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.window import create_window
from core.timing import ms_to_frames
from core.stimuli import create_tone
from core.trial import _run_stimulus_sequence
from core.abort import ExperimentAbort

from config import (
    LAB_MODE,
    LAB_SCREEN_WIDTH_CM,
    LAB_VIEWING_DISTANCE_CM,
    FLASH_DURATION_MS,
    SOA_MS,
)


N_REPS = 20
ITI_S = 5.0
FIXATION_TEST_S = 0
TEST_CONDITIONS = ["A1V1_A2V2", "A1V1_A2"]

CENTER_FLASH_DIAMETER_DEG = 3.0

ENABLE_PHOTODIODE_PATCH = True
PHOTODIODE_PATCH_SIZE_DEG = 1.2
PHOTODIODE_PATCH_POS = (8.5, 5.0)   

CSV_FILENAME = "photodiode_test.csv"


def make_monitor():
    from psychopy import monitors

    mon = monitors.Monitor("photodiode_test_monitor")
    if LAB_MODE:
        mon.setWidth(LAB_SCREEN_WIDTH_CM)
        mon.setDistance(LAB_VIEWING_DISTANCE_CM)
        mon.setSizePix([1920, 1200])
    else:
        mon.setWidth(34.46)
        mon.setDistance(60.0)
        mon.setSizePix([1920, 1200])
    return mon


def make_center_flash(win, diameter_deg=3.0):
    return visual.Circle(
        win=win,
        radius=diameter_deg / 2.0,
        fillColor=[1, 1, 1],
        lineColor=[1, 1, 1],
        pos=(0, 0),
        units="deg"
    )


def make_photodiode_patch(win, size_deg=1.2, pos=(8.5, 5.0)):
    return visual.Rect(
        win=win,
        width=size_deg,
        height=size_deg,
        fillColor=[1, 1, 1],
        lineColor=[1, 1, 1],
        pos=pos,
        units="deg"
    )


def make_blank_fixation(win):
    return visual.TextStim(
        win=win,
        text="",
        color="white",
        height=1,
        units="deg"
    )


def main():
    mon = make_monitor()
    win, frame_rate, frame_period, timing_info = create_window(mon)
    kb = keyboard.Keyboard()

    fixation = make_blank_fixation(win)
    tone = create_tone()

    flash_center = make_center_flash(win, diameter_deg=CENTER_FLASH_DIAMETER_DEG)

    photodiode_patch = None
    if ENABLE_PHOTODIODE_PATCH:
        photodiode_patch = make_photodiode_patch(
            win,
            size_deg=PHOTODIODE_PATCH_SIZE_DEG,
            pos=PHOTODIODE_PATCH_POS
        )

    flash_frames = ms_to_frames(FLASH_DURATION_MS, frame_period)
    isi_ms = SOA_MS - FLASH_DURATION_MS
    isi_frames = ms_to_frames(isi_ms, frame_period)

    if isi_frames < 0:
        raise ValueError(
            f"Computed isi_frames is negative ({isi_frames}). "
            f"Check SOA_MS ({SOA_MS}) and FLASH_DURATION_MS ({FLASH_DURATION_MS})."
        )

    intro = visual.TextStim(
        win,
        text=(
            "ESPACE = démarrer\n"
        ),
        color="white",
        height=0.8,
        wrapWidth=24
    )
    intro.draw()
    win.flip()

    keys = event.waitKeys(keyList=["space", "escape"])
    if "escape" in keys:
        win.close()
        core.quit()

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_FILENAME)

    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "trial_index",
            "condition",
            "frame_rate_hz",
            "frame_period_s",
            "flash_duration_ms_requested",
            "soa_ms_requested",
            "flash_frames",
            "isi_frames",
            "fixation_duration_requested_s",
            "fixation_programmed_s",
            "fixation_measured_s",
            "flash1_onset_time",
            "flash1_offset_time",
            "flash2_onset_time",
            "flash2_offset_time",
            "isi_blank_start_time",
            "isi_blank_end_time",
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
            "lab_mode",
            "screen_width_cm",
            "viewing_distance_cm",
            "photodiode_patch_enabled",
            "photodiode_patch_size_deg",
            "photodiode_patch_pos_x_deg",
            "photodiode_patch_pos_y_deg",
            "center_flash_diameter_deg",
            "fixation_visible",
        ])

        trial_index = 0

        try:
            for rep in range(N_REPS):
                for condition in TEST_CONDITIONS:
                    stim_data = _run_stimulus_sequence(
                        win=win,
                        fixation=fixation,
                        tone=tone,
                        flash_upper=flash_center,
                        flash_lower=flash_center,
                        flash_frames=flash_frames,
                        isi_frames=isi_frames,
                        frame_period=frame_period,
                        condition=condition,
                        position="upper",
                        fixation_duration_requested_s=FIXATION_TEST_S,
                        photodiode_patch=photodiode_patch,
                    )

                    writer.writerow([
                        datetime.now().isoformat(timespec="milliseconds"),
                        trial_index,
                        condition,
                        frame_rate,
                        frame_period,
                        FLASH_DURATION_MS,
                        SOA_MS,
                        flash_frames,
                        isi_frames,
                        FIXATION_TEST_S,
                        stim_data["fixation_programmed_s"],
                        stim_data["fixation_measured_s"],
                        stim_data["flash1_onset_time"],
                        stim_data["flash1_offset_time"],
                        stim_data["flash2_onset_time"],
                        stim_data["flash2_offset_time"],
                        stim_data["isi_blank_start_time"],
                        stim_data["isi_blank_end_time"],
                        stim_data["beep1_scheduled_ptb_time"],
                        stim_data["beep1_flip_proxy_time"],
                        stim_data["beep2_scheduled_ptb_time"],
                        stim_data["beep2_flip_proxy_time"],
                        stim_data["soa_visual_programmed_s"],
                        stim_data["soa_visual_flip_measured_s"],
                        stim_data["soa_audio_programmed_s"],
                        stim_data["soa_audio_scheduled_s"],
                        stim_data["soa_audio_flip_proxy_s"],
                        stim_data["isi_blank_programmed_s"],
                        stim_data["isi_blank_measured_s"],
                        stim_data["dropped_fixation"],
                        stim_data["dropped_stim1"],
                        stim_data["dropped_isi"],
                        stim_data["dropped_stim2"],
                        stim_data["dropped_poststim"],
                        stim_data["dropped_frames_total"],
                        int(bool(LAB_MODE)),
                        LAB_SCREEN_WIDTH_CM if LAB_MODE else 34.46,
                        LAB_VIEWING_DISTANCE_CM if LAB_MODE else 60.0,
                        int(bool(ENABLE_PHOTODIODE_PATCH)),
                        PHOTODIODE_PATCH_SIZE_DEG if ENABLE_PHOTODIODE_PATCH else "",
                        PHOTODIODE_PATCH_POS[0] if ENABLE_PHOTODIODE_PATCH else "",
                        PHOTODIODE_PATCH_POS[1] if ENABLE_PHOTODIODE_PATCH else "",
                        CENTER_FLASH_DIAMETER_DEG,
                        0,
                    ])
                    f.flush()

                    iti_clock = core.Clock()
                    while iti_clock.getTime() < ITI_S:
                        if "escape" in event.getKeys(keyList=["escape"]):
                            raise ExperimentAbort("User aborted (escape)")
                        win.flip()

                    trial_index += 1

        except ExperimentAbort:
            pass

    end_text = visual.TextStim(
        win,
        text=(
            "Fin.\n\n"
            "ESPACE pour quitter."
        ),
        color="white",
        height=0.8,
        wrapWidth=24
    )
    end_text.draw()
    win.flip()
    event.waitKeys(keyList=["space", "escape"])

    win.close()
    core.quit()


if __name__ == "__main__":
    main()
