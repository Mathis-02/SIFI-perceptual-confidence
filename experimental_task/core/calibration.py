"""Screen-size and viewing-distance calibration procedures."""

import numpy as np
from psychopy import core, event, monitors, visual

from config import MAX_ACCEPTABLE_IQR_CM
from core.abort import ExperimentAbort

def _create_clean_pix_window(fullscr=True, allow_gui=False):
    win = visual.Window(
        fullscr=fullscr,
        units="pix",
        color="black",
        allowGUI=allow_gui,
        checkTiming=False,
        infoMsg="",
        waitBlanking=True
    )
    win.mouseVisible = False
    return win


def _estimate_frame_rate_safely(win):
    """Estimate the display refresh rate without showing PsychoPy messages."""
    try:
        fps = win.getActualFrameRate(
            nIdentical=20,
            nMaxFrames=120,
            nWarmUpFrames=20,
            threshold=1,
            infoMsg=""
        )
        if fps is not None and fps > 0:
            return float(fps)
    except Exception:
        pass

    try:
        mean_ms, sd_ms, median_ms = win.getMsPerFrame(
            nFrames=60,
            showVisual=False,
            msg=""
        )
        if median_ms is not None and median_ms > 0:
            return 1000.0 / float(median_ms)
    except Exception:
        pass

    if getattr(win, "monitorFramePeriod", None):
        if win.monitorFramePeriod > 0:
            return 1.0 / float(win.monitorFramePeriod)

    return 60.0



# Bank-card screen-size calibration


def calibrate_screen(win):
    win.mouseVisible = False

    CARD_WIDTH_CM = 8.56
    CARD_HEIGHT_CM = 5.398
    CARD_RATIO = CARD_HEIGHT_CM / CARD_WIDTH_CM

    while True:
        width_pix_small = _run_card_calibration_trial(win, 300.0, CARD_RATIO)
        width_pix_large = _run_card_calibration_trial(win, 500.0, CARD_RATIO)

        width_pix = (width_pix_small + width_pix_large) / 2.0

        pixels_per_cm = width_pix / CARD_WIDTH_CM
        screen_width_cm = win.size[0] / pixels_per_cm

        if 25 <= screen_width_cm <= 100:
            return {
                "pixels_per_cm": float(pixels_per_cm),
                "screen_width_cm": float(screen_width_cm),
                "resolution": win.size,
                "card_calibration_small_start_pix": float(width_pix_small),
                "card_calibration_large_start_pix": float(width_pix_large),
                "card_calibration_mean_pix": float(width_pix),
            }

        _warning(win)


def _run_card_calibration_trial(win, initial_width_pix, card_ratio):
    width_pix = float(initial_width_pix)

    rect = visual.Rect(
        win,
        width=width_pix,
        height=width_pix * card_ratio,
        units="pix",
        lineColor="white",
        lineWidth=2
    )

    instructions = visual.TextStim(
        win,
        text=(
            "CALIBRATION DE L’ÉCRAN\n\n"
            "Placez une carte bancaire contre l’écran.\n"
            "Ajustez le rectangle pour qu’il ait exactement\n"
            "la même taille que la carte.\n\n"
            "Flèche droite : agrandir\n"
            "Flèche gauche : rétrécir\n"
            "Maj + flèche : ajustement fin\n\n"
            "Alignez les bords du rectangle avec ceux de la carte.\n\n"
            "ESPACE : valider"
        ),
        pos=(0, -300),
        units="pix",
        height=22,
        wrapWidth=1000,
    )

    while True:
        win.mouseVisible = False
        keys = event.getKeys(modifiers=True)

        for key, modifiers in keys:
            step = 1 if modifiers["shift"] else 5

            if key == "right":
                width_pix += step
            elif key == "left":
                width_pix = max(50, width_pix - step)
            elif key == "space":
                event.clearEvents()
                return width_pix
            elif key == "escape":
                raise ExperimentAbort("User aborted (escape) during calibration")

        rect.size = (width_pix, width_pix * card_ratio)
        rect.draw()
        instructions.draw()
        win.flip()




def _warning(win):
    warn_text = visual.TextStim(
        win,
        text=(
            "Calibration incohérente détectée.\n"
            "Veuillez recommencer attentivement."
        ),
        units="pix",
        height=24,
        color="red"
    )

    warn_text.draw()
    win.flip()
    core.wait(2)



# Blind-spot viewing-distance calibration


def _show_blindspot_retry_instructions(win):
    retry_msg = visual.TextStim(
        win,
        text=(
            "La première mesure de distance n'a pas été suffisamment fiable.\n\n"
            "Nous allons recommencer avec des consignes plus précises.\n\n"
            "IMPORTANT :\n"
            "• Fermez uniquement l'œil GAUCHE.\n"
            "• Gardez l'œil DROIT ouvert.\n"
            "• Fixez en permanence la croix rouge au centre.\n"
            "• Ne suivez pas le point blanc avec les yeux.\n"
            "• Gardez la tête aussi immobile que possible.\n"
            "• Le point blanc apparaît à droite de la croix et continue vers la droite.\n"
            "• Appuyez sur ESPACE dès qu'il disparaît complètement.\n\n"
            "Appuyez sur ESPACE pour recommencer."
        ),
        color="white",
        height=25,
        units="pix",
        wrapWidth=1100
    )

    while True:
        retry_msg.draw()
        win.flip()

        keys = event.getKeys(keyList=["space", "escape"])
        if "escape" in keys:
            raise ExperimentAbort("User aborted (escape) during calibration")
        if "space" in keys:
            event.clearEvents()
            return


def estimate_viewing_distance(win, pixels_per_cm, n_trials=5, show_intro=True):
    win.mouseVisible = False

    BLIND_SPOT_DEG = 13.5
    START_OFFSET_CM = 0.5
    END_OFFSET_CM = 25.0
    SPEED_CM_PER_SEC = 2
    PRE_FIXATION_S = 1.0

    MIN_VALID_TRIALS = 3

    frame_rate = _estimate_frame_rate_safely(win)
    speed_pix_per_frame = (SPEED_CM_PER_SEC * pixels_per_cm) / frame_rate
    start_offset_pix = START_OFFSET_CM * pixels_per_cm
    end_offset_pix = END_OFFSET_CM * pixels_per_cm

    distances = []

    intro_msg = visual.TextStim(
        win,
        text=(
            "MESURE DE LA DISTANCE (point aveugle)\n\n"
            "• Fermez l'œil GAUCHE.\n"
            "• Gardez l'œil DROIT ouvert.\n"
            "• Fixez la croix ROUGE au centre pendant tout l'essai.\n"
            "• Ne regardez pas le point blanc directement.\n"
            "• Un point blanc apparaîtra à droite de la croix et se déplacera encore plus vers la droite.\n"
            "• Appuyez sur ESPACE dès qu'il DISPARAÎT.\n\n"
            "Appuyez sur ESPACE pour commencer."
        ),
        color="white",
        height=25,
        units="pix",
        wrapWidth=1100
    )

    trial_msg = visual.TextStim(
        win,
        text="",
        color="white",
        height=30,
        units="pix"
    )

    fixation = visual.TextStim(
        win,
        text="+",
        color="red",
        height=35,
        units="pix"
    )

    dot = visual.Circle(
        win,
        radius=0.5 * pixels_per_cm,
        fillColor="white",
        lineColor="white",
        units="pix"
    )

    if show_intro:
        while True:
            intro_msg.draw()
            win.flip()

            keys = event.getKeys(keyList=["space", "escape"])
            if "escape" in keys:
                raise ExperimentAbort("User aborted (escape) during calibration")
            if "space" in keys:
                event.clearEvents()
                break

    for t in range(n_trials):
        trial_msg.text = f"Essai {t + 1} / {n_trials}\n\nPrêt ? Appuyez sur ESPACE."

        while True:
            trial_msg.draw()
            win.flip()

            keys = event.getKeys(keyList=["space", "escape"])
            if "escape" in keys:
                raise ExperimentAbort("User aborted (escape) during calibration")
            if "space" in keys:
                event.clearEvents()
                break

        core.wait(0.4)

        pre_fix_clock = core.Clock()
        while pre_fix_clock.getTime() < PRE_FIXATION_S:
            fixation.draw()
            win.flip()

        x_pos = start_offset_pix
        pressed = False

        while True:
            fixation.draw()
            dot.pos = (x_pos, 0)
            dot.draw()
            win.flip()

            keys = event.getKeys(keyList=["space", "escape"])
            if "escape" in keys:
                raise ExperimentAbort("User aborted (escape) during calibration")
            if "space" in keys:
                event.clearEvents()
                pressed = True
                break

            x_pos += speed_pix_per_frame

            if x_pos > end_offset_pix:
                pressed = False
                break

        if pressed:
            x_cm = x_pos / pixels_per_cm
            dist_cm = x_cm / np.tan(np.deg2rad(BLIND_SPOT_DEG))
            distances.append(float(dist_cm))

        win.flip()
        core.wait(0.8)

    qc = {
        "n_trials": int(n_trials),
        "n_valid": int(len(distances)),
        "median_cm": float(np.median(distances)) if len(distances) else np.nan,
        "iqr_cm": float(np.subtract(*np.percentile(distances, [75, 25]))) if len(distances) >= 2 else np.nan,
        "notes": ""
    }

    if len(distances) < MIN_VALID_TRIALS:
        qc["notes"] = "Too few valid blindspot trials"
        return None, qc

    median = float(np.median(distances))
    iqr = qc["iqr_cm"]

    if not (30.0 <= median <= 120.0):
        qc["notes"] = "Median out of plausible range"
        return None, qc

    if not np.isnan(iqr) and iqr > max(15.0, 0.25 * median):
        qc["notes"] = "High variability across trials"
        return None, qc

    qc["notes"] = "OK"
    return median, qc


def run_blindspot_distance_calibration(win, calibration, n_trials=5, retry_trials=3):
    win.mouseVisible = False
    pixels_per_cm = calibration["pixels_per_cm"]

    viewing_distance_cm, dist_qc = estimate_viewing_distance(
        win,
        pixels_per_cm,
        n_trials=n_trials,
        show_intro=True
    )

    first_iqr = dist_qc.get("iqr_cm", np.nan)

    needs_retry = (
        viewing_distance_cm is None
        or (
            not np.isnan(first_iqr)
            and first_iqr > MAX_ACCEPTABLE_IQR_CM
        )
    )

    if needs_retry:
        if viewing_distance_cm is None:
            dist_qc["notes"] = f"{dist_qc.get('notes', '')} | retry_trigger=invalid_measure"
        else:
            dist_qc["notes"] = f"{dist_qc.get('notes', '')} | retry_trigger=high_iqr"

        _show_blindspot_retry_instructions(win)

        viewing_distance_cm_retry, dist_qc_retry = estimate_viewing_distance(
            win,
            pixels_per_cm,
            n_trials=retry_trials,
            show_intro=False
        )

        retry_iqr = dist_qc_retry.get("iqr_cm", np.nan)

        retry_ok = (
            viewing_distance_cm_retry is not None
            and (
                np.isnan(retry_iqr) or retry_iqr <= MAX_ACCEPTABLE_IQR_CM
            )
        )

        if retry_ok:
            viewing_distance_cm = viewing_distance_cm_retry
            dist_qc = dist_qc_retry
            calibration["viewing_distance_method"] = "blindspot_retry"
        else:
            viewing_distance_cm = 60.0
            dist_qc = dist_qc_retry
            calibration["viewing_distance_method"] = "fallback_60cm_after_retry"
    else:
        calibration["viewing_distance_method"] = "blindspot"

    calibration["viewing_distance_cm"] = float(viewing_distance_cm)
    calibration["viewing_distance_n_valid"] = int(dist_qc.get("n_valid", 0))
    calibration["viewing_distance_iqr_cm"] = float(dist_qc.get("iqr_cm", np.nan))
    calibration["viewing_distance_notes"] = dist_qc.get("notes", "")

    return calibration


def run_screen_size_calibration():
    """Run the bank-card calibration in a temporary full-screen window."""
    win = _create_clean_pix_window(fullscr=True, allow_gui=False)
    try:
        return calibrate_screen(win)
    finally:
        win.close()
        core.wait(0.3)


def build_monitor_from_calibration(
    calibration,
    monitor_name="calibrated_monitor",
    default_distance_cm=60.0,
):
    """Create a PsychoPy monitor object from calibration measurements."""
    mon = monitors.Monitor(monitor_name)
    mon.setWidth(calibration["screen_width_cm"])
    mon.setDistance(calibration.get("viewing_distance_cm", default_distance_cm))
    mon.setSizePix(calibration["resolution"])
    return mon


def run_screen_calibration():
    calibration = run_screen_size_calibration()

    win = _create_clean_pix_window(fullscr=True, allow_gui=False)
    calibration = run_blindspot_distance_calibration(
        win,
        calibration,
        n_trials=5,
        retry_trials=3
    )
    win.close()
    core.wait(0.3)

    mon = build_monitor_from_calibration(calibration)
    return mon, calibration
