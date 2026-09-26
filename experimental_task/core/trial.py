"""Single-trial presentation, response collection, and timing measurements."""

import random
import numpy as np
from psychopy import core, event
from config import (
    FIXATION_MIN,
    FIXATION_MAX,
    POST_STIM_BLANK_MS,
    KEEP_FIXATION_DURING_STIM,
    CONFIDENCE_MODE,
    CONF_MIN,
    CONF_MAX,
)

from core.abort import check_abort, ExperimentAbort


def _count_dropped(intervals, frame_period):
    return int(sum(max(0, int(round(f / frame_period)) - 1) for f in intervals))


def _run_blank_interval(win, frames):
    first_flip_time = np.nan
    last_flip_time = np.nan

    for i in range(frames):
        check_abort()
        t = win.flip()
        if i == 0:
            first_flip_time = t
        last_flip_time = t

    return first_flip_time, last_flip_time


def _slice_new_intervals(win, start_idx):
    end_idx = len(win.frameIntervals)
    return win.frameIntervals[start_idx:end_idx], end_idx


def _clamp(value, low, high):
    return max(low, min(high, value))


def _value_to_bar_x(value, bar_left_x, bar_right_x, conf_min, conf_max):
    frac = (value - conf_min) / float(conf_max - conf_min)
    return bar_left_x + frac * (bar_right_x - bar_left_x)


def _bar_x_to_value(x, bar_left_x, bar_right_x, conf_min, conf_max):
    frac = (x - bar_left_x) / float(bar_right_x - bar_left_x)
    value = conf_min + frac * (conf_max - conf_min)
    return int(round(value))


def _get_discrete_confidence(win, confidence_text, kb):
    kb.clearEvents()
    kb.clock.reset()

    confidence_text.draw()
    win.flip()

    while True:
        check_abort()

        these_keys = kb.getKeys(waitRelease=False)

        for key in these_keys:
            name = key.name.lower()

            if name == "escape":
                raise ExperimentAbort("User aborted (escape) during confidence")

            if name in ["1", "&"]:
                return 1.0, key.rt
            elif name in ["2", "é"]:
                return 2.0, key.rt
            elif name in ["3", '"']:
                return 3.0, key.rt
            elif name in ["4", "'"]:
                return 4.0, key.rt


def _get_continuous_confidence(win, confidence_widget):
    instruction = confidence_widget["instruction"]
    bar = confidence_widget["bar"]
    active_bar = confidence_widget["active_bar"]
    marker = confidence_widget["marker"]
    tick_labels = confidence_widget["tick_labels"]
    qual_labels = confidence_widget["qual_labels"]
    value_text = confidence_widget["value_text"]

    bar_left_x = confidence_widget["bar_left_x"]
    bar_right_x = confidence_widget["bar_right_x"]
    bar_y = confidence_widget["bar_y"]
    hover_half_height = confidence_widget["hover_half_height"]

    win.mouseVisible = True
    mouse = event.Mouse(win=win)
    start_x = random.uniform(bar_left_x + 0.8, bar_right_x - 0.8)
    mouse.setPos((start_x, bar_y - 0.8))
    mouse.clickReset()
    event.clearEvents()

    current_value = None
    prev_left_pressed = False

    clock_conf = core.Clock()
    clock_conf.reset()

    try:
        while True:
            check_abort()

            mouse_x, mouse_y = mouse.getPos()

            over_bar = (
                bar_left_x <= mouse_x <= bar_right_x
                and (bar_y - hover_half_height) <= mouse_y <= (bar_y + hover_half_height)
            )

            if over_bar:
                clamped_x = _clamp(mouse_x, bar_left_x, bar_right_x)
                current_value = _bar_x_to_value(
                    clamped_x,
                    bar_left_x,
                    bar_right_x,
                    CONF_MIN,
                    CONF_MAX
                )

                marker_x = _value_to_bar_x(
                    current_value,
                    bar_left_x,
                    bar_right_x,
                    CONF_MIN,
                    CONF_MAX
                )

                marker.pos = (marker_x, bar_y)
                active_bar.end = (marker_x, bar_y)
                value_text.text = f"{current_value}%"
            else:
                current_value = None
                value_text.text = ""

            instruction.draw()
            bar.draw()

            if over_bar:
                active_bar.draw()
                marker.draw()

            for tick in tick_labels:
                tick.draw()

            for qual_label in qual_labels:
                qual_label.draw()

            if over_bar:
                value_text.draw()

            win.flip()

            keys = event.getKeys(keyList=["escape"])
            if "escape" in keys:
                raise ExperimentAbort("User aborted (escape) during confidence")

            left_pressed = mouse.getPressed()[0]

            if over_bar and current_value is not None and left_pressed and not prev_left_pressed:
                rt_conf = clock_conf.getTime()
                return float(current_value), rt_conf

            prev_left_pressed = left_pressed

    finally:
        win.mouseVisible = False


def _run_stimulus_sequence(
    win,
    fixation,
    tone,
    flash_upper,
    flash_lower,
    flash_frames,
    isi_frames,
    frame_period,
    condition,
    position,
    fixation_duration_requested_s=None,
    photodiode_patch=None,
):
    if fixation_duration_requested_s is None:
        fixation_duration_requested_s = random.uniform(FIXATION_MIN, FIXATION_MAX)

    fix_frames = int(round(fixation_duration_requested_s / frame_period))

    win.frameIntervals = []
    win.recordFrameIntervals = True

    fixation_onset_time = np.nan
    first_event_onset_time = np.nan

    flash1_onset_time = np.nan
    flash1_offset_time = np.nan
    flash2_onset_time = np.nan
    flash2_offset_time = np.nan

    isi_blank_start_time = np.nan
    isi_blank_end_time = np.nan

    beep1_scheduled_ptb_time = np.nan
    beep1_flip_proxy_time = np.nan
    beep2_scheduled_ptb_time = np.nan
    beep2_flip_proxy_time = np.nan

    idx0 = 0

    has_beep1 = condition in [
        "A1V1",
        "A1V1_A2",
        "A1V1_V2",
        "A1V1_A2V2",
    ]

    has_second_event = condition in [
        "V1V2",
        "A1V1_A2",
        "A1V1_V2",
        "A1V1_A2V2",
    ]

    second_event_is_flash = condition in [
        "V1V2",
        "A1V1_V2",
        "A1V1_A2V2",
    ]

    second_event_is_beep_only = condition == "A1V1_A2"

    for i in range(fix_frames):
        check_abort()
        fixation.draw()
        t = win.flip()
        if i == 0:
            fixation_onset_time = t

    fix_intervals, idx1 = _slice_new_intervals(win, idx0)

    if KEEP_FIXATION_DURING_STIM:
        fixation.setAutoDraw(True)

    flash = flash_upper if position == "upper" else flash_lower

    for i in range(flash_frames):
        check_abort()

        if has_beep1 and i == 0:
            beep1_scheduled_ptb_time = win.getFutureFlipTime(clock="ptb")
            tone.play(when=beep1_scheduled_ptb_time)

        flash.draw()
        if photodiode_patch is not None:
            photodiode_patch.draw()

        t = win.flip()

        if i == 0:
            flash1_onset_time = t
            first_event_onset_time = t
            if has_beep1:
                beep1_flip_proxy_time = t

    stim1_intervals, idx2 = _slice_new_intervals(win, idx1)

    if has_second_event:
        isi_blank_start_time, isi_blank_end_time = _run_blank_interval(win, isi_frames)
        if not np.isnan(isi_blank_start_time):
            flash1_offset_time = isi_blank_start_time

    isi_intervals, idx3 = _slice_new_intervals(win, idx2)

    if condition in ["V1", "A1V1"]:
        pass

    elif condition == "V1V2":
        for i in range(flash_frames):
            check_abort()

            flash.draw()
            if photodiode_patch is not None:
                photodiode_patch.draw()

            t = win.flip()
            if i == 0:
                flash2_onset_time = t

    elif condition == "A1V1_V2":
        for i in range(flash_frames):
            check_abort()

            flash.draw()
            if photodiode_patch is not None:
                photodiode_patch.draw()

            t = win.flip()
            if i == 0:
                flash2_onset_time = t

    elif second_event_is_beep_only:
        check_abort()

        beep2_scheduled_ptb_time = win.getFutureFlipTime(clock="ptb")
        tone.play(when=beep2_scheduled_ptb_time)
        beep2_flip_proxy_time = win.flip()

    elif condition == "A1V1_A2V2":
        for i in range(flash_frames):
            check_abort()

            if i == 0:
                beep2_scheduled_ptb_time = win.getFutureFlipTime(clock="ptb")
                tone.play(when=beep2_scheduled_ptb_time)

            flash.draw()
            if photodiode_patch is not None:
                photodiode_patch.draw()

            t = win.flip()
            if i == 0:
                flash2_onset_time = t
                beep2_flip_proxy_time = t

    else:
        raise ValueError(f"Unknown condition: {condition}")

    stim2_intervals, idx4 = _slice_new_intervals(win, idx3)

    blank_frames = int(round((POST_STIM_BLANK_MS / 1000.0) / frame_period))
    post_blank_start_time, post_blank_end_time = _run_blank_interval(win, blank_frames)

    poststim_intervals, idx5 = _slice_new_intervals(win, idx4)

    if condition in ["V1", "A1V1"]:
        if not np.isnan(post_blank_start_time):
            flash1_offset_time = post_blank_start_time

    elif condition in ["V1V2", "A1V1_V2", "A1V1_A2V2"]:
        if not np.isnan(post_blank_start_time):
            flash2_offset_time = post_blank_start_time

    elif condition == "A1V1_A2":
        pass

    if KEEP_FIXATION_DURING_STIM:
        fixation.setAutoDraw(False)

    win.recordFrameIntervals = False

    fixation_programmed_s = fix_frames * frame_period
    fixation_measured_s = (
        first_event_onset_time - fixation_onset_time
        if not np.isnan(first_event_onset_time) and not np.isnan(fixation_onset_time)
        else np.nan
    )

    soa_visual_programmed_s = np.nan
    if second_event_is_flash:
        soa_visual_programmed_s = (flash_frames + isi_frames) * frame_period

    soa_visual_flip_measured_s = (
        flash2_onset_time - flash1_onset_time
        if not np.isnan(flash2_onset_time) and not np.isnan(flash1_onset_time)
        else np.nan
    )

    soa_audio_programmed_s = np.nan
    if has_beep1:
        soa_audio_programmed_s = (flash_frames + isi_frames) * frame_period

    soa_audio_scheduled_s = (
        beep2_scheduled_ptb_time - beep1_scheduled_ptb_time
        if not np.isnan(beep2_scheduled_ptb_time) and not np.isnan(beep1_scheduled_ptb_time)
        else np.nan
    )

    soa_audio_flip_proxy_s = (
        beep2_flip_proxy_time - beep1_flip_proxy_time
        if not np.isnan(beep2_flip_proxy_time) and not np.isnan(beep1_flip_proxy_time)
        else np.nan
    )

    isi_blank_programmed_s = np.nan
    isi_blank_measured_s = np.nan

    if has_second_event:
        isi_blank_programmed_s = isi_frames * frame_period

        second_event_time = np.nan
        if condition == "V1V2":
            second_event_time = flash2_onset_time
        elif condition == "A1V1_A2":
            second_event_time = beep2_flip_proxy_time
        elif condition == "A1V1_V2":
            second_event_time = flash2_onset_time
        elif condition == "A1V1_A2V2":
            second_event_time = flash2_onset_time

        if not np.isnan(isi_blank_start_time) and not np.isnan(second_event_time):
            isi_blank_measured_s = second_event_time - isi_blank_start_time

    dropped_fixation = _count_dropped(fix_intervals, frame_period)
    dropped_stim1 = _count_dropped(stim1_intervals, frame_period)
    dropped_isi = _count_dropped(isi_intervals, frame_period)
    dropped_stim2 = _count_dropped(stim2_intervals, frame_period)
    dropped_poststim = _count_dropped(poststim_intervals, frame_period)
    dropped_frames_total = (
        dropped_fixation
        + dropped_stim1
        + dropped_isi
        + dropped_stim2
        + dropped_poststim
    )

    win.frameIntervals = []

    return {
        "fixation_programmed_s": fixation_programmed_s,
        "fixation_measured_s": fixation_measured_s,
        "flash_frames": flash_frames,
        "isi_frames": isi_frames,
        "flash1_onset_time": flash1_onset_time,
        "flash1_offset_time": flash1_offset_time,
        "isi_blank_start_time": isi_blank_start_time,
        "isi_blank_end_time": isi_blank_end_time,
        "flash2_onset_time": flash2_onset_time,
        "flash2_offset_time": flash2_offset_time,
        "beep1_scheduled_ptb_time": beep1_scheduled_ptb_time,
        "beep1_flip_proxy_time": beep1_flip_proxy_time,
        "beep2_scheduled_ptb_time": beep2_scheduled_ptb_time,
        "beep2_flip_proxy_time": beep2_flip_proxy_time,
        "soa_visual_programmed_s": soa_visual_programmed_s,
        "soa_visual_flip_measured_s": soa_visual_flip_measured_s,
        "soa_audio_programmed_s": soa_audio_programmed_s,
        "soa_audio_scheduled_s": soa_audio_scheduled_s,
        "soa_audio_flip_proxy_s": soa_audio_flip_proxy_s,
        "isi_blank_programmed_s": isi_blank_programmed_s,
        "isi_blank_measured_s": isi_blank_measured_s,
        "dropped_fixation": dropped_fixation,
        "dropped_stim1": dropped_stim1,
        "dropped_isi": dropped_isi,
        "dropped_stim2": dropped_stim2,
        "dropped_poststim": dropped_poststim,
        "dropped_frames_total": dropped_frames_total,
    }


def run_trial(
    win,
    kb,
    fixation,
    tone,
    flash_upper,
    flash_lower,
    response_text,
    confidence_text,
    flash_frames,
    isi_frames,
    frame_period,
    condition,
    position,
    ask_confidence=True
):
    trial_clock = core.Clock()

    stim_data = _run_stimulus_sequence(
        win=win,
        fixation=fixation,
        tone=tone,
        flash_upper=flash_upper,
        flash_lower=flash_lower,
        flash_frames=flash_frames,
        isi_frames=isi_frames,
        frame_period=frame_period,
        condition=condition,
        position=position,
    )

    kb.clearEvents()
    kb.clock.reset()

    response_text.draw()
    win.flip()

    while True:
        check_abort()

        these_keys = kb.getKeys(waitRelease=False)

        for key in these_keys:
            name = key.name.lower()

            if name == "escape":
                raise ExperimentAbort("User aborted (escape) during response")

            if name in ["1", "&"]:
                response = "1"
                rt = key.rt
                break
            elif name in ["2", "é"]:
                response = "2"
                rt = key.rt
                break
        else:
            continue

        break
    
    if ask_confidence:
        if CONFIDENCE_MODE == "discrete":
            confidence, rt_conf = _get_discrete_confidence(win, confidence_text, kb)
        elif CONFIDENCE_MODE == "continuous":
            confidence, rt_conf = _get_continuous_confidence(win, confidence_text)
        else:
            raise ValueError(f"Unknown CONFIDENCE_MODE: {CONFIDENCE_MODE}")
    else:
        confidence = np.nan
        rt_conf = np.nan
    
    trial_total_s = trial_clock.getTime()

    return {
        "response": response,
        "rt": rt,
        "confidence": confidence,
        "rt_conf": rt_conf,
        "trial_total_s": trial_total_s,
        **stim_data,
    }
