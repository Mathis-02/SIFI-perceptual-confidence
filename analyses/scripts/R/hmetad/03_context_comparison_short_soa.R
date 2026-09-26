# ============================================================
# Direct hierarchical comparison of metacognitive efficiency across physical and fission contexts at the short SOA.
# Run from the repository root unless stated otherwise.
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
  "hmetad_context_comparison_short"
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

DIAG_DIR <- file.path(
  PROJECT_ROOT,
  "outputs",
  "figures",
  "diagnostics"
)

dir.create(OUT_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(REPORT_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(MODEL_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(DIAG_DIR, recursive = TRUE, showWarnings = FALSE)

K_CONFIDENCE <- 4L
CONFIDENCE_BINNING <- "participant_quantiles"

CHAINS <- 4L
CORES <- min(4L, parallel::detectCores())
ITER <- 5000L
WARMUP <- 2500L
SEED <- 20260620L

if (!file.exists(DATA_FILE)) {
  stop(paste0("Fichier introuvable : ", DATA_FILE))
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
      "Missing required columns: ",
      paste(missing_columns, collapse = ", ")
    )
  )
}

raw <- raw %>%
  mutate(
    participant = factor(participant),
    base_condition = as.character(base_condition),
    soa_type = as.character(soa_type),
    response2 = as.integer(response2),
    confidence = as.numeric(confidence),
    row_id = row_number()
  ) %>%
  filter(
    response2 %in% c(0L, 1L),
    is.finite(confidence)
  )


set.seed(SEED)

make_participant_data <- function(d) {

  p <- unique(d$participant)

  baseline <- d %>%
    filter(base_condition == "A1V1")

  fission <- d %>%
    filter(
      base_condition == "A1V1_A2",
      soa_type == "short"
    )

  congruent <- d %>%
    filter(
      base_condition == "A1V1_A2V2",
      soa_type == "short"
    ) %>%
    slice_sample(prop = 1)

  if (
    nrow(baseline) == 0 ||
    nrow(fission) == 0 ||
    nrow(congruent) < 2
  ) {
    return(NULL)
  }

  split_point <- floor(nrow(congruent) / 2)

  congruent_physical <- congruent %>%
    slice(seq_len(split_point))

  congruent_fission <- congruent %>%
    slice((split_point + 1):n())

  target_n <- min(
    nrow(baseline),
    nrow(fission),
    nrow(congruent_physical),
    nrow(congruent_fission)
  )

  if (target_n < 10) {
    warning(
      paste0(
        "Participant ", as.character(p),
        " : seulement ", target_n,
        " essais par cellule après équilibrage."
      )
    )
  }

  bind_rows(
    baseline %>%
      slice_sample(n = target_n) %>%
      mutate(
        context = "Physique",
        stimulus = 0L
      ),
    congruent_physical %>%
      slice_sample(n = target_n) %>%
      mutate(
        context = "Physique",
        stimulus = 1L
      ),
    fission %>%
      slice_sample(n = target_n) %>%
      mutate(
        context = "Fission",
        stimulus = 0L
      ),
    congruent_fission %>%
      slice_sample(n = target_n) %>%
      mutate(
        context = "Fission",
        stimulus = 1L
      )
  )
}

dat <- raw %>%
  group_split(participant) %>%
  lapply(make_participant_data) %>%
  bind_rows() %>%
  mutate(
    participant = droplevels(factor(participant)),
    context = factor(
      context,
      levels = c("Physique", "Fission")
    ),
    response = response2,
    correct = as.integer(stimulus == response)
  )

if (nrow(dat) == 0) {
  stop("No data remain after constructing the contexts.")
}

if (anyDuplicated(dat$row_id) > 0) {
  stop("Some trials were reused across contexts.")
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
      confidence_ord = make_quantile_bins(
        confidence,
        K_CONFIDENCE
      )
    ) %>%
    ungroup()
} else {
  dat <- dat %>%
    mutate(
      confidence_ord = make_fixed_bins(confidence)
    )
}

dat <- dat %>%
  mutate(
    confidence_raw = confidence,
    confidence = as.integer(confidence_ord)
  )


cell_counts <- dat %>%
  count(
    participant,
    context,
    stimulus,
    response,
    name = "n"
  ) %>%
  complete(
    participant,
    context,
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
  select(
    participant,
    context,
    cell,
    n
  ) %>%
  pivot_wider(
    names_from = cell,
    values_from = n,
    values_fill = 0L
  ) %>%
  mutate(
    total = (
      correct_rejection +
      false_alarm +
      miss +
      hit
    ),
    has_all_type1_cells = (
      correct_rejection > 0 &
      false_alarm > 0 &
      miss > 0 &
      hit > 0
    )
  )

trial_summary <- dat %>%
  group_by(
    participant,
    context
  ) %>%
  summarise(
    n_trials = n(),
    accuracy = mean(correct),
    response2_rate = mean(response),
    mean_confidence = mean(confidence_raw),
    .groups = "drop"
  ) %>%
  left_join(
    cell_counts,
    by = c("participant", "context")
  )

write_csv(
  dat,
  file.path(
    OUT_DIR,
    "hmetad_context_comparison_trial_data.csv"
  )
)

write_csv(
  trial_summary,
  file.path(
    OUT_DIR,
    "hmetad_context_comparison_cell_counts.csv"
  )
)


threshold_parameters <- hmetad::metac2_parameters(
  K = K_CONFIDENCE
)

distributional_formula <- paste0(
  "dprime + c + ",
  paste(
    threshold_parameters,
    collapse = " + "
  ),
  " ~ context + (1 || participant)"
)

model_formula <- brms::bf(
  as.formula(
    "N ~ context + (1 || participant)"
  ),
  as.formula(
    distributional_formula
  )
)

priors <- (
  brms::prior(
    normal(0, 1),
    class = Intercept
  ) +
  brms::prior(
    normal(0, 0.5),
    class = b
  ) +
  brms::prior(
    student_t(3, 0, 0.5),
    class = sd
  )
)

message("Ajustement du modèle HMeta-d commun...")
message("Cette étape peut être longue.")

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
    adapt_delta = 0.999,
    max_treedepth = 20
  ),
  refresh = 100
)

MODEL_PATH <- file.path(
  MODEL_DIR,
  "hmetad_context_comparison_short.rds"
)

saveRDS(
  fit,
  MODEL_PATH
)


draws <- posterior::as_draws_df(fit)

context_candidates <- grep(
  "^b_context",
  names(draws),
  value = TRUE
)

if (
  !"b_Intercept" %in% names(draws) ||
  length(context_candidates) == 0
) {
  stop(
    paste0(
      "Paramètres attendus non trouvés.\n",
      "Paramètres b_ disponibles :\n",
      paste(
        grep("^b_", names(draws), value = TRUE),
        collapse = "\n"
      )
    )
  )
}

context_name <- context_candidates[1]

posterior_results <- tibble(
  log_M_physique = draws$b_Intercept,
  log_ratio_M_fission_vs_physique = draws[[context_name]],
  M_physique = exp(log_M_physique),
  M_fission = exp(
    log_M_physique +
    log_ratio_M_fission_vs_physique
  ),
  ratio_M_fission_vs_physique = exp(
    log_ratio_M_fission_vs_physique
  ),
  difference_M = M_fission - M_physique
)

summarise_posterior <- function(x) {
  tibble(
    mean = mean(x),
    median = median(x),
    sd = sd(x),
    q025 = quantile(x, 0.025),
    q975 = quantile(x, 0.975)
  )
}

group_summary <- bind_rows(
  summarise_posterior(
    posterior_results$M_physique
  ) %>%
    mutate(parameter = "M_physique"),
  summarise_posterior(
    posterior_results$M_fission
  ) %>%
    mutate(parameter = "M_fission"),
  summarise_posterior(
    posterior_results$ratio_M_fission_vs_physique
  ) %>%
    mutate(parameter = "ratio_M_fission_vs_physique"),
  summarise_posterior(
    posterior_results$difference_M
  ) %>%
    mutate(parameter = "difference_M")
) %>%
  select(parameter, everything())

write_csv(
  group_summary,
  file.path(
    OUT_DIR,
    "hmetad_context_comparison_group_estimates.csv"
  )
)

probabilities <- tibble(
  probability_M_fission_lower_than_physical = mean(
    posterior_results$M_fission <
      posterior_results$M_physique
  ),
  probability_ratio_below_1 = mean(
    posterior_results$ratio_M_fission_vs_physique < 1
  ),
  probability_difference_below_0 = mean(
    posterior_results$difference_M < 0
  )
)

write_csv(
  probabilities,
  file.path(
    OUT_DIR,
    "hmetad_context_comparison_probabilities.csv"
  )
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
  file.path(
    OUT_DIR,
    "hmetad_context_comparison_diagnostics.csv"
  )
)

np <- brms::nuts_params(fit)

n_divergent <- np %>%
  filter(
    Parameter == "divergent__"
  ) %>%
  summarise(
    n = sum(Value)
  ) %>%
  pull(n)

max_rhat <- max(
  diagnostics$rhat,
  na.rm = TRUE
)

min_bulk_ess <- min(
  diagnostics$ess_bulk,
  na.rm = TRUE
)

min_tail_ess <- min(
  diagnostics$ess_tail,
  na.rm = TRUE
)

capture.output(
  summary(fit),
  file = file.path(
    REPORT_DIR,
    "hmetad_context_comparison_model_summary.txt"
  )
)

diagnostic_report <- c(
  "HMeta-d — comparaison directe des contextes au SOA court",
  "========================================================",
  "",
  paste0(
    "Participants: ",
    n_distinct(dat$participant)
  ),
  paste0(
    "Essais : ",
    nrow(dat)
  ),
  paste0(
    "Essais par cellule et participant : ",
    min(
      dat %>%
        count(
          participant,
          context,
          stimulus
        ) %>%
        pull(n)
    )
  ),
  "",
  paste0(
    "Divergences : ",
    n_divergent
  ),
  paste0(
    "Rhat maximal : ",
    sprintf("%.4f", max_rhat)
  ),
  paste0(
    "ESS bulk minimal : ",
    sprintf("%.1f", min_bulk_ess)
  ),
  paste0(
    "ESS tail minimal : ",
    sprintf("%.1f", min_tail_ess)
  ),
  "",
  paste0(
    "M physique moyen : ",
    sprintf(
      "%.3f",
      mean(posterior_results$M_physique)
    )
  ),
  paste0(
    "M fission moyen : ",
    sprintf(
      "%.3f",
      mean(posterior_results$M_fission)
    )
  ),
  paste0(
    "Ratio M fission / physique : ",
    sprintf(
      "%.3f",
      mean(
        posterior_results$ratio_M_fission_vs_physique
      )
    )
  ),
  paste0(
    "P(M fission < M physique) : ",
    sprintf(
      "%.3f",
      mean(
        posterior_results$M_fission <
          posterior_results$M_physique
      )
    )
  ),
  "",
  "Interprétation :",
  "- ratio < 1 : efficacité métacognitive plus faible en contexte fission ;",
  "- ratio = 1 : efficacité comparable ;",
  "- ratio > 1 : efficacité plus élevée en contexte fission ;",
  "",
  "Limite conceptuelle :",
  "les contextes diffèrent aussi par leur stimulus S1.",
  "Le coefficient de contexte n'isole donc pas une connaissance pure",
  "de l'origine illusoire du percept."
)

writeLines(
  diagnostic_report,
  file.path(
    REPORT_DIR,
    "hmetad_context_comparison_diagnostic_report.txt"
  )
)

pdf(
  file.path(
    DIAG_DIR,
    "hmetad_context_comparison_traceplots.pdf"
  ),
  width = 11,
  height = 7
)

print(
  bayesplot::mcmc_trace(
    posterior::as_draws_array(fit),
    pars = c(
      "b_Intercept",
      context_name,
      "b_dprime_Intercept",
      "b_c_Intercept"
    )
  )
)

dev.off()

cat("\nAnalysis completed.\n\n")
cat(
  "M physique : ",
  sprintf(
    "%.3f",
    mean(posterior_results$M_physique)
  ),
  "\n",
  sep = ""
)
cat(
  "M fission : ",
  sprintf(
    "%.3f",
    mean(posterior_results$M_fission)
  ),
  "\n",
  sep = ""
)
cat(
  "Ratio M fission / physique : ",
  sprintf(
    "%.3f",
    mean(
      posterior_results$ratio_M_fission_vs_physique
    )
  ),
  "\n",
  sep = ""
)
cat(
  "P(M fission < M physique) : ",
  sprintf(
    "%.3f",
    mean(
      posterior_results$M_fission <
        posterior_results$M_physique
    )
  ),
  "\n",
  sep = ""
)
cat(
  "Divergences : ",
  n_divergent,
  "\n",
  sep = ""
)
