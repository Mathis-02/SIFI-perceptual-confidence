# ============================================================
# Exploratory associations between individual posterior M-ratios and fission-related outcomes.
# Run from the analyses/ directory.
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(posterior)
})

PROJECT_ROOT <- getwd()

candidate_model_files <- c(
  file.path(PROJECT_ROOT, "outputs", "models", "hmetad_congruent_baseline.rds"),
  file.path(PROJECT_ROOT, "outputs", "models", "hmetad_congruent_baseline", "hmetad_congruent_baseline.rds"),
  file.path(PROJECT_ROOT, "hmetad_congruent_baseline.rds")
)
MODEL_FILE <- candidate_model_files[file.exists(candidate_model_files)][1]
if (is.na(MODEL_FILE)) stop("Could not find hmetad_congruent_baseline.rds.")

candidate_data_files <- c(
  file.path(PROJECT_ROOT, "data", "processed", "model_ready_trials.csv"),
  file.path(PROJECT_ROOT, "outputs", "tables", "model_ready_trials.csv"),
  file.path(PROJECT_ROOT, "model_ready_trials.csv")
)
DATA_FILE <- candidate_data_files[file.exists(candidate_data_files)][1]
if (is.na(DATA_FILE)) stop("Could not find model_ready_trials.csv.")

FIG_DIR <- file.path(PROJECT_ROOT, "outputs", "figures", "backup", "hmetad_individual_associations")
TABLE_DIR <- file.path(PROJECT_ROOT, "outputs", "tables", "hmetad_individual_associations")
REPORT_DIR <- file.path(PROJECT_ROOT, "outputs", "reports")
dir.create(FIG_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(TABLE_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(REPORT_DIR, recursive = TRUE, showWarnings = FALSE)


fit <- readRDS(MODEL_FILE)
draws <- posterior::as_draws_df(fit)
draw_names <- names(draws)

fixed_candidates <- c("b_Intercept", "b_mu_Intercept", "b_N_Intercept")
fixed_name <- fixed_candidates[fixed_candidates %in% draw_names][1]
if (is.na(fixed_name)) {
  stop(paste0(
    "Intercept fixe du M-ratio introuvable.\nVariables contenant Intercept :\n",
    paste(grep("Intercept", draw_names, value = TRUE), collapse = "\n")
  ))
}

random_names <- grep("^r_participant\\[[^,]+,Intercept\\]$", draw_names, value = TRUE)
if (length(random_names) == 0) {
  stop(paste0(
    "Effets individuels du M-ratio introuvables.\nVariables r_participant disponibles :\n",
    paste(grep("^r_participant", draw_names, value = TRUE), collapse = "\n")
  ))
}

extract_id <- function(x) sub(".*\\[([^,]+),Intercept\\]$", "\\1", x)

participant_draws <- bind_rows(lapply(random_names, function(rn) {
  tibble(
    .draw = draws$.draw,
    participant = extract_id(rn),
    mratio = exp(draws[[fixed_name]] + draws[[rn]])
  )
}))

individual_mratio <- participant_draws %>%
  group_by(participant) %>%
  summarise(
    mratio_mean = mean(mratio),
    mratio_median = median(mratio),
    mratio_q025 = quantile(mratio, 0.025),
    mratio_q975 = quantile(mratio, 0.975),
    p_mratio_gt_1 = mean(mratio > 1),
    .groups = "drop"
  )

normalise_id <- function(x) tolower(gsub("[^[:alnum:]]", "", as.character(x)))
individual_mratio <- individual_mratio %>%
  mutate(participant_key = normalise_id(participant))

write_csv(individual_mratio, file.path(TABLE_DIR, "mratio_individuel_posterieur.csv"))


raw <- read_csv(DATA_FILE, show_col_types = FALSE)
needed <- c("participant", "base_condition", "soa_type", "response2", "confidence")
missing <- setdiff(needed, names(raw))
if (length(missing) > 0) stop(paste("Missing required columns:", paste(missing, collapse = ", ")))

dat <- raw %>%
  mutate(
    participant = as.character(participant),
    participant_key = normalise_id(participant),
    base_condition = as.character(base_condition),
    soa_type = as.character(soa_type),
    response2 = as.integer(response2),
    confidence = as.numeric(confidence)
  ) %>%
  filter(response2 %in% c(0L, 1L), is.finite(confidence))

fission_by_soa <- dat %>%
  filter(base_condition == "A1V1_A2", soa_type %in% c("standard", "short")) %>%
  group_by(participant_key, soa_type) %>%
  summarise(n_trials = n(), value = mean(response2), .groups = "drop") %>%
  mutate(
    soa = recode(soa_type, standard = "SOA standard", short = "SOA court"),
    outcome = "Taux de fission"
  ) %>%
  select(participant_key, soa, outcome, value, n_1 = n_trials)

fission_pooled <- dat %>%
  filter(base_condition == "A1V1_A2", soa_type %in% c("standard", "short")) %>%
  group_by(participant_key) %>%
  summarise(n_trials = n(), value = mean(response2), .groups = "drop") %>%
  mutate(soa = "SOA regroupés", outcome = "Taux de fission") %>%
  select(participant_key, soa, outcome, value, n_1 = n_trials)

conf_by_soa <- dat %>%
  filter(base_condition == "A1V1_A2", soa_type %in% c("standard", "short"), response2 == 1L) %>%
  group_by(participant_key, soa_type) %>%
  summarise(n_trials = n(), value = mean(confidence), .groups = "drop") %>%
  mutate(
    soa = recode(soa_type, standard = "SOA standard", short = "SOA court"),
    outcome = "Confiance associée aux fissions"
  ) %>%
  select(participant_key, soa, outcome, value, n_1 = n_trials)

conf_pooled <- dat %>%
  filter(base_condition == "A1V1_A2", soa_type %in% c("standard", "short"), response2 == 1L) %>%
  group_by(participant_key) %>%
  summarise(n_trials = n(), value = mean(confidence), .groups = "drop") %>%
  mutate(soa = "SOA regroupés", outcome = "Confiance associée aux fissions") %>%
  select(participant_key, soa, outcome, value, n_1 = n_trials)

contrast <- dat %>%
  filter(
    base_condition %in% c("A1V1_A2", "A1V1_A2V2"),
    soa_type %in% c("standard", "short"),
    response2 == 1L
  ) %>%
  mutate(origin = if_else(base_condition == "A1V1_A2", "Illusoire", "Congruente")) %>%
  group_by(participant_key, soa_type, origin) %>%
  summarise(n_trials = n(), mean_confidence = mean(confidence), .groups = "drop") %>%
  pivot_wider(
    names_from = origin,
    values_from = c(n_trials, mean_confidence),
    names_sep = "__"
  ) %>%
  mutate(
    value = `mean_confidence__Illusoire` - `mean_confidence__Congruente`,
    soa = recode(soa_type, standard = "SOA standard", short = "SOA court"),
    outcome = "Contraste de confiance illusoire - congruente",
    n_1 = `n_trials__Illusoire`,
    n_2 = `n_trials__Congruente`
  ) %>%
  select(participant_key, soa, outcome, value, n_1, n_2)

analysis_data <- bind_rows(
  mutate(fission_pooled, n_2 = NA_real_),
  mutate(fission_by_soa, n_2 = NA_real_),
  mutate(conf_pooled, n_2 = NA_real_),
  mutate(conf_by_soa, n_2 = NA_real_),
  contrast
) %>%
  left_join(
    individual_mratio %>%
      select(participant, participant_key, mratio_mean, mratio_median, mratio_q025, mratio_q975),
    by = "participant_key"
  ) %>%
  filter(is.finite(value), is.finite(mratio_mean)) %>%
  mutate(
    soa = factor(soa, levels = c("SOA regroupés", "SOA standard", "SOA court")),
    outcome = factor(
      outcome,
      levels = c(
        "Taux de fission",
        "Confiance associée aux fissions",
        "Contraste de confiance illusoire - congruente"
      )
    )
  )

write_csv(analysis_data, file.path(TABLE_DIR, "donnees_associations_mratio_fission.csv"))


safe_spearman <- function(x, y) {
  keep <- complete.cases(x, y)
  x <- x[keep]
  y <- y[keep]
  if (length(x) < 3 || sd(x) == 0 || sd(y) == 0) {
    return(tibble(n = length(x), rho = NA_real_, p_value = NA_real_))
  }
  test <- suppressWarnings(cor.test(x, y, method = "spearman", exact = FALSE))
  tibble(n = length(x), rho = unname(test$estimate), p_value = test$p.value)
}

correlation_results <- analysis_data %>%
  group_by(outcome, soa) %>%
  group_modify(~ safe_spearman(.x$mratio_mean, .x$value)) %>%
  ungroup()

write_csv(correlation_results, file.path(TABLE_DIR, "correlations_mratio_mesures_fission.csv"))

leave_one_out <- analysis_data %>%
  group_by(outcome, soa) %>%
  group_modify(function(.x, .y) {
    ids <- unique(.x$participant_key)
    bind_rows(lapply(ids, function(id) {
      d <- filter(.x, participant_key != id)
      safe_spearman(d$mratio_mean, d$value) %>%
        mutate(participant_excluded = id)
    }))
  }) %>%
  ungroup()

write_csv(leave_one_out, file.path(TABLE_DIR, "sensibilite_leave_one_out.csv"))

loo_summary <- leave_one_out %>%
  group_by(outcome, soa) %>%
  summarise(
    rho_min = min(rho, na.rm = TRUE),
    rho_max = max(rho, na.rm = TRUE),
    p_min = min(p_value, na.rm = TRUE),
    p_max = max(p_value, na.rm = TRUE),
    n_significant = sum(p_value < .05, na.rm = TRUE),
    n_analyses = sum(is.finite(p_value)),
    .groups = "drop"
  )

write_csv(loo_summary, file.path(TABLE_DIR, "resume_sensibilite_leave_one_out.csv"))


format_p <- function(p) {
  ifelse(is.na(p), "p = NA", ifelse(p < .001, "p < .001", paste0("p = ", sprintf("%.3f", p))))
}

annotations <- correlation_results %>%
  mutate(label = paste0("rho = ", sprintf("%.2f", rho), "\n", format_p(p_value)))

make_plot <- function(outcome_name, file_stub, y_label) {
  d <- filter(analysis_data, outcome == outcome_name)
  a <- filter(annotations, outcome == outcome_name)

  x_min <- min(d$mratio_q025, na.rm = TRUE)
  x_max <- max(d$mratio_q975, na.rm = TRUE)
  y_min <- min(d$value, na.rm = TRUE)
  y_max <- max(d$value, na.rm = TRUE)
  x_pad <- max(0.02, 0.08 * (x_max - x_min))
  y_pad <- max(0.02, 0.08 * (y_max - y_min))

  a <- a %>% mutate(x = x_min + x_pad, y = y_max + y_pad)

  p <- ggplot(d, aes(x = mratio_mean, y = value)) +
    geom_smooth(method = "lm", formula = y ~ x, se = TRUE,
                colour = "grey45", fill = "grey85", linewidth = 0.8) +
    geom_segment(aes(x = mratio_q025, xend = mratio_q975, yend = value),
                 colour = "grey55", linewidth = 0.55) +
    geom_point(shape = 21, fill = "white", colour = "black", size = 3, stroke = 0.9) +
    geom_text(aes(label = participant), nudge_y = y_pad * 0.35,
              size = 3, check_overlap = TRUE) +
    geom_text(data = a, aes(x = x, y = y, label = label),
              inherit.aes = FALSE, hjust = 0, vjust = 1, size = 3.8) +
    facet_wrap(~ soa, scales = "free_y", nrow = 1) +
    labs(
      title = paste0("Association entre efficacité métacognitive et ", tolower(outcome_name)),
      subtitle = paste0(
        "Chaque point représente un participant. Les barres horizontales représentent ",
        "l'IC crédible à 95 % du M-ratio individuel."
      ),
      x = "M-ratio individuel dans la discrimination congruente",
      y = y_label,
      caption = paste0(
        "Corrélations de Spearman exploratoires, N = 9. ",
        "Les M-ratios sont des estimations postérieures régularisées."
      )
    ) +
    theme_classic(base_size = 12) +
    theme(
      plot.title = element_text(face = "bold", size = 13.5),
      strip.background = element_blank(),
      strip.text = element_text(face = "bold"),
      plot.caption = element_text(size = 8.5, hjust = 0)
    )

  ggsave(file.path(FIG_DIR, paste0(file_stub, ".pdf")), p,
         width = 11.5, height = 5, device = cairo_pdf)
  ggsave(file.path(FIG_DIR, paste0(file_stub, ".png")), p,
         width = 11.5, height = 5, dpi = 300)
}

make_plot("Taux de fission", "association_mratio_taux_fission", "Taux d'illusion de fission")
make_plot("Confiance associée aux fissions", "association_mratio_confiance_fission", "Confiance moyenne associée aux fissions (%)")
make_plot("Contraste de confiance illusoire - congruente", "association_mratio_contraste_confiance", "Confiance illusoire - confiance congruente (points)")


report <- capture.output({
  cat("Associations exploratoires entre M-ratio individuel et mesures de fission\n")
  cat("=====================================================================\n\n")
  cat("Modèle HMeta-d : ", MODEL_FILE, "\n", sep = "")
  cat("Données : ", DATA_FILE, "\n\n", sep = "")
  cat("M-ratios individuels\n")
  print(individual_mratio)
  cat("\nCorrélations principales\n")
  print(correlation_results)
  cat("\nRésumé leave-one-out\n")
  print(loo_summary)
  cat("\nAttention : analyses exploratoires avec N = 9, multiplicité des tests, ")
  cat("régularisation hiérarchique et divergences précédemment observées.\n")
})

writeLines(report, file.path(REPORT_DIR, "rapport_associations_mratio_fission.txt"))

cat("\nAnalysis completed.\n\n")
print(correlation_results)
cat("\nRésultats : ", TABLE_DIR, "\n", sep = "")
cat("Figures : ", FIG_DIR, "\n", sep = "")
