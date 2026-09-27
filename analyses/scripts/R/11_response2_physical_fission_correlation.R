# ============================================================
# Participant-level association between correct two-flash reports and fission rates.
# Run from the analyses/ directory.
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(scales)
})

PROJECT_ROOT <- getwd()

candidate_data_files <- c(
  file.path(PROJECT_ROOT, "data", "processed", "model_ready_trials.csv"),
  file.path(PROJECT_ROOT, "outputs", "tables", "model_ready_trials.csv"),
  file.path(PROJECT_ROOT, "model_ready_trials.csv")
)

existing_files <- candidate_data_files[file.exists(candidate_data_files)]

if (length(existing_files) == 0) {
  stop("Could not find model_ready_trials.csv.")
}

DATA_FILE <- existing_files[1]

FIG_DIR <- file.path(PROJECT_ROOT, "outputs", "figures", "backup")
TABLE_DIR <- file.path(PROJECT_ROOT, "outputs", "tables", "correlations")
REPORT_DIR <- file.path(PROJECT_ROOT, "outputs", "reports")

dir.create(FIG_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(TABLE_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(REPORT_DIR, recursive = TRUE, showWarnings = FALSE)

raw <- read_csv(DATA_FILE, show_col_types = FALSE)

required_columns <- c("participant", "base_condition", "soa_type", "response2")
missing_columns <- setdiff(required_columns, names(raw))

if (length(missing_columns) > 0) {
  stop(paste("Missing required columns:", paste(missing_columns, collapse = ", ")))
}

dat <- raw %>%
  mutate(
    participant = factor(participant),
    base_condition = as.character(base_condition),
    soa_type = as.character(soa_type),
    response2 = as.integer(response2)
  ) %>%
  filter(
    base_condition %in% c("A1V1_A2", "A1V1_A2V2"),
    soa_type %in% c("standard", "short"),
    response2 %in% c(0L, 1L)
  )

make_rates <- function(data, label) {
  data %>%
    group_by(participant, base_condition) %>%
    summarise(
      n_trials = n(),
      n_response2 = sum(response2),
      response2_rate = mean(response2),
      .groups = "drop"
    ) %>%
    mutate(
      mesure = if_else(
        base_condition == "A1V1_A2V2",
        "Deux flashs physiques",
        "Illusion de fission"
      )
    ) %>%
    select(participant, mesure, n_trials, n_response2, response2_rate) %>%
    pivot_wider(
      names_from = mesure,
      values_from = c(n_trials, n_response2, response2_rate),
      names_sep = "__"
    ) %>%
    rename(
      n_physical = `n_trials__Deux flashs physiques`,
      n_illusion = `n_trials__Illusion de fission`,
      n_response2_physical = `n_response2__Deux flashs physiques`,
      n_response2_illusion = `n_response2__Illusion de fission`,
      physical_response2_rate = `response2_rate__Deux flashs physiques`,
      fission_rate = `response2_rate__Illusion de fission`
    ) %>%
    mutate(analysis = label)
}

rates_pooled <- make_rates(dat, "SOA regroupés")
rates_standard <- make_rates(filter(dat, soa_type == "standard"), "SOA standard")
rates_short <- make_rates(filter(dat, soa_type == "short"), "SOA court")

correlation_data <- bind_rows(
  rates_pooled,
  rates_standard,
  rates_short
) %>%
  mutate(
    analysis = factor(
      analysis,
      levels = c("SOA regroupés", "SOA standard", "SOA court")
    )
  ) %>%
  arrange(analysis, participant)

write_csv(
  correlation_data,
  file.path(TABLE_DIR, "taux_reponse2_physique_et_illusion_fission_par_participant.csv")
)

safe_cor <- function(x, y, method) {
  keep <- complete.cases(x, y)
  x <- x[keep]
  y <- y[keep]

  if (length(x) < 3 || sd(x) == 0 || sd(y) == 0) {
    return(tibble(
      n = length(x),
      estimate = NA_real_,
      statistic = NA_real_,
      p_value = NA_real_
    ))
  }

  test <- if (method == "spearman") {
    suppressWarnings(cor.test(x, y, method = "spearman", exact = FALSE))
  } else {
    cor.test(x, y, method = "pearson")
  }

  tibble(
    n = length(x),
    estimate = unname(test$estimate),
    statistic = unname(test$statistic),
    p_value = test$p.value
  )
}

results <- correlation_data %>%
  group_by(analysis) %>%
  group_modify(~ bind_rows(
    safe_cor(.x$physical_response2_rate, .x$fission_rate, "spearman") %>%
      mutate(method = "Spearman"),
    safe_cor(.x$physical_response2_rate, .x$fission_rate, "pearson") %>%
      mutate(method = "Pearson")
  )) %>%
  ungroup() %>%
  select(analysis, method, n, estimate, statistic, p_value)

write_csv(
  results,
  file.path(TABLE_DIR, "correlations_reponse2_physique_illusion_fission.csv")
)

format_p <- function(p) {
  ifelse(
    is.na(p),
    "p = NA",
    ifelse(p < .001, "p < .001", paste0("p = ", sprintf("%.3f", p)))
  )
}

annotations <- results %>%
  filter(method == "Spearman") %>%
  mutate(
    label = paste0("rho = ", sprintf("%.2f", estimate), "\n", format_p(p_value)),
    x = 0.05,
    y = 0.95
  )

p <- ggplot(
  correlation_data,
  aes(x = physical_response2_rate, y = fission_rate)
) +
  geom_smooth(
    method = "lm",
    formula = y ~ x,
    se = TRUE,
    colour = "grey45",
    fill = "grey85",
    linewidth = 0.8
  ) +
  geom_point(
    shape = 21,
    fill = "white",
    colour = "black",
    size = 3,
    stroke = 0.9
  ) +
  geom_text(
    aes(label = participant),
    nudge_y = 0.025,
    size = 3,
    check_overlap = TRUE
  ) +
  geom_text(
    data = annotations,
    aes(x = x, y = y, label = label),
    inherit.aes = FALSE,
    hjust = 0,
    vjust = 1,
    size = 3.8
  ) +
  facet_wrap(~ analysis, nrow = 1) +
  scale_x_continuous(
    limits = c(0, 1),
    breaks = seq(0, 1, 0.2),
    labels = label_percent(accuracy = 1)
  ) +
  scale_y_continuous(
    limits = c(0, 1),
    breaks = seq(0, 1, 0.2),
    labels = label_percent(accuracy = 1)
  ) +
  labs(
    title = "Association entre la détection de deux flashs physiques et l'illusion de fission",
    subtitle = "Chaque point représente un participant ; la statistic affichée est la corrélation de Spearman.",
    x = "Réponses « 2 flashs » dans A1V1_A2V2",
    y = "Taux d'illusion de fission dans A1V1_A2",
    caption = "Une corrélation positive peut refléter une propension générale à répondre « 2 flashs »."
  ) +
  theme_classic(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", size = 14),
    strip.background = element_blank(),
    strip.text = element_text(face = "bold"),
    plot.caption = element_text(size = 8.5, hjust = 0)
  )

pdf_path <- file.path(FIG_DIR, "correlation_response2_physical_illusion_fission.pdf")
png_path <- file.path(FIG_DIR, "correlation_response2_physical_illusion_fission.png")

ggsave(pdf_path, p, width = 12, height = 5.2, device = cairo_pdf)
ggsave(png_path, p, width = 12, height = 5.2, dpi = 300)

report <- capture.output({
  cat("Corrélations entre taux de réponse « 2 flashs » dans A1V1_A2V2\n")
  cat("et taux d'illusion de fission dans A1V1_A2\n\n")
  print(results)
  cat("\nInterprétation : une corrélation positive indique que les participants\n")
  cat("qui répondent plus souvent « 2 flashs » lorsque deux flashs sont réellement\n")
  cat("présentés rapportent aussi davantage de fissions. Cette relation peut toutefois\n")
  cat("refléter un biais général vers la réponse « 2 flashs ».\n")
})

writeLines(
  report,
  file.path(REPORT_DIR, "rapport_correlation_response2_physical_illusion_fission.txt")
)

cat("\nAnalysis completed.\n\n")
print(filter(results, method == "Spearman"))
cat("\nPDF figure: ", pdf_path, "\n", sep = "")
cat("PNG figure: ", png_path, "\n", sep = "")
