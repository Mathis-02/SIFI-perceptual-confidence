# ============================================================
# Hierarchical meta-d analysis for the short-SOA fission discrimination.
# Run from the analyses/ directory.
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
  library(tibble)
  library(brms)
  library(hmetad)
  library(posterior)
  library(bayesplot)
})


PROJECT_ROOT <- getwd()

DATA_FILE <- file.path(
  PROJECT_ROOT,
  "data",
  "processed",
  "model_ready_trials.csv"
)

OUT_DIR <- file.path(
  PROJECT_ROOT,
  "outputs",
  "tables",
  "hmetad_short"
)

REPORT_DIR <- file.path(
  PROJECT_ROOT,
  "outputs",
  "reports"
)

MODEL_DIR <- file.path(
  PROJECT_ROOT,
  "outputs",
  "models"
)

dir.create(OUT_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(REPORT_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(MODEL_DIR, recursive = TRUE, showWarnings = FALSE)

K_CONFIDENCE <- 4L

CONFIDENCE_BINNING <- "participant_quantiles"

CHAINS <- 4L
CORES <- min(4L, parallel::detectCores())
ITER <- 4000L
WARMUP <- 2000L
SEED <- 20260615L


if (!file.exists(DATA_FILE)) {
  stop(
    paste0(
      "Fichier introuvable : ", DATA_FILE, "\n",
      "Lance d'abord : python scripts/01_prepare_data.py"
    )
  )
}

required_packages <- c("hmetad", "brms", "posterior", "bayesplot")
missing_packages <- required_packages[
  !vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)
]

if (length(missing_packages) > 0) {
  stop(
    paste0(
      "Packages R manquants : ",
      paste(missing_packages, collapse = ", "),
      "\nInstalle-les avec :\n",
      "install.packages(c(",
      paste(sprintf('"%s"', missing_packages), collapse = ", "),
      "))"
    )
  )
}


raw <- read_csv(DATA_FILE, show_col_types = FALSE)

required_columns <- c(
  "participant",
  "base_condition",
  "soa_type",
  "response2",
  "confidence"
)

missing_columns <- setdiff(required_columns, names(raw))

if (length(missing_columns) > 0) {
  stop(
    paste0(
      "Missing required columns in model_ready_trials.csv: ",
      paste(missing_columns, collapse = ", ")
    )
  )
}

dat <- raw %>%
  mutate(
    participant = factor(participant),
    base_condition = as.character(base_condition),
    soa_type = as.character(soa_type),
    response2 = as.integer(response2),
    confidence = as.numeric(confidence)
  ) %>%
  filter(
    soa_type == "short",
    base_condition %in% c("A1V1_A2", "A1V1_A2V2"),
    response2 %in% c(0L, 1L),
    is.finite(confidence)
  ) %>%
  mutate(
    stimulus = if_else(
      base_condition == "A1V1_A2",
      0L,
      1L
    ),
    response = response2,
    correct = as.integer(stimulus == response)
  ) %>%
  droplevels()

if (nrow(dat) == 0) {
  stop("No trials matching the short-SOA conditions were found.")
}


make_quantile_bins <- function(x, K = 4L) {
  r <- rank(x, ties.method = "average", na.last = "keep")
  p <- (r - 1) / max(1, sum(!is.na(r)) - 1)

  out <- floor(p * K) + 1L
  out[out > K] <- K
  as.integer(out)
}

make_fixed_bins <- function(x) {
  cut(
    x,
    breaks = c(-Inf, 62.5, 75, 87.5, Inf),
    labels = 1:4,
    include.lowest = TRUE,
    right = FALSE
  ) %>%
    as.character() %>%
    as.integer()
}

if (CONFIDENCE_BINNING == "participant_quantiles") {
  dat <- dat %>%
    group_by(participant) %>%
    mutate(
      confidence_ord = make_quantile_bins(confidence, K_CONFIDENCE)
    ) %>%
    ungroup()
} else if (CONFIDENCE_BINNING == "fixed_width") {
  dat <- dat %>%
    mutate(
      confidence_ord = make_fixed_bins(confidence)
    )
} else {
  stop(
    "CONFIDENCE_BINNING doit être 'participant_quantiles' ou 'fixed_width'."
  )
}

if (!all(dat$confidence_ord %in% seq_len(K_CONFIDENCE))) {
  stop("Confidence discretization produced invalid values.")
}

dat <- dat %>%
  mutate(
    confidence_raw = confidence,
    confidence = as.integer(confidence_ord)
  )


type1_counts <- dat %>%
  count(participant, stimulus, response, name = "n") %>%
  complete(
    participant,
    stimulus = 0:1,
    response = 0:1,
    fill = list(n = 0L)
  ) %>%
  mutate(
    cell = case_when(
      stimulus == 0 & response == 0 ~ "correct_rejection",
      stimulus == 0 & response == 1 ~ "false_alarm",
      stimulus == 1 & response == 0 ~ "miss",
      stimulus == 1 & response == 1 ~ "hit"
    )
  ) %>%
  select(participant, cell, n) %>%
  pivot_wider(
    names_from = cell,
    values_from = n,
    values_fill = 0L
  ) %>%
  mutate(
    total = correct_rejection + false_alarm + miss + hit,
    has_all_type1_cells = (
      correct_rejection > 0 &
      false_alarm > 0 &
      miss > 0 &
      hit > 0
    )
  )

confidence_counts <- dat %>%
  count(participant, confidence_ord, name = "n") %>%
  complete(
    participant,
    confidence_ord = seq_len(K_CONFIDENCE),
    fill = list(n = 0L)
  )

trial_summary <- dat %>%
  group_by(participant) %>%
  summarise(
    n_trials = n(),
    n_stimulus_0 = sum(stimulus == 0),
    n_stimulus_1 = sum(stimulus == 1),
    n_response_0 = sum(response == 0),
    n_response_1 = sum(response == 1),
    accuracy = mean(correct),
    mean_confidence = mean(confidence_raw),
    .groups = "drop"
  ) %>%
  left_join(type1_counts, by = "participant")

write_csv(
  dat,
  file.path(OUT_DIR, "hmetad_short_trial_level_data.csv")
)

write_csv(
  trial_summary,
  file.path(OUT_DIR, "hmetad_short_type1_cell_counts.csv")
)

write_csv(
  confidence_counts,
  file.path(OUT_DIR, "hmetad_short_confidence_bin_counts.csv")
)


threshold_parameters <- hmetad::metac2_parameters(K = K_CONFIDENCE)

distributional_formula <- paste0(
  "dprime + c + ",
  paste(threshold_parameters, collapse = " + "),
  " ~ 1 + (1 || participant)"
)

model_formula <- brms::bf(
  as.formula("N ~ 1 + (1 || participant)"),
  as.formula(distributional_formula)
)

priors <- (
  brms::prior(normal(0, 1), class = Intercept) +
  brms::prior(student_t(3, 0, 0.5), class = sd)
)

message("Ajustement du modèle HMeta-d...")
message("Cette étape peut prendre plusieurs minutes lors de la première compilation.")

fit <- hmetad::fit_metad(
  formula = model_formula,
  data = dat,
  K = K_CONFIDENCE,
  init = "0",
  prior = priors,
  chains = CHAINS,
  cores = CORES,
  iter = ITER,
  warmup = WARMUP,
  seed = SEED,
  control = list(
    adapt_delta = 0.99,
    max_treedepth = 15
  ),
  refresh = 100
)

saveRDS(
  fit,
  file.path(MODEL_DIR, "hmetad_short_fission_congruent.rds")
)


draws <- posterior::as_draws_df(fit)

if (!"b_Intercept" %in% names(draws)) {
  stop(
    "Le paramètre b_Intercept n'a pas été trouvé dans les sorties du modèle."
  )
}

group_draws <- tibble(
  log_M = draws$b_Intercept,
  M_ratio = exp(draws$b_Intercept)
)

summarise_draws <- function(x) {
  tibble(
    posterior_mean = mean(x),
    posterior_median = median(x),
    posterior_sd = sd(x),
    ci_2.5 = quantile(x, 0.025),
    ci_97.5 = quantile(x, 0.975),
    probability_above_0 = mean(x > 0),
    probability_above_1 = mean(x > 1)
  )
}

group_log_M_summary <- summarise_draws(group_draws$log_M) %>%
  mutate(parameter = "log_M") %>%
  select(parameter, everything())

group_M_summary <- summarise_draws(group_draws$M_ratio) %>%
  mutate(parameter = "M_ratio") %>%
  select(parameter, everything())

group_summary <- bind_rows(
  group_log_M_summary,
  group_M_summary
)

write_csv(
  group_summary,
  file.path(OUT_DIR, "hmetad_short_group_estimates.csv")
)


model_summary <- summary(fit)

capture.output(
  model_summary,
  file = file.path(REPORT_DIR, "hmetad_short_model_summary.txt")
)

diagnostics <- posterior::summarise_draws(
  posterior::as_draws_array(fit),
  "mean",
  "sd",
  "rhat",
  "ess_bulk",
  "ess_tail"
)

write_csv(
  diagnostics,
  file.path(OUT_DIR, "hmetad_short_convergence_diagnostics.csv")
)

np <- brms::nuts_params(fit)

n_divergent <- np %>%
  filter(Parameter == "divergent__") %>%
  summarise(n = sum(Value)) %>%
  pull(n)

max_rhat <- max(diagnostics$rhat, na.rm = TRUE)
min_bulk_ess <- min(diagnostics$ess_bulk, na.rm = TRUE)
min_tail_ess <- min(diagnostics$ess_tail, na.rm = TRUE)

diagnostic_report <- c(
  "HMeta-d — SOA court",
  "===================",
  "",
  paste0("Participants: ", n_distinct(dat$participant)),
  paste0("Essais : ", nrow(dat)),
  paste0("Méthode de discrétisation : ", CONFIDENCE_BINNING),
  paste0("Nombre de catégories de confiance : ", K_CONFIDENCE),
  "",
  paste0("Divergences : ", n_divergent),
  paste0("Rhat maximal : ", sprintf("%.4f", max_rhat)),
  paste0("ESS bulk minimal : ", sprintf("%.1f", min_bulk_ess)),
  paste0("ESS tail minimal : ", sprintf("%.1f", min_tail_ess)),
  "",
  paste0(
    "M-ratio moyen postérieur : ",
    sprintf("%.3f", mean(group_draws$M_ratio))
  ),
  paste0(
    "IC crédible 95 % du M-ratio : [",
    sprintf("%.3f", quantile(group_draws$M_ratio, 0.025)),
    ", ",
    sprintf("%.3f", quantile(group_draws$M_ratio, 0.975)),
    "]"
  ),
  paste0(
    "P(M-ratio > 1) : ",
    sprintf("%.3f", mean(group_draws$M_ratio > 1))
  ),
  "",
  "Interprétation diagnostique recommandée :",
  if (n_divergent == 0) {
    "- aucune divergence ;"
  } else {
    paste0("- ", n_divergent, " transition(s) divergente(s) détectée(s) ;")
  },
  "- Rhat <= 1.01 ;",
  "- ESS suffisamment élevés ;",
  "- inspection visuelle des chaînes."
)

writeLines(
  diagnostic_report,
  file.path(REPORT_DIR, "hmetad_short_diagnostic_report.txt")
)


pdf(
  file.path(
    PROJECT_ROOT,
    "outputs",
    "figures",
    "diagnostics",
    "hmetad_short_traceplots.pdf"
  ),
  width = 10,
  height = 7
)

print(
  bayesplot::mcmc_trace(
    posterior::as_draws_array(fit),
    pars = c("b_Intercept", "b_dprime_Intercept", "b_c_Intercept")
  )
)

dev.off()


cat("\nHMeta-d terminé.\n")
cat("Participants:", n_distinct(dat$participant), "\n")
cat("Essais :", nrow(dat), "\n")
cat(
  "M-ratio moyen postérieur :",
  sprintf("%.3f", mean(group_draws$M_ratio)),
  "\n"
)
cat(
  "IC crédible 95 % : [",
  sprintf("%.3f", quantile(group_draws$M_ratio, 0.025)),
  ", ",
  sprintf("%.3f", quantile(group_draws$M_ratio, 0.975)),
  "]\n",
  sep = ""
)
cat("Divergences :", n_divergent, "\n")
cat("Rhat maximal :", sprintf("%.4f", max_rhat), "\n")
cat(
  "\nResults saved to:\n",
  OUT_DIR,
  "\n"
)
