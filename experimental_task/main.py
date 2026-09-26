"""Run the SIFI acquisition task and write session-level quality-control files."""

from psychopy import prefs
prefs.hardware['audioLib'] = ['PTB']
prefs.hardware['audioLatencyMode'] = 3

import os
import random
import time
from datetime import datetime

import numpy as np
from psychopy.hardware import keyboard
from psychopy import core, gui, visual, event

from core.window import create_window, create_fixation
from core.timing import ms_to_frames
from core.stimuli import create_flash, create_tone
from core.trial import run_trial
from core.experiment import generate_blocks
from core.calibration import (
    run_screen_size_calibration,
    build_monitor_from_calibration,
    run_blindspot_distance_calibration,
)
from core.start_phase import (
    run_audio_calibration,
    run_visual_display_check,
    show_instructions,
    run_practice,
)
from core.trial_logger import TrialLogger
from core.session_io import sanitize_participant_id, write_session_csv
from core.session_summary import (
    build_session_summary,
    format_session_summary,
    save_session_summary,
)
from core.abort import ExperimentAbort

from config import (
    DEBUG_MODE,
    PILOT_MODE,
    FLASH_DURATION_MS,
    SOA_MS,
    SHORT_SOA_MS,
    RNG_SEED,
    CODE_VERSION,
    CONFIDENCE_MODE,
    CONF_MIN,
    CONF_MAX,
    LAB_MODE,
    LAB_VIEWING_DISTANCE_CM,
    LAB_SCREEN_WIDTH_CM,
    DESIGN_MODE,
    TRIALS_PER_BLOCK,
    TRIALS_TOTAL,
    N_BLOCKS,
)


def _safe_close_window(window):
    """Close a PsychoPy window without masking the original exception."""
    try:
        if window is not None:
            window.close()
    except Exception:
        pass
    return None


def main():
    exp_info = {"Participant ID": ""}
    dlg = gui.DlgFromDict(exp_info, title="SIFI Experiment")
    if not dlg.OK:
        core.quit()

    try:
        participant_id = sanitize_participant_id(exp_info["Participant ID"])
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    trial_dir = os.path.join(data_dir, "trials")
    session_dir = os.path.join(data_dir, "session_info")

    os.makedirs(trial_dir, exist_ok=True)
    os.makedirs(session_dir, exist_ok=True)

    trials_path = os.path.join(trial_dir, f"{participant_id}_trials.csv")
    session_path = os.path.join(session_dir, f"{participant_id}_session.csv")
    condition_summary_path = os.path.join(
        session_dir, f"{participant_id}_condition_summary.csv"
    )
    block_summary_path = os.path.join(
        session_dir, f"{participant_id}_block_summary.csv"
    )

    if os.path.exists(trials_path):
        raise RuntimeError(
            f"File already exists for participant '{participant_id}'. "
            "Choose a different participant ID."
        )

    if RNG_SEED is None:
        seed_used = int(time.time() * 1000) % (2**32)
    else:
        seed_used = RNG_SEED

    random.seed(seed_used)
    np.random.seed(seed_used)

    win = None
    setup_win = None
    blindspot_win = None
    logger = None
    session_summary = None
    abort_reason = ""
    completed = 0

    session_values = {
        "participant": participant_id,
        "date_start": "",
        "date_end": "",
        "completed": 0,
        "abort_reason": "",
        "rng_seed": seed_used,
        "code_version": CODE_VERSION,
        "design_mode": DESIGN_MODE,
        "n_blocks": N_BLOCKS,
        "trials_per_block": TRIALS_PER_BLOCK,
        "trials_total": TRIALS_TOTAL,
        "standard_soa_ms": SOA_MS,
        "short_soa_ms": SHORT_SOA_MS,
        "debug_mode": int(bool(DEBUG_MODE)),
        "pilot_mode": int(bool(PILOT_MODE)),
        "lab_mode": int(bool(LAB_MODE)),
        "confidence_mode": CONFIDENCE_MODE,
    }

    try:
        if DEBUG_MODE:
            from psychopy import monitors
            mon = monitors.Monitor("testMonitor")
            mon.setWidth(53)
            mon.setDistance(60)
            mon.setSizePix([1920, 1080])

            calibration = {
                "screen_width_cm": 53,
                "pixels_per_cm": 1920 / 53,
                "resolution": [1920, 1080],
                "viewing_distance_cm": 60,
                "viewing_distance_method": "debug_fixed",
                "viewing_distance_n_valid": np.nan,
                "viewing_distance_iqr_cm": np.nan,
                "viewing_distance_notes": ""
            }

        elif LAB_MODE:
            from psychopy import monitors

            provisional_resolution = [1920, 1200]

            mon = monitors.Monitor("lab_thinkpad_monitor")
            mon.setWidth(LAB_SCREEN_WIDTH_CM)
            mon.setDistance(LAB_VIEWING_DISTANCE_CM)
            mon.setSizePix(provisional_resolution)

            calibration = {
                "screen_width_cm": LAB_SCREEN_WIDTH_CM,
                "pixels_per_cm": provisional_resolution[0] / LAB_SCREEN_WIDTH_CM,
                "resolution": provisional_resolution,
                "viewing_distance_cm": LAB_VIEWING_DISTANCE_CM,
                "viewing_distance_method": "lab_fixed",
                "viewing_distance_n_valid": np.nan,
                "viewing_distance_iqr_cm": np.nan,
                "viewing_distance_notes": "ThinkPad 21QV fixed lab setup"
            }

        else:
            calibration = run_screen_size_calibration()

            setup_mon = build_monitor_from_calibration(
                calibration,
                monitor_name="setup_monitor",
                default_distance_cm=60.0
            )

            setup_win = visual.Window(
                fullscr=False,
                size=(1200, 800),
                monitor=setup_mon,
                units="pix",
                color="black",
                allowGUI=True,
                checkTiming=False,
                infoMsg="",
                waitBlanking=True
            )
            setup_win.mouseVisible = True

            setup_tone = create_tone()
            run_audio_calibration(setup_win, setup_tone)
            run_visual_display_check(setup_win)

            try:
                setup_tone.stop()
            except Exception:
                pass
            del setup_tone

            setup_win = _safe_close_window(setup_win)
            core.wait(0.3)

            mon_provisional = build_monitor_from_calibration(
                calibration,
                monitor_name="provisional_monitor",
                default_distance_cm=60.0
            )

            blindspot_win, _, _, _ = create_window(mon_provisional)

            calibration = run_blindspot_distance_calibration(
                blindspot_win,
                calibration,
                n_trials=5,
                retry_trials=3
            )

            blindspot_win = _safe_close_window(blindspot_win)
            core.wait(0.3)

            mon = build_monitor_from_calibration(
                calibration,
                monitor_name="calibrated_monitor",
                default_distance_cm=60.0
            )

        win, frame_rate, frame_period, timing_info = create_window(mon)
        if LAB_MODE:
            actual_resolution = [int(win.size[0]), int(win.size[1])]
            calibration["resolution"] = actual_resolution
            calibration["pixels_per_cm"] = actual_resolution[0] / calibration["screen_width_cm"]

            mon.setSizePix(actual_resolution)

        kb = keyboard.Keyboard()

        fixation = create_fixation(win)
        tone = create_tone()
        flash_upper = create_flash(win, position="upper")
        flash_lower = create_flash(win, position="lower")

        response_text = visual.TextStim(
            win,
            text=(
                "Combien de flashs avez-vous perçus ?\n\n"
                "1 = Un flash\n"
                "2 = Deux flashs\n\n"
                "Appuyez sur 1 ou 2."
            ),
            color="white",
            units="pix",
            height=32,
            wrapWidth=win.size[0] * 0.58,
            alignText="center"
        )

        if CONFIDENCE_MODE == "discrete":
            confidence_widget = visual.TextStim(
                win,
                text=(
                    "Indiquez votre degré de confiance dans votre réponse.\n\n"
                    "1        2        3        4\n\n"
                    "1 = proche du hasard\n"
                    "4 = certain"
                ),
                color="white",
                units="pix",
                height=30,
                wrapWidth=win.size[0] * 0.60,
                alignText="center"
            )

        elif CONFIDENCE_MODE == "continuous":
            bar_left_x = -6.0
            bar_right_x = 6.0
            bar_y = -2.0
            tick_y = -3.0
            qual_y = -4.1

            tick_values = np.linspace(CONF_MIN, CONF_MAX, 6, dtype=int).tolist()
            tick_positions = np.linspace(bar_left_x, bar_right_x, len(tick_values))

            confidence_widget = {
                "instruction": visual.TextStim(
                    win,
                    text=(
                        "Indiquez votre degré de confiance.\n\n"
                        f"Déplacez la souris sur la barre entre {CONF_MIN} % et {CONF_MAX} %.\n"
                        "Cliquez pour valider."
                    ),
                    color="white",
                    units="pix",
                    height=30,
                    wrapWidth=win.size[0] * 0.62,
                    pos=(0, 140),
                    alignText="center"
                ),
                "bar": visual.Line(
                    win,
                    start=(bar_left_x, bar_y),
                    end=(bar_right_x, bar_y),
                    lineColor="white",
                    lineWidth=8.0,
                    units="deg"
                ),
                "active_bar": visual.Line(
                    win,
                    start=(bar_left_x, bar_y),
                    end=(bar_left_x, bar_y),
                    lineColor="white",
                    lineWidth=10.0,
                    units="deg"
                ),
                "marker": visual.Circle(
                    win,
                    radius=0.25,
                    fillColor="white",
                    lineColor="white",
                    units="deg",
                    pos=(bar_left_x, bar_y)
                ),
                "bar_left_x": bar_left_x,
                "bar_right_x": bar_right_x,
                "bar_y": bar_y,
                "hover_half_height": 0.55,
                "tick_labels": [
                    visual.TextStim(
                        win,
                        text=f"{value}%",
                        color="white",
                        units="deg",
                        height=0.34,
                        pos=(x, tick_y)
                    )
                    for value, x in zip(tick_values, tick_positions)
                ],
                "qual_labels": [
                    visual.TextStim(
                        win,
                        text="Pas sûr du tout",
                        color="white",
                        units="deg",
                        height=0.45,
                        pos=(-5.8, qual_y)
                    ),
                    visual.TextStim(
                        win,
                        text="Tout à fait sûr",
                        color="white",
                        units="deg",
                        height=0.45,
                        pos=(5.8, qual_y)
                    ),
                ],
                "value_text": visual.TextStim(
                    win,
                    text="",
                    color="white",
                    units="pix",
                    height=34,
                    pos=(0, 20),
                    alignText="center"
                )
            }
        else:
            raise ValueError(f"Unknown CONFIDENCE_MODE: {CONFIDENCE_MODE}")

        flash_frames = max(1, ms_to_frames(FLASH_DURATION_MS, frame_period))
        isi_ms = SOA_MS - FLASH_DURATION_MS
        isi_frames = ms_to_frames(isi_ms, frame_period)

        if isi_frames < 0:
            raise ValueError(
                f"Computed isi_frames is negative ({isi_frames}). "
                f"Check SOA_MS ({SOA_MS}) and FLASH_DURATION_MS ({FLASH_DURATION_MS})."
            )

        soa_programmed_s = (flash_frames + isi_frames) * frame_period
        isi_programmed_s = isi_frames * frame_period

        date_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_values.update({
            "date_start": date_start,
            "framerate": frame_rate,
            "frame_period": frame_period,
            "resolution": str(win.size),
            "screen_width_cm": calibration.get("screen_width_cm", np.nan),
            "pixels_per_cm": calibration.get("pixels_per_cm", np.nan),
            "viewing_distance_cm": calibration.get("viewing_distance_cm", np.nan),
            "viewing_distance_method": calibration.get("viewing_distance_method", ""),
            "viewing_distance_n_valid": calibration.get("viewing_distance_n_valid", np.nan),
            "viewing_distance_iqr_cm": calibration.get("viewing_distance_iqr_cm", np.nan),
            "viewing_distance_notes": calibration.get("viewing_distance_notes", ""),
            "flash_frames": flash_frames,
            "standard_isi_frames": isi_frames,
            "standard_soa_programmed_s": soa_programmed_s,
            "standard_isi_programmed_s": isi_programmed_s,
            "frame_median_ms": timing_info.get("median_ms", np.nan),
            "frame_sd_ms": timing_info.get("sd_ms", np.nan),
            "frame_mean_ms": timing_info.get("mean_ms", np.nan),
        })
        write_session_csv(session_path, session_values, atomic=False)

        blocks = generate_blocks()
        logger = TrialLogger(trials_path)

        if not DEBUG_MODE:
            show_instructions(win)

            run_practice(
                win,
                kb,
                fixation,
                tone,
                flash_upper,
                flash_lower,
                response_text,
                confidence_widget,
                flash_frames,
                isi_frames,
                frame_period
            )

        for block_index, block in enumerate(blocks):
            block_text = visual.TextStim(
                win,
                text=f"Bloc {block_index + 1} / {len(blocks)}\n\nAppuyez sur ESPACE pour commencer.",
                color="white",
                units="pix",
                height=32,
                wrapWidth=win.size[0] * 0.60,
                alignText="center"
            )
            block_text.draw()
            win.flip()

            event.clearEvents()
            keys = event.waitKeys(keyList=["space", "escape"])
            if "escape" in keys:
                raise ExperimentAbort("User aborted (escape) before block start")

            for trial_index, trial in enumerate(block):
                try:
                    condition_label = trial["condition_label"]
                    base_condition = trial["base_condition"]
                    soa_ms = float(trial["soa_ms"])
                    soa_type = trial["soa_type"]
                    correct_answer = trial["correct_answer"]

                    trial_isi_ms = soa_ms - FLASH_DURATION_MS
                    trial_isi_frames = ms_to_frames(trial_isi_ms, frame_period)

                    if trial_isi_frames < 0:
                        raise ValueError(
                            f"Negative trial_isi_frames={trial_isi_frames} for "
                            f"condition={condition_label}, soa_ms={soa_ms}, "
                            f"FLASH_DURATION_MS={FLASH_DURATION_MS}."
                        )

                    trial_data = run_trial(
                        win,
                        kb,
                        fixation,
                        tone,
                        flash_upper,
                        flash_lower,
                        response_text,
                        confidence_widget,
                        flash_frames,
                        trial_isi_frames,
                        frame_period,
                        base_condition,
                        trial["position"]
                    )

                    accuracy = 1 if trial_data["response"] == correct_answer else 0

                    illusion_type = trial.get("illusion_type", "none")

                    fission_illusion = 1 if (
                        base_condition == "A1V1_A2"
                        and trial_data["response"] == "2"
                    ) else 0

                    fusion_illusion = 1 if (
                        base_condition == "A1V1_V2"
                        and trial_data["response"] == "1"
                    ) else 0

                    illusion = 1 if (fission_illusion or fusion_illusion) else 0

                    logger.log_trial({
                        "participant": participant_id,
                        "block": block_index + 1,
                        "trial": trial_index + 1,
                        "condition": condition_label,
                        "base_condition": base_condition,
                        "soa_type": soa_type,
                        "soa_ms": soa_ms,
                        "position": trial["position"],
                        "response": trial_data["response"],
                        "rt": trial_data["rt"],
                        "correct_answer": correct_answer,
                        "accuracy": accuracy,
                        "illusion": illusion,
                        "illusion_type": illusion_type,
                        "fission_illusion": fission_illusion,
                        "fusion_illusion": fusion_illusion,
                        "confidence": trial_data["confidence"],
                        "confidence_mode": CONFIDENCE_MODE,
                        "rt_conf": trial_data["rt_conf"],
                        "fixation_programmed_s": trial_data["fixation_programmed_s"],
                        "fixation_measured_s": trial_data["fixation_measured_s"],
                        "flash_frames": trial_data["flash_frames"],
                        "isi_frames": trial_data["isi_frames"],
                        "flash1_onset_time": trial_data["flash1_onset_time"],
                        "flash1_offset_time": trial_data["flash1_offset_time"],
                        "isi_blank_start_time": trial_data["isi_blank_start_time"],
                        "isi_blank_end_time": trial_data["isi_blank_end_time"],
                        "flash2_onset_time": trial_data["flash2_onset_time"],
                        "flash2_offset_time": trial_data["flash2_offset_time"],
                        "beep1_scheduled_ptb_time": trial_data["beep1_scheduled_ptb_time"],
                        "beep1_flip_proxy_time": trial_data["beep1_flip_proxy_time"],
                        "beep2_scheduled_ptb_time": trial_data["beep2_scheduled_ptb_time"],
                        "beep2_flip_proxy_time": trial_data["beep2_flip_proxy_time"],
                        "soa_visual_programmed_s": trial_data["soa_visual_programmed_s"],
                        "soa_visual_flip_measured_s": trial_data["soa_visual_flip_measured_s"],
                        "soa_audio_programmed_s": trial_data["soa_audio_programmed_s"],
                        "soa_audio_scheduled_s": trial_data["soa_audio_scheduled_s"],
                        "soa_audio_flip_proxy_s": trial_data["soa_audio_flip_proxy_s"],
                        "isi_blank_programmed_s": trial_data["isi_blank_programmed_s"],
                        "isi_blank_measured_s": trial_data["isi_blank_measured_s"],
                        "dropped_fixation": trial_data["dropped_fixation"],
                        "dropped_stim1": trial_data["dropped_stim1"],
                        "dropped_isi": trial_data["dropped_isi"],
                        "dropped_stim2": trial_data["dropped_stim2"],
                        "dropped_poststim": trial_data["dropped_poststim"],
                        "dropped_frames_total": trial_data["dropped_frames_total"],
                        "trial_total_s": trial_data["trial_total_s"],
                        "error": "",
                    })

                except ExperimentAbort:
                    raise
                except Exception as e:
                    logger.log_error(
                        participant_id,
                        block_index + 1,
                        trial_index + 1,
                        trial.get("condition_label", ""),
                        trial.get("position", ""),
                        f"{type(e).__name__}: {str(e)}",
                        base_condition=trial.get("base_condition", ""),
                        soa_type=trial.get("soa_type", ""),
                        soa_ms=trial.get("soa_ms", ""),
                    )

            if block_index < len(blocks) - 1:
                pause_text = visual.TextStim(
                    win,
                    text=(
                        "Pause\n\n"
                        "Prenez autant de temps que nécessaire.\n\n"
                        "Merci de rester assis et de conserver la même position devant l'écran, "
                        "car la distance à l'écran doit rester stable pendant l'expérience.\n\n"
                        "Appuyez sur ESPACE pour continuer."
                    ),
                    color="white",
                    units="pix",
                    height=30,
                    wrapWidth=win.size[0] * 0.68,
                    alignText="center"
                )
                pause_text.draw()
                win.flip()

                event.clearEvents()
                keys = event.waitKeys(keyList=["space", "escape"])
                if "escape" in keys:
                    raise ExperimentAbort("User aborted (escape) during pause")

        end_text = visual.TextStim(
            win,
            text="Expérience terminée.\n\nMerci pour votre participation.",
            color="white",
            units="pix",
            height=34,
            wrapWidth=win.size[0] * 0.60,
            alignText="center"
        )
        end_text.draw()
        win.flip()
        event.waitKeys(keyList=["space", "escape"])

        completed = 1

    except ExperimentAbort as e:
        abort_reason = str(e) if str(e) else "User aborted (escape)"

    except Exception as e:
        abort_reason = f"Global error: {type(e).__name__}: {str(e)}"
        print("GLOBAL ERROR:", abort_reason)

    finally:
        if logger is not None:
            logger.close()

        setup_win = _safe_close_window(setup_win)
        blindspot_win = _safe_close_window(blindspot_win)
        win = _safe_close_window(win)

    try:
        if os.path.exists(trials_path):
            session_summary = build_session_summary(
                trials_path=trials_path,
                design_mode=DESIGN_MODE,
            )
            save_session_summary(
                session_summary,
                condition_summary_path=condition_summary_path,
                block_summary_path=block_summary_path,
            )
            print(format_session_summary(session_summary, session_values))
    except Exception as exc:
        session_summary = None
        print(f"Session summary error: {type(exc).__name__}: {exc}")

    try:
        session_values.update(
            {
                "date_end": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "completed": completed,
                "abort_reason": abort_reason,
            }
        )
        if session_summary is not None:
            session_values.update(session_summary.timing_metrics)

        write_session_csv(session_path, session_values, atomic=True)
    except Exception as exc:
        print(f"Session save error: {type(exc).__name__}: {exc}")

    core.quit()


if __name__ == "__main__":
    main()
