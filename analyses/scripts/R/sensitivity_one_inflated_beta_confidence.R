# ============================================================
# One-inflated beta sensitivity analysis for bounded confidence ratings.
# Run from the analyses/ directory.
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tibble)
  library(glmmTMB)
  library(emmeans)
})


PROJECT_ROOT <- getwd()
DATA_FILE <- file.path(PROJECT_ROOT, "data", "processed", "model_ready_trials.csv")
OUT_DIR <- file.path(PROJECT_ROOT, "outputs", "tables", "results_v2")
dir.create(OUT_DIR, recursive = TRUE, showWarnings = FALSE)


fmt_p_plain <- function(p) {
  ifelse(
    is.na(p), NA_character_,
    ifelse(p < .001, "< .001", sub("^0", "", sprintf("%.3f", p)))
  )
}

lrt_row <- function(model_reduced, model_full, analysis, model_name, effect_tested, model_formula) {
  a <- anova(model_reduced, model_full, test = "Chisq")
  full_row <- a[2, ]
  data_used <- model.frame(model_full)

  tibble(
    analysis = analysis,
    model = model_name,
    effect_tested = effect_tested,
    formula = model_formula,
    N = dplyr::n_distinct(data_used$participant),
    n_obs = nrow(data_used),
    df = as.numeric(full_row$Df),
    chi_square = as.numeric(full_row$Chisq),
    p = as.numeric(full_row$`Pr(>Chisq)`)
  )
}

rescale_uncertainty_for_zibeta <- function(confidence, lower = 50, upper = 100, eps = 0.001) {
  u <- (upper - confidence) / (upper - lower)
  u <- ifelse(u >= 1, 1 - eps, u)
  u <- ifelse(u < 0, 0, u)
  u
}


if (!file.exists(DATA_FILE)) {
  stop("Missing data file: ", DATA_FILE, "\nRun the Python pipeline first.")
}

df <- read_csv(DATA_FILE, show_col_types = FALSE) %>%
  mutate(
    participant = factor(participant),
    base_condition = as.character(base_condition),
    soa_type = as.character(soa_type),
    illusion_type = as.character(illusion_type),
    percept_origin = as.character(percept_origin),
    matched_percept = as.character(matched_percept),
    response2 = as.numeric(response2),
    illusion = as.numeric(illusion),
    confidence = as.numeric(confidence)
  )


df_fiss <- df %>%
  filter(
    matched_percept == "two",
    percept_origin %in% c("congruent", "illusory"),
    soa_type %in% c("standard", "short"),
    !is.na(confidence)
  ) %>%
  mutate(
    percept_origin = factor(percept_origin, levels = c("congruent", "illusory")),
    soa_type = factor(soa_type, levels = c("standard", "short")),
    uncertainty_beta = rescale_uncertainty_for_zibeta(confidence)
  )

df_fus <- df %>%
  filter(
    matched_percept == "one",
    percept_origin %in% c("congruent", "illusory"),
    !is.na(confidence)
  ) %>%
  mutate(
    fusion_comparison = dplyr::case_when(
      percept_origin == "congruent" ~ "congruent_A1V1",
      percept_origin == "illusory" & soa_type == "standard" ~ "fusion_standard",
      percept_origin == "illusory" & soa_type == "short" ~ "fusion_short",
      TRUE ~ NA_character_
    ),
    fusion_comparison = factor(
      fusion_comparison,
      levels = c("congruent_A1V1", "fusion_standard", "fusion_short")
    ),
    uncertainty_beta = rescale_uncertainty_for_zibeta(confidence)
  ) %>%
  filter(!is.na(fusion_comparison))

cat("\nFission uncertainty range:\n")
print(range(df_fiss$uncertainty_beta, na.rm = TRUE))
cat("Number of zeros in fission uncertainty, corresponding to confidence = 100:\n")
print(sum(df_fiss$uncertainty_beta == 0, na.rm = TRUE))

cat("\nFusion uncertainty range:\n")
print(range(df_fus$uncertainty_beta, na.rm = TRUE))
cat("Number of zeros in fusion uncertainty, corresponding to confidence = 100:\n")
print(sum(df_fus$uncertainty_beta == 0, na.rm = TRUE))


m_fiss_zib_add <- glmmTMB(
  uncertainty_beta ~ percept_origin + soa_type + (1 | participant),
  ziformula = ~ 1,
  data = df_fiss,
  family = beta_family(link = "logit")
)

m_fiss_zib_int <- glmmTMB(
  uncertainty_beta ~ percept_origin * soa_type + (1 | participant),
  ziformula = ~ 1,
  data = df_fiss,
  family = beta_family(link = "logit")
)

m_fus_zib_null <- glmmTMB(
  uncertainty_beta ~ 1 + (1 | participant),
  ziformula = ~ 1,
  data = df_fus,
  family = beta_family(link = "logit")
)

m_fus_zib <- glmmTMB(
  uncertainty_beta ~ fusion_comparison + (1 | participant),
  ziformula = ~ 1,
  data = df_fus,
  family = beta_family(link = "logit")
)


zibeta_global_tests <- bind_rows(
  lrt_row(
    m_fiss_zib_add,
    m_fiss_zib_int,
    analysis = "ZIB uncertainty / one-inflated confidence: 2 flashs perçus",
    model_name = "Zero-inflated beta mixed model",
    effect_tested = "percept_origin × SOA",
    model_formula = "uncertainty_beta ~ percept_origin * SOA + (1 | participant), ziformula = ~1"
  ),
  lrt_row(
    m_fus_zib_null,
    m_fus_zib,
    analysis = "ZIB uncertainty / one-inflated confidence: 1 flash perçu",
    model_name = "Zero-inflated beta mixed model",
    effect_tested = "fusion_comparison",
    model_formula = "uncertainty_beta ~ fusion_comparison + (1 | participant), ziformula = ~1"
  )
) %>%
  mutate(
    chi_square = round(chi_square, 2),
    p_formatted = fmt_p_plain(p)
  )

write_csv(
  zibeta_global_tests,
  file.path(OUT_DIR, "confidence_one_inflated_beta_global_tests.csv")
)

cat("\nGlobal tests:\n")
print(zibeta_global_tests)



emm_fiss_zib <- emmeans(
  m_fiss_zib_int,
  ~ percept_origin | soa_type,
  type = "response"
)

fiss_zib_contr <- as.data.frame(
  contrast(
    emm_fiss_zib,
    method = "revpairwise",
    by = "soa_type"
  )
) %>%
  mutate(
    analysis = "2 flashs perçus",
    interpretation = "Positive estimate = higher uncertainty / lower confidence for illusory percepts"
  )

emm_fus_zib <- emmeans(
  m_fus_zib,
  ~ fusion_comparison,
  type = "response"
)

fus_zib_contr <- as.data.frame(
  contrast(
    emm_fus_zib,
    method = list(
      "fusion_standard - congruent_A1V1" = c(-1, 1, 0),
      "fusion_short - congruent_A1V1" = c(-1, 0, 1)
    )
  )
) %>%
  mutate(
    analysis = "1 flash perçu",
    interpretation = "Positive estimate = higher uncertainty / lower confidence for illusory percepts"
  )

write_csv(
  fiss_zib_contr,
  file.path(OUT_DIR, "confidence_one_inflated_beta_fission_contrasts.csv")
)

write_csv(
  fus_zib_contr,
  file.path(OUT_DIR, "confidence_one_inflated_beta_fusion_contrasts.csv")
)

cat("\nFission post-hoc contrasts:\n")
print(fiss_zib_contr)

cat("\nFusion post-hoc contrasts:\n")
print(fus_zib_contr)


sink(file.path(OUT_DIR, "confidence_one_inflated_beta_session_info.txt"))
sessionInfo()
sink()

message("\nOne-inflated beta sensitivity analysis completed.")
message("Outputs written to: ", OUT_DIR)
