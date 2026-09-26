# Data dictionary

The raw files in `data/trials/` contain one row per trial. `data/processed/model_ready_trials.csv` adds analysis variables without altering the raw files.

## Core identifiers and design variables

| Variable | Description |
|---|---|
| `participant` | Pseudonymized participant code |
| `block` | Experimental block number |
| `trial` | Trial number |
| `condition` | Full experimental condition label |
| `base_condition` | Base stimulus structure, e.g. `A1V1_A2` |
| `soa_type` | Standard, short, or baseline/no-SOA classification |
| `soa_ms` | Requested SOA in milliseconds |
| `position` | Flash position |

## Responses

| Variable | Description |
|---|---|
| `response` | Reported number of flashes |
| `response2` | Binary recoding, 1 for a two-flash report |
| `rt` | Perceptual response time in seconds |
| `correct_answer` | Number of physically presented flashes |
| `accuracy` | Trial correctness indicator |
| `illusion` | Trial-level illusion indicator |
| `illusion_type` | Fission, fusion, or none |
| `confidence` | Confidence rating from 50 to 100 |
| `rt_conf` | Confidence response time in seconds |

## Timing and quality-control variables

The remaining columns document programmed and measured event times, frame counts, audio scheduling proxies, dropped-frame indicators, total trial duration, and error messages. They are retained to support timing and data-quality audits.

## Derived analysis variables

| Variable | Description |
|---|---|
| `condition_cell` | Combined condition and SOA analysis factor |
| `matched_percept` | Report-matching indicator used in confidence analyses |
| `percept_origin` | Physical/congruent or illusory origin of the reported percept |
| `soa_ms_clean` | Cleaned numeric SOA variable |
