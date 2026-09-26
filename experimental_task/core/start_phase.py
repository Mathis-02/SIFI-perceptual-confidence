"""Audio checks, instructions, demonstrations, and practice trials."""

from psychopy import visual, event, core
import random
import numpy as np

from core.trial import run_trial
from config import CONDITIONS, CONFIDENCE_MODE, LAB_MODE, DESIGN_MODE
from core.abort import ExperimentAbort


LAB_INSTR_WIDTH_RATIO = 0.76
LAB_SHORT_WIDTH_RATIO = 0.66
LAB_TEXT_HEIGHT_PX = 30
LAB_SHORT_TEXT_HEIGHT_PX = 32
LAB_SUBTEXT_HEIGHT_PX = 24

def _get_practice_conditions():
    if DESIGN_MODE == "av_fission_fusion_2soa":
        return ["A1V1", "A1V1_A2", "A1V1_V2", "A1V1_A2V2"]

    return CONDITIONS


def _make_text(win, text, *, short=False, y=0, align="center", color="white"):
    width_ratio = LAB_SHORT_WIDTH_RATIO if short else LAB_INSTR_WIDTH_RATIO
    height_px = LAB_SHORT_TEXT_HEIGHT_PX if short else LAB_TEXT_HEIGHT_PX
    return visual.TextStim(
        win,
        text=text,
        color=color,
        units="pix",
        height=height_px,
        wrapWidth=win.size[0] * width_ratio,
        pos=(0, y),
        alignText=align,
    )


def _wait_keys(win, stim, valid_keys, escape_message):
    while True:
        stim.draw()
        win.flip()
        keys = event.getKeys(keyList=valid_keys + ["escape"])
        if "escape" in keys:
            raise ExperimentAbort(escape_message)
        for key in valid_keys:
            if key in keys:
                event.clearEvents()
                return key


def _wait_for_space(win, stim, escape_message):
    _wait_keys(win, stim, ["space"], escape_message)


def _run_fixation_for_seconds(win, fixation, duration_s, frame_period):
    n_frames = max(1, int(round(duration_s / frame_period)))
    for _ in range(n_frames):
        fixation.draw()
        win.flip()


def run_audio_calibration(win, tone):
    instruction_text = visual.TextStim(
        win,
        text=(
            "RÉGLAGE AUDIO\n\n"
            "Veuillez utiliser un casque ou des écouteurs.\n\n"
            "Vous pouvez maintenant ajuster le volume de votre ordinateur si nécessaire.\n\n"
            "Objectif : obtenir un son clairement audible, mais confortable.\n\n"
            "Appuyez sur ESPACE pour écouter les sons de test."
        ),
        color="white",
        height=28,
        wrapWidth=1000,
        units="pix",
    )

    playing_text = visual.TextStim(
        win,
        text=(
            "Lecture des sons de test...\n\n"
            "Vous pouvez ajuster le volume pendant cette étape."
        ),
        color="white",
        height=28,
        wrapWidth=1000,
        units="pix"
    )

    confirm_text = visual.TextStim(
        win,
        text=(
            "Le volume est-il correct ?\n\n"
            "ESPACE = Oui, continuer\n"
            "R = Réécouter immédiatement les sons\n"
            "ÉCHAP = Quitter"
        ),
        color="white",
        height=28,
        wrapWidth=1000,
        units="pix"
    )

    _wait_for_space(win, instruction_text, "User aborted (escape) during calibration")

    while True:
        event.clearEvents()
        for _ in range(3):
            playing_text.draw()
            win.flip()
            tone.play()
            core.wait(0.5)

        key = _wait_keys(
            win,
            confirm_text,
            ["space", "r"],
            "User aborted (escape) during calibration"
        )
        if key == "space":
            return


def run_visual_display_check(win):
    intro_text = visual.TextStim(
        win,
        text=(
            "RÉGLAGE DE L'ÉCRAN\n\n"
            "Réglez maintenant la luminosité de votre écran à l’aide des paramètres de votre ordinateur.\n\n"
            "Désactivez si possible :\n"
            "- le mode nuit / filtre de lumière bleue\n"
            "- True Tone / Night Shift\n"
            "- la luminosité automatique\n\n"
            "Réglez l’écran jusqu’à ce que :\n"
            "- les carrés sombres restent visibles sur le fond noir,\n"
            "- le dégradé paraisse progressif,\n"
            "- les carrés clairs restent distincts les uns des autres.\n\n"
            "Appuyez sur ESPACE pour afficher la mire."
        ),
        color="white",
        height=28,
        wrapWidth=1000,
        units="pix",
    )

    _wait_for_space(win, intro_text, "User aborted (escape) during calibration")

    labels = [
        visual.TextStim(win, text="Carrés très sombres", color="white", height=24, pos=(0, 215), units="pix"),
        visual.TextStim(win, text="doivent rester visibles", color=[0.75] * 3, height=18, pos=(0, 185), units="pix"),
        visual.TextStim(win, text="Dégradé de gris", color="white", height=24, pos=(0, 55), units="pix"),
        visual.TextStim(win, text="doit paraître progressif", color=[0.75] * 3, height=18, pos=(0, 25), units="pix"),
        visual.TextStim(win, text="Carrés très clairs", color="white", height=24, pos=(0, -105), units="pix"),
        visual.TextStim(win, text="doivent rester distincts", color=[0.75] * 3, height=18, pos=(0, -135), units="pix"),
        visual.TextStim(
            win,
            text="Appuyez sur ESPACE quand le réglage vous semble correct",
            color=[0.82] * 3,
            height=22,
            pos=(0, -320),
            units="pix"
        ),
    ]

    dark_patches = [
        visual.Rect(win, width=110, height=90, pos=(x, 115), fillColor=[lv] * 3, lineColor=[lv] * 3, units="pix")
        for x, lv in zip([-375, -225, -75, 75, 225, 375], [-0.93, -0.89, -0.84, -0.78, -0.70, -0.60])
    ]

    grad_w = 40
    gradient_bars = [
        visual.Rect(
            win,
            width=grad_w,
            height=60,
            pos=(-420 + i * grad_w, -55),
            fillColor=[lv] * 3,
            lineColor=[lv] * 3,
            units="pix"
        )
        for i, lv in enumerate([
            -1.0, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4,
            -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3,
            0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0
        ])
    ]

    light_patches = [
        visual.Rect(win, width=110, height=90, pos=(x, -215), fillColor=[lv] * 3, lineColor=[lv] * 3, units="pix")
        for x, lv in zip([-375, -225, -75, 75, 225, 375], [0.55, 0.68, 0.80, 0.90, 0.96, 1.00])
    ]

    static_elements = labels + dark_patches + gradient_bars + light_patches

    while True:
        for el in static_elements:
            el.draw()
        win.flip()

        keys = event.getKeys(keyList=["space", "escape"])
        if "escape" in keys:
            raise ExperimentAbort("User aborted (escape) during calibration")
        if "space" in keys:
            event.clearEvents()
            return


def show_instructions(win):
    if DESIGN_MODE == "av_fission_fusion_2soa":
        first_page = (
            "Dans cette expérience, vous verrez un ou deux flashs lumineux, présentés sous la forme de ronds blancs.\n\n"
            "Des sons seront également présentés.\n\n"
            "Votre tâche sera d’indiquer combien de flashs vous avez perçus.\n\n"
            "Appuyez sur ESPACE pour continuer."
        )
    else:
        first_page = (
            "Dans cette expérience, vous verrez un ou deux flashs lumineux, présentés sous la forme de ronds blancs.\n\n"
            "Parfois, des sons seront également présentés.\n\n"
            "Votre tâche sera d’indiquer combien de flashs vous avez perçus.\n\n"
            "Appuyez sur ESPACE pour continuer."
        )

    pages = [first_page]

    if not LAB_MODE:
        pages.append(
            (
                "IMPORTANT\n\n"
                "Essayez de garder la même position que pendant la calibration.\n\n"
                "La distance entre vos yeux et l’écran est importante pour que les stimuli soient présentés correctement.\n\n"
                "Pendant toute l’expérience, gardez le regard fixé sur la croix au centre de l’écran et évitez d’avancer ou de reculer la tête.\n\n"
                "Appuyez sur ESPACE pour continuer."
            )
        )

        pages.append(
            (
                "IMPORTANT — CONDITIONS DE PASSATION\n\n"
                "Gardez votre casque ou vos écouteurs en place pendant toute l’expérience.\n\n"
                "Ne modifiez plus le volume ni la luminosité de l’écran après les réglages.\n\n"
                "Essayez de rester dans un environnement calme.\n\n"
                "Appuyez sur ESPACE pour continuer."
            )
        )

    for page in pages:
        txt = _make_text(win, page, short=False)
        _wait_for_space(win, txt, "User aborted (escape) during instructions")


def _draw_demo_sequence(win, fixation, flash, flash_frames, isi_frames, frame_period, n_flashes):
    _run_fixation_for_seconds(win, fixation, duration_s=1.2, frame_period=frame_period)

    for _ in range(flash_frames):
        fixation.draw()
        flash.draw()
        win.flip()

    if n_flashes == 2:
        for _ in range(isi_frames):
            fixation.draw()
            win.flip()

        for _ in range(flash_frames):
            fixation.draw()
            flash.draw()
            win.flip()

    _run_fixation_for_seconds(win, fixation, duration_s=0.6, frame_period=frame_period)


def show_flash_demo(win, fixation, flash_upper, flash_lower, flash_frames, isi_frames, frame_period):
    intro = _make_text(
        win,
        "Avant de commencer l’entraînement, nous allons vous montrer un exemple avec un seul flash, puis un exemple avec deux flashs.\n\n"
        "Observez bien la différence entre les deux.\n\n"
        "Appuyez sur ESPACE pour continuer."
    )

    prompts = [
        (
            "Exemple : UN flash\n\n"
            "Gardez les yeux sur la croix centrale.\n\n"
            "Appuyez sur ESPACE pour voir l’exemple.",
            1
        ),
        (
            "Exemple : DEUX flashs\n\n"
            "Gardez les yeux sur la croix centrale.\n\n"
            "Appuyez sur ESPACE pour voir l’exemple.",
            2
        ),
    ]

    end_text = _make_text(
        win,
        "L’entraînement va maintenant commencer.\n\n"
        "Appuyez sur ESPACE pour continuer.",
        short=True
    )

    _wait_for_space(win, intro, "User aborted (escape) during flash demo")

    for text, n_flashes in prompts:
        stim = _make_text(win, text, short=True)
        _wait_for_space(win, stim, "User aborted (escape) during flash demo")
        _draw_demo_sequence(
            win=win,
            fixation=fixation,
            flash=flash_upper,
            flash_frames=flash_frames,
            isi_frames=isi_frames,
            frame_period=frame_period,
            n_flashes=n_flashes
        )

    _wait_for_space(win, end_text, "User aborted (escape) during flash demo")


def _make_practice_trials_balanced(n_reps_per_condition=4):
    practice_conditions = _get_practice_conditions()

    trials = [
        {"condition": condition, "position": random.choice(["upper", "lower"])}
        for condition in practice_conditions
        for _ in range(n_reps_per_condition)
    ]

    random.shuffle(trials)
    return trials


def _make_practice_trials_baseline_weighted():
    if DESIGN_MODE == "av_fission_fusion_2soa":
        weighted_conditions = (
            ["A1V1"] * 6
            + ["A1V1_A2"] * 4
            + ["A1V1_V2"] * 4
            + ["A1V1_A2V2"] * 6
        )
    else:
        weighted_conditions = (
            ["V1"] * 6
            + ["V1V2"] * 6
            + ["A1V1_A2"] * 2
            + ["A1V1_A2V2"] * 2
        )

    trials = [
        {"condition": cond, "position": random.choice(["upper", "lower"])}
        for cond in weighted_conditions
    ]

    random.shuffle(trials)
    return trials

def _run_practice_block(
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
    frame_period,
    trials,
    ask_confidence
):
    results = []

    for trial in trials:
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
            isi_frames,
            frame_period,
            trial["condition"],
            trial["position"],
            ask_confidence=ask_confidence
        )
        results.append({
            "condition": trial["condition"],
            "position": trial["position"],
            "response": trial_data["response"],
            "rt": trial_data["rt"],
            "confidence": trial_data.get("confidence", np.nan),
            "rt_conf": trial_data.get("rt_conf", np.nan),
        })

    return results


def _compute_practice_baseline_metrics(results):
    metrics = {}

    if DESIGN_MODE == "av_fission_fusion_2soa":
        expected_map = {
            "A1V1": "1",
            "A1V1_A2": "1",
            "A1V1_V2": "2",
            "A1V1_A2V2": "2",
        }
    else:
        expected_map = {
            "V1": "1",
            "V1V2": "2",
        }

    for cond, expected in expected_map.items():
        subset = [r for r in results if r["condition"] == cond]
        metrics[f"acc_{cond}"] = (
            float(np.mean([r["response"] == expected for r in subset]))
            if subset else np.nan
        )

    return metrics


def _compute_practice_confidence_metrics(results, conf_mode):
    confs = []
    for r in results:
        c = r.get("confidence", np.nan)
        if c is None:
            continue
        try:
            c = float(c)
        except Exception:
            continue
        if np.isnan(c):
            continue
        confs.append(c)

    if not confs:
        return {"n_conf": 0, "n_unique_conf": 0, "bad_confidence": False}

    confs = np.array(confs, dtype=float)
    n_unique = len(np.unique(confs))

    if conf_mode == "continuous":
        conf_min = float(np.min(confs))
        conf_max = float(np.max(confs))
        conf_range = float(conf_max - conf_min)
        extreme_band_prop = float(
            np.mean(((confs >= 50) & (confs <= 60)) | ((confs >= 90) & (confs <= 100)))
        )

        bad_confidence = (
            (n_unique <= 4) or
            (conf_range < 20) or
            (extreme_band_prop >= 0.90)
        )

        return {
            "n_conf": int(len(confs)),
            "n_unique_conf": int(n_unique),
            "conf_min": conf_min,
            "conf_max": conf_max,
            "conf_range": conf_range,
            "extreme_band_prop": extreme_band_prop,
            "bad_confidence": bool(bad_confidence)
        }

    if conf_mode == "discrete":
        extreme_band_prop = float(np.mean((confs == 1) | (confs == 4)))
        bad_confidence = (n_unique == 1) or (extreme_band_prop >= 0.90)

        return {
            "n_conf": int(len(confs)),
            "n_unique_conf": int(n_unique),
            "extreme_band_prop": extreme_band_prop,
            "bad_confidence": bool(bad_confidence)
        }

    raise ValueError(f"Unknown CONFIDENCE_MODE: {conf_mode}")


def _show_practice_feedback(win, bad_baseline, bad_confidence):
    if not (bad_baseline or bad_confidence):
        return

    if bad_baseline and bad_confidence:
        if CONFIDENCE_MODE == "continuous":
            message = (
                "Nous allons faire une courte série d’entraînement supplémentaire.\n\n"
                "Il faut encore mieux distinguer les essais avec un seul flash de ceux avec deux flashs.\n\n"
                "De plus, l’échelle de confiance n’a pas été utilisée de manière suffisamment variée.\n"
                "Essayez d’utiliser toute l’échelle entre 50 % et 100 % en fonction de votre degré réel de confiance, "
                "et pas seulement quelques valeurs extrêmes.\n\n"
                "Appuyez sur ESPACE pour continuer."
            )
        else:
            message = (
                "Nous allons faire une courte série d’entraînement supplémentaire.\n\n"
                "Il faut encore mieux distinguer les essais avec un seul flash de ceux avec deux flashs.\n\n"
                "Essayez aussi d’utiliser plusieurs niveaux de confiance, et pas seulement toujours la même réponse "
                "ou uniquement les extrêmes.\n\n"
                "Appuyez sur ESPACE pour continuer."
            )

    elif bad_baseline:
        message = (
            "Nous allons faire une courte série d’entraînement supplémentaire.\n\n"
            "Il faut encore mieux distinguer les essais avec un seul flash de ceux avec deux flashs.\n\n"
            "Appuyez sur ESPACE pour continuer."
        )

    else:
        if CONFIDENCE_MODE == "continuous":
            message = (
                "Nous allons faire une courte série d’entraînement supplémentaire.\n\n"
                "L’échelle de confiance n’a pas été utilisée de manière suffisamment variée.\n\n"
                "Essayez d’utiliser toute l’échelle entre 50 % et 100 % en fonction de votre degré réel de confiance, "
                "et pas seulement quelques valeurs extrêmes.\n\n"
                "Appuyez sur ESPACE pour continuer."
            )
        else:
            message = (
                "Nous allons faire une courte série d’entraînement supplémentaire.\n\n"
                "Essayez d’utiliser plusieurs niveaux de confiance, et pas seulement toujours la même réponse "
                "ou uniquement les extrêmes.\n\n"
                "Appuyez sur ESPACE pour continuer."
            )

    txt = _make_text(win, message)
    _wait_for_space(win, txt, "User aborted (escape) during practice feedback")


def _compute_lab_baseline_error_metrics(results):
    baseline = _compute_practice_baseline_metrics(results)

    if DESIGN_MODE == "av_fission_fusion_2soa":
        key_conditions = ["A1V1", "A1V1_A2V2"]
    else:
        key_conditions = ["V1", "V1V2"]

    acc_values = []
    err_values = {}

    for cond in key_conditions:
        acc = baseline.get(f"acc_{cond}", np.nan)
        err = 1.0 - acc if not np.isnan(acc) else np.nan

        acc_values.append(acc)
        err_values[f"err_{cond}"] = err

    valid_errs = [1.0 - x for x in acc_values if not np.isnan(x)]
    mean_err = float(np.mean(valid_errs)) if valid_errs else np.nan

    bad_baseline = any(
        not np.isnan(x) and x < 0.75
        for x in acc_values
    )

    out = {
        **baseline,
        **err_values,
        "mean_err": mean_err,
        "bad_baseline": bad_baseline,
    }

    return out


def _show_lab_baseline_supervision(win, metrics):
    corner_text = visual.TextStim(
        win,
        text=f"{metrics['mean_err'] * 100:.1f}",
        color="white",
        units="pix",
        height=24,
        pos=(-win.size[0] / 2 + 60, win.size[1] / 2 - 40),
        alignText="left",
        anchorHoriz="left",
        anchorVert="top",
        wrapWidth=200,
    )

    while True:
        win.flip(clearBuffer=True)
        corner_text.draw()
        win.flip()

        keys = event.getKeys(keyList=["o", "p", "escape"])
        if "escape" in keys:
            raise ExperimentAbort("User aborted (escape) during lab practice supervision")
        if "o" in keys:
            event.clearEvents()
            return "repeat"
        if "p" in keys:
            event.clearEvents()
            return "continue"


def run_practice(
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
):
    intro_text = _make_text(
        win,
        "Bloc d’entraînement\n\n"
        "Appuyez sur ESPACE pour commencer.",
        short=True
    )

    phase1_msg = _make_text(
        win,
        "Première partie de l’entraînement\n\n"
        "Pour l’instant, indiquez seulement combien de flashs vous avez perçus.\n\n"
        "Appuyez sur ESPACE pour commencer."
    )

    phase1_repeat_msg_lab = _make_text(
        win,
        "Relance manuelle du premier bloc d’entraînement\n\n"
        "Indiquez seulement combien de flashs vous avez perçus.\n\n"
        "Appuyez sur ESPACE pour recommencer.",
        short=False
    )

    phase2_repeat_msg_lab = _make_text(
        win,
        "Relance manuelle du deuxième bloc d’entraînement\n\n"
        "Appuyez sur ESPACE pour recommencer.",
        short=False
    )

    retry_msg = _make_text(
        win,
        "Série d’entraînement supplémentaire\n\n"
        "Appuyez sur ESPACE pour commencer.",
        short=True
    )

    end_msg = _make_text(
        win,
        "L’expérience va maintenant commencer.\n\n"
        "Appuyez sur ESPACE pour continuer.",
        short=True
    )

    if CONFIDENCE_MODE == "continuous":
        confidence_page = (
            "Après chaque réponse, vous devrez indiquer votre degré de confiance dans votre réponse.\n\n"
            "Vous utiliserez une échelle de confiance allant de 50 % à 100 %.\n\n"
            "50 % = vous avez répondu au hasard\n"
            "100 % = vous êtes certain que votre réponse est correcte\n\n"
            "Utilisez aussi les valeurs intermédiaires lorsque votre degré de confiance varie.\n"
            "N’utilisez pas seulement les valeurs extrêmes.\n\n"
            "Déplacez la souris sur la barre, puis cliquez pour valider.\n\n"
            "Appuyez sur ESPACE pour commencer l’entraînement."
        )
    elif CONFIDENCE_MODE == "discrete":
        confidence_page = (
            "Après chaque réponse, vous devrez indiquer votre degré de confiance dans votre réponse.\n\n"
            "Vous utiliserez une échelle de confiance allant de 1 à 4.\n\n"
            "1 = votre réponse vous semble proche du hasard\n"
            "4 = vous êtes certain que votre réponse est correcte\n\n"
            "Les valeurs 2 et 3 permettent d’indiquer des niveaux de confiance intermédiaires.\n\n"
            "Utilisez toute l’échelle lorsque votre degré de confiance varie, et pas seulement toujours la même réponse "
            "ou uniquement les extrêmes.\n\n"
            "Appuyez sur ESPACE pour commencer l’entraînement."
        )
    else:
        raise ValueError(f"Unknown CONFIDENCE_MODE: {CONFIDENCE_MODE}")

    confidence_msg = _make_text(win, confidence_page, align="left")

    _wait_for_space(win, intro_text, "User aborted (escape) during practice")

    show_flash_demo(
        win,
        fixation,
        flash_upper,
        flash_lower,
        flash_frames,
        isi_frames,
        frame_period
    )

    if LAB_MODE:
        first_pass_phase1 = True

        while True:
            if first_pass_phase1:
                _wait_for_space(win, phase1_msg, "User aborted (escape) during practice")
            else:
                _wait_for_space(win, phase1_repeat_msg_lab, "User aborted (escape) during practice")

            results_phase1 = _run_practice_block(
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
                frame_period,
                _make_practice_trials_balanced(n_reps_per_condition=4),
                ask_confidence=False
            )

            lab_metrics_phase1 = _compute_lab_baseline_error_metrics(results_phase1)
            action_phase1 = _show_lab_baseline_supervision(win, lab_metrics_phase1)

            if action_phase1 == "repeat":
                first_pass_phase1 = False
                continue
            break

        first_pass_phase2 = True

        while True:
            if first_pass_phase2:
                _wait_for_space(win, confidence_msg, "User aborted (escape) during practice")
            else:
                _wait_for_space(win, phase2_repeat_msg_lab, "User aborted (escape) during practice")

            results_phase2 = _run_practice_block(
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
                frame_period,
                _make_practice_trials_balanced(n_reps_per_condition=4),
                ask_confidence=True
            )

            lab_metrics_phase2 = _compute_lab_baseline_error_metrics(results_phase2)
            action_phase2 = _show_lab_baseline_supervision(win, lab_metrics_phase2)

            if action_phase2 == "repeat":
                first_pass_phase2 = False
                continue
            break

        _wait_for_space(win, end_msg, "User aborted (escape) during practice")
        return

    _wait_for_space(win, phase1_msg, "User aborted (escape) during practice")
    results_phase1 = _run_practice_block(
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
        frame_period,
        _make_practice_trials_balanced(n_reps_per_condition=4),
        ask_confidence=False
    )

    _wait_for_space(win, confidence_msg, "User aborted (escape) during practice")
    results_phase2 = _run_practice_block(
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
        frame_period,
        _make_practice_trials_balanced(n_reps_per_condition=4),
        ask_confidence=True
    )

    all_results = results_phase1 + results_phase2
    baseline_metrics = _compute_practice_baseline_metrics(all_results)

    if DESIGN_MODE == "av_fission_fusion_2soa":
        baseline_accuracy_keys = ["acc_A1V1", "acc_A1V1_A2V2"]
    else:
        baseline_accuracy_keys = ["acc_V1", "acc_V1V2"]

    bad_baseline = any(
        not np.isnan(accuracy) and accuracy < 0.75
        for accuracy in (
            baseline_metrics.get(key, np.nan)
            for key in baseline_accuracy_keys
        )
    )

    confidence_metrics = _compute_practice_confidence_metrics(
        results_phase2,
        CONFIDENCE_MODE
    )
    bad_confidence = confidence_metrics["bad_confidence"]

    if bad_baseline or bad_confidence:
        _show_practice_feedback(win, bad_baseline, bad_confidence)

        if bad_baseline:
            show_flash_demo(
                win,
                fixation,
                flash_upper,
                flash_lower,
                flash_frames,
                isi_frames,
                frame_period
            )

        if bad_confidence:
            _wait_for_space(win, confidence_msg, "User aborted (escape) during practice")

        _wait_for_space(win, retry_msg, "User aborted (escape) during practice")

        retry_trials = (
            _make_practice_trials_baseline_weighted()
            if bad_baseline
            else _make_practice_trials_balanced(n_reps_per_condition=4)
        )

        _run_practice_block(
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
            frame_period,
            retry_trials,
            ask_confidence=True
        )

    _wait_for_space(win, end_msg, "User aborted (escape) during practice")
