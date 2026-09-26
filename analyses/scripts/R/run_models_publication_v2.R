# ============================================================
# Publication-oriented inferential tables for the SIFI participant study - v2
# ============================================================
# Main logic:
# 1. Perceptual primary model: illusion ~ illusion_type * SOA
# 2. Matched-confidence fission model: confidence ~ percept_origin * SOA
# 3. Matched-confidence fusion model: confidence ~ fusion_comparison
#
# response2 is kept as descriptive / manipulation-check output, not as a
# central inferential model in the main results table.
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tibble)
  library(tidyr)
  library(lme4)
  library(lmerTest)
  library(emmeans)
  library(glmmTMB)
  library(DHARMa)
})

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

PROJECT_ROOT <- getwd()
DATA_FILE <- file.path(PROJECT_ROOT, "data", "processed", "model_ready_trials.csv")
OUT_DIR <- file.path(PROJECT_ROOT, "outputs", "tables", "results_v2")
REPORT_DIR <- file.path(PROJECT_ROOT, "outputs", "reports")
dir.create(OUT_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(REPORT_DIR, recursive = TRUE, showWarnings = FALSE)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

fmt_p_plain <- function(p) {
  ifelse(
    is.na(p), NA_character_,
    ifelse(p < .001, "< .001", sub("^0", "", sprintf("%.3f", p)))
  )
}

fmt_p_latex <- function(p) {
  ifelse(
    is.na(p), NA_character_,
    ifelse(p < .001, "$< .001$", paste0("$", sub("^0", "", sprintf("%.3f", p)), "$"))
  )
}

fmt_num <- function(x, digits = 2) {
  ifelse(is.na(x), NA_character_, sprintf(paste0("%.", digits, "f"), x))
}

as_chr <- function(x) as.character(x)

participant_summary <- function(data, group_vars, outcome) {
  # Mean per participant first, then group mean/SD/SEM across participants.
  pdat <- data %>%
    group_by(across(all_of(c(group_vars, "participant")))) %>%
    summarise(
      participant_mean = mean(.data[[outcome]], na.rm = TRUE),
      n_trials_participant = dplyr::n(),
      .groups = "drop"
    )

  pdat %>%
    group_by(across(all_of(group_vars))) %>%
    summarise(
      N = n_distinct(participant),
      n_trials = sum(n_trials_participant),
      mean = mean(participant_mean, na.rm = TRUE),
      SD = sd(participant_mean, na.rm = TRUE),
      SEM = SD / sqrt(N),
      .groups = "drop"
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
    N = n_distinct(data_used$participant),
    n_obs = nrow(data_used),
    df = as.numeric(full_row$Df),
    chi_square = as.numeric(full_row$Chisq),
    p = as.numeric(full_row$`Pr(>Chisq)`)
  )
}

write_main_model_tests <- function(df, path) {
  con <- file(path, open = "wt", encoding = "UTF-8")
  on.exit(close(con), add = TRUE)

  writeLines("\\begin{table}[ht]", con)
  writeLines("\\centering", con)
  writeLines("\\caption{Likelihood-ratio tests pour les modèles mixtes principaux.}", con)
  writeLines("\\label{tab:main_model_tests_v2}", con)
  writeLines("\\scriptsize", con)
  writeLines("\\begin{tabular}{p{4.4cm}p{1.3cm}p{3.5cm}rrrrr}", con)
  writeLines("\\toprule", con)
  writeLines("Analyse & Modèle & Effet testé & N & Essais & ddl LRT & $\\chi^2$ & $p$ \\\\", con)
  writeLines("\\midrule", con)

  for (i in seq_len(nrow(df))) {
    line <- paste0(
      df$analysis_fr[i], " & ",
      df$model_fr[i], " & ",
      df$effect_fr[i], " & ",
      df$N[i], " & ",
      df$n_obs[i], " & ",
      df$df[i], " & ",
      df$chi_square_fmt[i], " & ",
      df$p_fmt[i], " \\\\"
    )
    writeLines(line, con)
  }

  writeLines("\\bottomrule", con)
  writeLines("\\end{tabular}", con)
  writeLines("", con)
  writeLines("\\vspace{0.2cm}", con)
  writeLines("\\begin{minipage}{0.96\\textwidth}", con)
  writeLines("\\footnotesize", con)
  writeLines("\\textit{Note.} GLMM = modèle linéaire généralisé mixte binomial ; LMM = modèle linéaire mixte gaussien. Les effets ont été évalués par tests du rapport de vraisemblance comparant des modèles emboîtés. Les ddl LRT correspondent au nombre de paramètres ajoutés dans le modèle complet. Tous les modèles incluaient un intercept aléatoire par participant.", con)
  writeLines("\\end{minipage}", con)
  writeLines("\\end{table}", con)
}
write_perceptual_response_contrasts <- function(df, path) {
  con <- file(path, open = "wt", encoding = "UTF-8")
  on.exit(close(con), add = TRUE)

  writeLines("\\begin{table}[ht]", con)
  writeLines("\\centering", con)
  writeLines("\\caption{Contrastes planifiés sur les réponses perceptives « 2 flashs ».}", con)
  writeLines("\\label{tab:perceptual_response_contrasts_v2}", con)
  writeLines("\\scriptsize", con)
  writeLines("\\begin{tabular}{p{5.2cm}rrrrr}", con)
  writeLines("\\toprule", con)
  writeLines("Contraste & Odds ratio & SE & $z$ & IC 95\\% & $p$ \\\\", con)
  writeLines("\\midrule", con)

  for (i in seq_len(nrow(df))) {
    line <- paste0(
      df$contrast_fr[i], " & ",
      df$odds_ratio_fmt[i], " & ",
      df$se_fmt[i], " & ",
      df$z_fmt[i], " & ",
      df$ci_fmt[i], " & ",
      df$p_fmt[i], " \\\\"
    )
    writeLines(line, con)
  }

  writeLines("\\bottomrule", con)
  writeLines("\\end{tabular}", con)
  writeLines("", con)
  writeLines("\\vspace{0.2cm}", con)
  writeLines("\\begin{minipage}{0.94\\textwidth}", con)
  writeLines("\\footnotesize", con)
  writeLines("\\textit{Note.} Le modèle est un GLMM binomial prédisant la probabilité de répondre « 2 flashs » à partir de la condition expérimentale, avec un intercept aléatoire par participant : \\texttt{response2 \\textasciitilde{} condition\\_cell + (1 | participant)}. Les contrastes sont exprimés en odds ratios. Une valeur supérieure à 1 indique une probabilité plus élevée de réponse « 2 flashs » dans la première condition du contraste.", con)
  writeLines("\\end{minipage}", con)
  writeLines("\\end{table}", con)
}

write_illusion_descriptives <- function(df, path, total_trials_note) {
  con <- file(path, open = "wt", encoding = "UTF-8")
  on.exit(close(con), add = TRUE)

  writeLines("\\begin{table}[ht]", con)
  writeLines("\\centering", con)
  writeLines("\\caption{Taux d’illusion observés et probabilités prédites par le modèle selon le type d’illusion et le SOA.}", con)
  writeLines("\\label{tab:illusion_descriptives_v2}", con)
  writeLines("\\footnotesize", con)
  writeLines("\\begin{tabular}{llrrr}", con)
  writeLines("\\toprule", con)
  writeLines("Type d’illusion & SOA & N & Observé (\\%) & Prédit par GLMM (\\%) \\\\", con)
  writeLines("\\midrule", con)

  for (i in seq_len(nrow(df))) {
    line <- paste0(
      df$illusion_type_fr[i], " & ",
      df$soa_type_fr[i], " & ",
      df$N[i], " & ",
      df$observed_fmt[i], " & ",
      df$predicted_fmt[i], " \\\\"
    )
    writeLines(line, con)
  }

  writeLines("\\bottomrule", con)
  writeLines("\\end{tabular}", con)
  writeLines("", con)
  writeLines("\\vspace{0.2cm}", con)
  writeLines("\\begin{minipage}{0.92\\textwidth}", con)
  writeLines("\\footnotesize", con)
  writeLines(paste0("\\textit{Note.} ", total_trials_note, " Les valeurs observées correspondent aux moyennes des taux individuels. Les valeurs prédites correspondent aux probabilités estimées par le modèle logistique mixte utilisé pour analyser le taux d’illusion : $illusion \\sim type\\_illusion \\times SOA + (1\\,|\\,participant)$.") , con)
  writeLines("\\end{minipage}", con)
  writeLines("\\end{table}", con)
}

write_matched_contrasts <- function(df, path) {
  con <- file(path, open = "wt", encoding = "UTF-8")
  on.exit(close(con), add = TRUE)

  writeLines("\\begin{table}[ht]", con)
  writeLines("\\centering", con)
  writeLines("\\caption{Contrastes de confiance à percept apparié.}", con)
  writeLines("\\label{tab:matched_confidence_contrasts_v2}", con)
  writeLines("\\scriptsize", con)
  writeLines("\\begin{tabular}{p{4.0cm}p{1.4cm}rrrp{2.6cm}r}", con)
  writeLines("\\toprule", con)
  writeLines("Analyse & SOA & Estimation & SE & ddl & IC 95\\% & $p$ \\\\", con)
  writeLines("\\midrule", con)

  for (i in seq_len(nrow(df))) {
    line <- paste0(
      df$analysis_fr[i], " & ",
      df$soa_fr[i], " & ",
      df$estimate_fmt[i], " & ",
      df$se_fmt[i], " & ",
      df$df_fmt[i], " & ",
      df$ci_fmt[i], " & ",
      df$p_fmt[i], " \\\\"
    )
    writeLines(line, con)
  }

  writeLines("\\bottomrule", con)
  writeLines("\\end{tabular}", con)
  writeLines("", con)
  writeLines("\\vspace{0.2cm}", con)
  writeLines("\\begin{minipage}{0.92\\textwidth}", con)
  writeLines("\\footnotesize", con)
  writeLines("\\textit{Note.} Toutes les estimations correspondent au contraste illusoire -- congruent et sont exprimées en points de pourcentage de confiance. Une valeur négative indique une confiance plus faible pour le percept illusoire que pour le percept congruent. Pour la fusion, la condition congruente A1V1, qui ne comporte pas de SOA, sert de référence commune aux contrastes avec les conditions de fusion standard et courte.", con)
  writeLines("\\end{minipage}", con)
  writeLines("\\end{table}", con)
}

write_matched_trial_counts <- function(df, path) {
  con <- file(path, open = "wt", encoding = "UTF-8")
  on.exit(close(con), add = TRUE)

  writeLines("\\begin{table}[ht]", con)
  writeLines("\\centering", con)
  writeLines("\\caption{Nombre d’essais inclus dans les contrastes de confiance à percept apparié.}", con)
  writeLines("\\label{tab:matched_confidence_trial_counts}", con)
  writeLines("\\footnotesize", con)
  writeLines("\\begin{tabular}{llcc}", con)
  writeLines("\\toprule", con)
  writeLines("Analyse & SOA & Participants congr./illus. & Essais congr./illus. \\\\", con)
  writeLines("\\midrule", con)

  for (i in seq_len(nrow(df))) {
    line <- paste0(
      df$Analyse[i], " & ",
      df$SOA[i], " & ",
      df$`Participants congr./illus.`[i], " & ",
      df$`Essais congr./illus.`[i], " \\\\"
    )
    writeLines(line, con)
  }

  writeLines("\\bottomrule", con)
  writeLines("\\end{tabular}", con)
  writeLines("", con)
  writeLines("\\vspace{0.2cm}", con)
  writeLines("\\begin{minipage}{0.92\\textwidth}", con)
  writeLines("\\footnotesize", con)
  writeLines("\\textit{Note.} Les colonnes indiquent le nombre de participants et le nombre d’essais contribuant respectivement à la condition congruente puis à la condition illusoire. Pour la fusion, la condition congruente A1V1 ne comporte pas de SOA et sert donc de référence commune aux contrastes avec les conditions de fusion standard et courte.", con)
  writeLines("\\end{minipage}", con)
  writeLines("\\end{table}", con)
}

write_secondary_soa_tests <- function(df, path) {
  con <- file(path, open = "wt", encoding = "UTF-8")
  on.exit(close(con), add = TRUE)

  writeLines("\\begin{table}[ht]", con)
  writeLines("\\centering", con)
  writeLines("\\caption{Analyses complémentaires : effet du SOA sur la confiance des essais illusoires.}", con)
  writeLines("\\label{tab:secondary_illusory_confidence_soa_v2}", con)
  writeLines("\\footnotesize", con)
  writeLines("\\begin{tabular}{lrrrr}", con)
  writeLines("\\toprule", con)
  writeLines("Analyse & N & Essais & $\\chi^2$ & $p$ \\\\", con)
  writeLines("\\midrule", con)

  for (i in seq_len(nrow(df))) {
    line <- paste0(
      df$analysis_fr[i], " & ",
      df$N[i], " & ",
      df$n_obs[i], " & ",
      df$chi_square_fmt[i], " & ",
      df$p_fmt[i], " \\\\"
    )
    writeLines(line, con)
  }

  writeLines("\\bottomrule", con)
  writeLines("\\end{tabular}", con)
  writeLines("", con)
  writeLines("\\vspace{0.2cm}", con)
  writeLines("\\begin{minipage}{0.92\\textwidth}", con)
  writeLines("\\footnotesize", con)
  writeLines("\\textit{Note.} Ces analyses sont complémentaires. Elles testent si, parmi les seuls essais illusoires, la confiance varie selon le SOA. Elles ne constituent pas les tests métacognitifs principaux.", con)
  writeLines("\\end{minipage}", con)
  writeLines("\\end{table}", con)
}

# ------------------------------------------------------------
# Load and harmonise data
# ------------------------------------------------------------

if (!file.exists(DATA_FILE)) {
  stop("Missing data file: ", DATA_FILE, "\nRun the Python pipeline first: python scripts/run_all.py")
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
    confidence = as.numeric(confidence),
    accuracy = as.numeric(accuracy)
  ) %>%
  mutate(
    condition_cell = dplyr::case_when(
      base_condition == "A1V1" ~ "A1V1",
      soa_type %in% c("standard", "short") ~ paste(base_condition, soa_type, sep = "_"),
      TRUE ~ base_condition
    )
  )

# ------------------------------------------------------------
# Main model 1: perceptual responses
# ------------------------------------------------------------

df_resp_cell <- df %>%
  filter(
    base_condition %in% c("A1V1", "A1V1_A2", "A1V1_A2V2", "A1V1_V2"),
    !is.na(response2),
    !is.na(condition_cell)
  ) %>%
  mutate(
    condition_cell = factor(
      condition_cell,
      levels = c(
        "A1V1",
        "A1V1_A2_standard", "A1V1_A2_short",
        "A1V1_A2V2_standard", "A1V1_A2V2_short",
        "A1V1_V2_standard", "A1V1_V2_short"
      )
    )
  ) %>%
  filter(!is.na(condition_cell))

m_resp_cell_null <- glmer(
  response2 ~ 1 + (1 | participant),
  data = df_resp_cell,
  family = binomial,
  control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))
)

m_resp_cell <- glmer(
  response2 ~ condition_cell + (1 | participant),
  data = df_resp_cell,
  family = binomial,
  control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))
)
# ------------------------------------------------------------
# Planned contrasts: perceptual responses
# ------------------------------------------------------------

emm_resp_cell <- emmeans(m_resp_cell, ~ condition_cell)

perceptual_contrasts_raw <- as.data.frame(
  contrast(
    emm_resp_cell,
    method = list(
      # Fission: does A1V1_A2 increase "2 flashes" responses relative to A1V1?
      "Fission standard vs A1V1" = c(-1, 1, 0, 0, 0, 0, 0),
      "Fission court vs A1V1"    = c(-1, 0, 1, 0, 0, 0, 0),

      # Fusion: does A1V1_V2 reduce "2 flashes" responses relative to congruent A1V1_A2V2?
      "Fusion standard vs congruent standard" = c(0, 0, 0, -1, 0, 1, 0),
      "Fusion court vs congruent court"       = c(0, 0, 0, 0, -1, 0, 1),

      # SOA effects within illusory conditions
      "Fission court vs standard" = c(0, -1, 1, 0, 0, 0, 0),
      "Fusion court vs standard"  = c(0, 0, 0, 0, 0, -1, 1)
    )
  )
)

perceptual_response_contrasts <- perceptual_contrasts_raw %>%
  mutate(
    odds_ratio = exp(estimate),
    lower_95 = exp(estimate - qnorm(.975) * SE),
    upper_95 = exp(estimate + qnorm(.975) * SE),
    contrast_fr = dplyr::case_when(
      contrast == "Fission standard vs A1V1" ~ "A1V1+A2 standard vs A1V1",
      contrast == "Fission court vs A1V1" ~ "A1V1+A2 court vs A1V1",
      contrast == "Fusion standard vs congruent standard" ~ "A1V1+V2 standard vs A1V1+A2V2 standard",
      contrast == "Fusion court vs congruent court" ~ "A1V1+V2 court vs A1V1+A2V2 court",
      contrast == "Fission court vs standard" ~ "A1V1+A2 court vs A1V1+A2 standard",
      contrast == "Fusion court vs standard" ~ "A1V1+V2 court vs A1V1+V2 standard",
    ),
    odds_ratio_fmt = sprintf("%.2f", odds_ratio),
    se_fmt = sprintf("%.2f", SE),
    z_fmt = sprintf("%.2f", z.ratio),
    ci_fmt = paste0("[", sprintf("%.2f", lower_95), ", ", sprintf("%.2f", upper_95), "]"),
    p_fmt = fmt_p_latex(p.value),
    p_formatted = fmt_p_plain(p.value)
  )

write_csv(
  perceptual_response_contrasts,
  file.path(OUT_DIR, "perceptual_response_planned_contrasts.csv")
)

write_perceptual_response_contrasts(
  perceptual_response_contrasts,
  file.path(OUT_DIR, "perceptual_response_planned_contrasts.tex")
)

# ------------------------------------------------------------
# Main model 2: matched confidence, fission
# ------------------------------------------------------------

df_fiss <- df %>%
  filter(
    matched_percept == "two",
    percept_origin %in% c("congruent", "illusory"),
    soa_type %in% c("standard", "short"),
    !is.na(confidence)
  ) %>%
  mutate(
    percept_origin = factor(percept_origin, levels = c("congruent", "illusory")),
    soa_type = factor(soa_type, levels = c("standard", "short"))
  )

m_fiss_add <- lmer(
  confidence ~ percept_origin + soa_type + (1 | participant),
  data = df_fiss,
  REML = FALSE
)

m_fiss_int <- lmer(
  confidence ~ percept_origin * soa_type + (1 | participant),
  data = df_fiss,
  REML = FALSE
)

# ------------------------------------------------------------
# Main model 3: matched confidence, fusion
# ------------------------------------------------------------

df_fus_by_soa <- df %>%
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
    )
  ) %>%
  filter(!is.na(fusion_comparison))

m_fus_by_soa_null <- lmer(
  confidence ~ 1 + (1 | participant),
  data = df_fus_by_soa,
  REML = FALSE
)

m_fus_by_soa <- lmer(
  confidence ~ fusion_comparison + (1 | participant),
  data = df_fus_by_soa,
  REML = FALSE
)


response2_observed <- participant_summary(
  df_resp_cell,
  group_vars = c("condition_cell"),
  outcome = "response2"
) %>%
  mutate(observed_percent = 100 * mean)

response2_emm <- as.data.frame(
  summary(emmeans(m_resp_cell, ~ condition_cell, type = "response"))
) %>%
  transmute(
    condition_cell,
    predicted_percent = 100 * prob,
    lower_95_percent = 100 * asymp.LCL,
    upper_95_percent = 100 * asymp.UCL
  )

response2_table <- response2_observed %>%
  left_join(response2_emm, by = "condition_cell") %>%
  mutate(
    observed_fmt = sprintf("%.1f", observed_percent),
    predicted_fmt = sprintf("%.1f", predicted_percent),
    ci_fmt = paste0("[", sprintf("%.1f", lower_95_percent), ", ", sprintf("%.1f", upper_95_percent), "]")
  )
write_csv(response2_table, file.path(OUT_DIR, "response2_condition_cell_descriptives.csv"))

response2_lrt <- lrt_row(
  m_resp_cell_null, m_resp_cell,
  analysis = "Response2 condition-cell manipulation check",
  model_name = "Binomial GLMM",
  effect_tested = "condition_cell",
  model_formula = "response2 ~ condition_cell + (1 | participant)"
) %>%
  mutate(
    chi_square = round(chi_square, 2),
    p_formatted = fmt_p_plain(p)
  )
write_csv(response2_lrt, file.path(OUT_DIR, "response2_condition_cell_LRT_control.csv"))

# ------------------------------------------------------------
# Sensitivity analysis: beta mixed models for confidence
# ------------------------------------------------------------

rescale_confidence_beta <- function(x, lower = 50, upper = 100, eps = 0.001) {
  y <- (x - lower) / (upper - lower)
  pmin(pmax(y, eps), 1 - eps)
}

df_fiss_beta <- df_fiss %>%
  mutate(confidence_beta = rescale_confidence_beta(confidence))

df_fus_beta <- df_fus_by_soa %>%
  mutate(confidence_beta = rescale_confidence_beta(confidence))

m_fiss_beta_add <- glmmTMB(
  confidence_beta ~ percept_origin + soa_type + (1 | participant),
  data = df_fiss_beta,
  family = beta_family(link = "logit")
)

m_fiss_beta_int <- glmmTMB(
  confidence_beta ~ percept_origin * soa_type + (1 | participant),
  data = df_fiss_beta,
  family = beta_family(link = "logit")
)

m_fus_beta_null <- glmmTMB(
  confidence_beta ~ 1 + (1 | participant),
  data = df_fus_beta,
  family = beta_family(link = "logit")
)

m_fus_beta <- glmmTMB(
  confidence_beta ~ fusion_comparison + (1 | participant),
  data = df_fus_beta,
  family = beta_family(link = "logit")
)

beta_sensitivity_tests <- bind_rows(
  lrt_row(
    m_fiss_beta_add, m_fiss_beta_int,
    analysis = "Beta sensitivity: 2 flashs perçus",
    model_name = "Beta GLMM",
    effect_tested = "percept_origin × SOA",
    model_formula = "confidence_beta ~ percept_origin * SOA + (1 | participant)"
  ),
  lrt_row(
    m_fus_beta_null, m_fus_beta,
    analysis = "Beta sensitivity: 1 flash perçu",
    model_name = "Beta GLMM",
    effect_tested = "fusion_comparison",
    model_formula = "confidence_beta ~ fusion_comparison + (1 | participant)"
  )
) %>%
  mutate(
    chi_square = round(chi_square, 2),
    chi_square_fmt = sprintf("%.2f", chi_square),
    p_fmt = fmt_p_latex(p),
    p_formatted = fmt_p_plain(p)
  )

write_csv(
  beta_sensitivity_tests,
  file.path(OUT_DIR, "confidence_beta_sensitivity_tests.csv")
)
# ------------------------------------------------------------
# Beta sensitivity: post-hoc contrasts for matched confidence
# ------------------------------------------------------------

# Fission / 2 flashs perçus
emm_fiss_beta <- emmeans(
  m_fiss_beta_int,
  ~ percept_origin | soa_type,
  type = "response"
)

fiss_beta_contr <- as.data.frame(
  contrast(
    emm_fiss_beta,
    method = "revpairwise",
    by = "soa_type"
  )
)

# Fusion / 1 flash perçu
emm_fus_beta <- emmeans(
  m_fus_beta,
  ~ fusion_comparison,
  type = "response"
)

fus_beta_contr <- as.data.frame(
  contrast(
    emm_fus_beta,
    method = list(
      "fusion_standard - congruent_A1V1" = c(-1, 1, 0),
      "fusion_short - congruent_A1V1" = c(-1, 0, 1)
    )
  )
)

write_csv(
  fiss_beta_contr,
  file.path(OUT_DIR, "beta_fission_matched_confidence_contrasts.csv")
)

write_csv(
  fus_beta_contr,
  file.path(OUT_DIR, "beta_fusion_matched_confidence_contrasts.csv")
)

# ------------------------------------------------------------
# Diagnostics: perceptual response GLMM
# ------------------------------------------------------------

sink(file.path(OUT_DIR, "diagnostic_response2_glmm_summary.txt"))
print(summary(m_resp_cell))
cat("\nSingular fit:\n")
print(isSingular(m_resp_cell))
cat("\nVariance components:\n")
print(VarCorr(m_resp_cell))
sink()

if (requireNamespace("DHARMa", quietly = TRUE)) {
  library(DHARMa)

  sim_resp <- simulateResiduals(m_resp_cell, n = 1000)

  pdf(file.path(OUT_DIR, "diagnostic_response2_glmm_DHARMa.pdf"))
  plot(sim_resp)
  dev.off()

  sink(file.path(OUT_DIR, "diagnostic_response2_glmm_DHARMa_tests.txt"))
  print(testUniformity(sim_resp))
  print(testDispersion(sim_resp))
  print(testOutliers(sim_resp))
  sink()
} else {
  warning("Package DHARMa is not installed; GLMM residual diagnostics were not run.")
}

# ------------------------------------------------------------
# Diagnostics: matched confidence LMM, 2 flashs perceived
# ------------------------------------------------------------

sink(file.path(OUT_DIR, "diagnostic_confidence_2flashes_lmm_summary.txt"))
print(summary(m_fiss_int))
cat("\nSingular fit:\n")
print(isSingular(m_fiss_int))
cat("\nVariance components:\n")
print(VarCorr(m_fiss_int))
sink()

pdf(file.path(OUT_DIR, "diagnostic_confidence_2flashes_lmm_residuals.pdf"))
par(mfrow = c(2, 2))

plot(
  fitted(m_fiss_int),
  resid(m_fiss_int),
  xlab = "Valeurs ajustées",
  ylab = "Résidus",
  main = "Résidus vs valeurs ajustées"
)
abline(h = 0, lty = 2)

qqnorm(resid(m_fiss_int), main = "QQ-plot des résidus")
qqline(resid(m_fiss_int))

hist(
  resid(m_fiss_int),
  breaks = 30,
  main = "Distribution des résidus",
  xlab = "Résidus"
)

plot(m_fiss_int, main = "Diagnostic LMM")
dev.off()

# ------------------------------------------------------------
# Diagnostics: matched confidence LMM, 1 flash perceived
# ------------------------------------------------------------

sink(file.path(OUT_DIR, "diagnostic_confidence_1flash_lmm_summary.txt"))
print(summary(m_fus_by_soa))
cat("\nSingular fit:\n")
print(isSingular(m_fus_by_soa))
cat("\nVariance components:\n")
print(VarCorr(m_fus_by_soa))
sink()

pdf(file.path(OUT_DIR, "diagnostic_confidence_1flash_lmm_residuals.pdf"))
par(mfrow = c(2, 2))

plot(
  fitted(m_fus_by_soa),
  resid(m_fus_by_soa),
  xlab = "Valeurs ajustées",
  ylab = "Résidus",
  main = "Résidus vs valeurs ajustées"
)
abline(h = 0, lty = 2)

qqnorm(resid(m_fus_by_soa), main = "QQ-plot des résidus")
qqline(resid(m_fus_by_soa))

hist(
  resid(m_fus_by_soa),
  breaks = 30,
  main = "Distribution des résidus",
  xlab = "Résidus"
)

plot(m_fus_by_soa, main = "Diagnostic LMM")
dev.off()

# ------------------------------------------------------------
# Secondary model: confidence in illusory trials as a function of SOA
# ------------------------------------------------------------

df_fiss_soa <- df %>%
  filter(
    matched_percept == "two",
    percept_origin == "illusory",
    soa_type %in% c("standard", "short"),
    !is.na(confidence)
  ) %>%
  mutate(soa_type = factor(soa_type, levels = c("standard", "short")))

m_fiss_soa_null <- lmer(confidence ~ 1 + (1 | participant), data = df_fiss_soa, REML = FALSE)
m_fiss_soa <- lmer(confidence ~ soa_type + (1 | participant), data = df_fiss_soa, REML = FALSE)

df_fus_soa <- df %>%
  filter(
    matched_percept == "one",
    percept_origin == "illusory",
    soa_type %in% c("standard", "short"),
    !is.na(confidence)
  ) %>%
  mutate(soa_type = factor(soa_type, levels = c("standard", "short")))

m_fus_soa_null <- lmer(confidence ~ 1 + (1 | participant), data = df_fus_soa, REML = FALSE)
m_fus_soa <- lmer(confidence ~ soa_type + (1 | participant), data = df_fus_soa, REML = FALSE)

secondary_soa_tests <- bind_rows(
  lrt_row(
    m_fiss_soa_null, m_fiss_soa,
    analysis = "Confiance fission illusoire",
    model_name = "Gaussian LMM",
    effect_tested = "SOA",
    model_formula = "confidence ~ SOA + (1 | participant)"
  ),
  lrt_row(
    m_fus_soa_null, m_fus_soa,
    analysis = "Confiance fusion illusoire",
    model_name = "Gaussian LMM",
    effect_tested = "SOA",
    model_formula = "confidence ~ SOA + (1 | participant)"
  )
) %>%
  mutate(
    analysis_fr = analysis,
    chi_square = round(chi_square, 2),
    chi_square_fmt = sprintf("%.2f", chi_square),
    p_formatted = fmt_p_plain(p),
    p_fmt = fmt_p_latex(p)
  )
write_csv(secondary_soa_tests, file.path(OUT_DIR, "secondary_illusory_confidence_soa_tests.csv"))
write_secondary_soa_tests(secondary_soa_tests, file.path(OUT_DIR, "secondary_illusory_confidence_soa_tests.tex"))

# ============================================================
# Robustesse : structure aléatoire enrichie (pentes aléatoires)
# ============================================================

# --- Fission : modèle additif et modèle interaction, avec pentes aléatoires ---
# (1 + a + b || participant) = intercept + pentes pour a et b, NON corrélées

m_fiss_add_rs <- lmer(
  confidence ~ percept_origin + soa_type + (1 + percept_origin + soa_type || participant),
  data = df_fiss, REML = FALSE,
  control = lmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))
)

m_fiss_int_rs <- lmer(
  confidence ~ percept_origin * soa_type + (1 + percept_origin + soa_type || participant),
  data = df_fiss, REML = FALSE,
  control = lmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))
)

# Le modèle a-t-il convergé proprement ? TRUE = problème (singularité)
cat("Fission interaction RS — singular:", isSingular(m_fiss_int_rs), "\n")

# Test de l'interaction origine x SOA avec la structure aléatoire enrichie
print(anova(m_fiss_add_rs, m_fiss_int_rs))

# Contrastes appariés sous la structure enrichie
print(
  contrast(
    emmeans(m_fiss_int_rs, ~ percept_origin | soa_type),
    method = "revpairwise"
  )
)

# --- Fusion : pente aléatoire pour le facteur de comparaison ---
m_fus_rs <- lmer(
  confidence ~ fusion_comparison + (1 + fusion_comparison || participant),
  data = df_fus_by_soa, REML = FALSE,
  control = lmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))
)

cat("Fusion RS — singular:", isSingular(m_fus_rs), "\n")

# Contrastes de fusion sous la structure enrichie
print(
  contrast(
    emmeans(m_fus_rs, ~ fusion_comparison),
    method = list(
      "fusion_standard - congruent_A1V1" = c(-1, 1, 0),
      "fusion_short - congruent_A1V1"     = c(-1, 0, 1)
    )
  )
)
# ------------------------------------------------------------
# Table 1: main model tests
# ------------------------------------------------------------

main_model_tests <- bind_rows(
  lrt_row(
    m_resp_cell_null, m_resp_cell,
    analysis = "Perceptual response",
    model_name = "Binomial GLMM",
    effect_tested = "condition_cell",
    model_formula = "response2 ~ condition_cell + (1 | participant)"
  ),
  lrt_row(
    m_fiss_add, m_fiss_int,
    analysis = "Matched confidence: fission",
    model_name = "Gaussian LMM",
    effect_tested = "percept_origin × SOA",
    model_formula = "confidence ~ percept_origin * SOA + (1 | participant)"
  ),
  lrt_row(
    m_fus_by_soa_null, m_fus_by_soa,
    analysis = "Matched confidence: fusion",
    model_name = "Gaussian LMM",
    effect_tested = "fusion_comparison",
    model_formula = "confidence ~ fusion_comparison + (1 | participant)"
  )
) %>%
  mutate(
    chi_square = round(chi_square, 2),
    p_formatted = fmt_p_plain(p)
  )

write_csv(main_model_tests, file.path(OUT_DIR, "main_model_tests.csv"))

main_model_tests_clean <- main_model_tests %>%
  mutate(
    analysis_fr = dplyr::case_when(
      analysis == "Perceptual response" ~ "Réponse perceptive",
      analysis == "Matched confidence: fission" ~ "Confiance appariée : 2 flashs",
      analysis == "Matched confidence: fusion" ~ "Confiance appariée : 1 flash",
      TRUE ~ analysis
    ),
    model_fr = dplyr::case_when(
      model == "Binomial GLMM" ~ "GLMM",
      model == "Gaussian LMM" ~ "LMM",
      TRUE ~ model
    ),
    effect_fr = dplyr::case_when(
      effect_tested == "condition_cell" ~ "Condition",
      effect_tested == "percept_origin × SOA" ~ "Origine $\\times$ SOA",
      effect_tested == "fusion_comparison" ~ "Condition de fusion",
      TRUE ~ effect_tested
    ),
    chi_square_fmt = sprintf("%.2f", chi_square),
    p_fmt = fmt_p_latex(p)
  )

write_main_model_tests(main_model_tests_clean, file.path(OUT_DIR, "main_model_tests.tex"))

# ------------------------------------------------------------
# Table 3: matched-confidence contrasts
# ------------------------------------------------------------

fiss_contr <- as.data.frame(
  contrast(
    emmeans(m_fiss_int, ~ percept_origin | soa_type),
    method = "revpairwise"
  )
) %>%
  mutate(
    analysis = "Fission matched percept: reported 2 flashes",
    contrast_type = "Illusory - congruent"
  ) %>%
  transmute(
    analysis,
    SOA = soa_type,
    contrast = contrast_type,
    estimate = estimate,
    SE = SE,
    df = df,
    lower_95 = estimate - qt(.975, df) * SE,
    upper_95 = estimate + qt(.975, df) * SE,
    statistic = t.ratio,
    p = p.value
  )

emm_fus_by_soa <- emmeans(m_fus_by_soa, ~ fusion_comparison)

fus_contr <- as.data.frame(
  contrast(
    emm_fus_by_soa,
    method = list(
      "fusion_standard - congruent_A1V1" = c(-1, 1, 0),
      "fusion_short - congruent_A1V1" = c(-1, 0, 1)
    )
  )
) %>%
  mutate(
    analysis = "Fusion matched percept: reported 1 flash",
    SOA = dplyr::case_when(
      contrast == "fusion_standard - congruent_A1V1" ~ "standard",
      contrast == "fusion_short - congruent_A1V1" ~ "short",
      TRUE ~ contrast
    ),
    contrast_type = "Illusory - congruent"
  ) %>%
  transmute(
    analysis,
    SOA,
    contrast = contrast_type,
    estimate = estimate,
    SE = SE,
    df = df,
    lower_95 = estimate - qt(.975, df) * SE,
    upper_95 = estimate + qt(.975, df) * SE,
    statistic = t.ratio,
    p = p.value
  )

matched_contrasts <- bind_rows(fiss_contr, fus_contr) %>%
  mutate(
    estimate = round(estimate, 2),
    SE = round(SE, 2),
    df = round(df, 1),
    lower_95 = round(lower_95, 2),
    upper_95 = round(upper_95, 2),
    statistic = round(statistic, 2),
    p_formatted = fmt_p_plain(p)
  )
write_csv(matched_contrasts, file.path(OUT_DIR, "matched_percept_confidence_contrasts.csv"))

matched_contrasts_clean <- matched_contrasts %>%
  mutate(
    analysis_fr = dplyr::case_when(
      analysis == "Fission matched percept: reported 2 flashes" ~ "2 flashs perçus",
      analysis == "Fusion matched percept: reported 1 flash" ~ "1 flash perçu",
      TRUE ~ analysis
    ),
    soa_fr = dplyr::case_when(
      SOA == "standard" ~ "Standard",
      SOA == "short" ~ "Court",
      TRUE ~ SOA
    ),
    estimate_fmt = sprintf("%.2f", estimate),
    se_fmt = sprintf("%.2f", SE),
    df_fmt = sprintf("%.1f", df),
    ci_fmt = paste0("[", sprintf("%.2f", lower_95), ", ", sprintf("%.2f", upper_95), "]"),
    p_fmt = fmt_p_latex(p)
  )
write_csv(matched_contrasts_clean, file.path(OUT_DIR, "matched_percept_confidence_contrasts_clean.csv"))
write_matched_contrasts(matched_contrasts_clean, file.path(OUT_DIR, "matched_percept_confidence_contrasts.tex"))

# ------------------------------------------------------------
# Table 4 / appendix: matched-confidence trial counts
# ------------------------------------------------------------

count_trials <- function(data, condition_expr) {
  out <- data %>%
    dplyr::filter({{ condition_expr }}) %>%
    dplyr::summarise(
      N = dplyr::n_distinct(participant),
      n_trials = dplyr::n(),
      .groups = "drop"
    )

  list(N = out$N[1], n_trials = out$n_trials[1])
}

fiss_standard_cong <- count_trials(df_fiss, soa_type == "standard" & percept_origin == "congruent")
fiss_standard_illus <- count_trials(df_fiss, soa_type == "standard" & percept_origin == "illusory")
fiss_short_cong <- count_trials(df_fiss, soa_type == "short" & percept_origin == "congruent")
fiss_short_illus <- count_trials(df_fiss, soa_type == "short" & percept_origin == "illusory")

fus_cong <- count_trials(df_fus_by_soa, fusion_comparison == "congruent_A1V1")
fus_standard_illus <- count_trials(df_fus_by_soa, fusion_comparison == "fusion_standard")
fus_short_illus <- count_trials(df_fus_by_soa, fusion_comparison == "fusion_short")

matched_trial_counts <- tibble(
  Analyse = c(
    "Fission : percept 2 flashs",
    "Fission : percept 2 flashs",
    "Fusion : percept 1 flash",
    "Fusion : percept 1 flash"
  ),
  SOA = c("Standard", "Court", "Standard", "Court"),
  `Participants congr./illus.` = c(
    paste0(fiss_standard_cong$N, " / ", fiss_standard_illus$N),
    paste0(fiss_short_cong$N, " / ", fiss_short_illus$N),
    paste0(fus_cong$N, " / ", fus_standard_illus$N),
    paste0(fus_cong$N, " / ", fus_short_illus$N)
  ),
  `Essais congr./illus.` = c(
    paste0(fiss_standard_cong$n_trials, " / ", fiss_standard_illus$n_trials),
    paste0(fiss_short_cong$n_trials, " / ", fiss_short_illus$n_trials),
    paste0(fus_cong$n_trials, " / ", fus_standard_illus$n_trials),
    paste0(fus_cong$n_trials, " / ", fus_short_illus$n_trials)
  )
)
write_csv(matched_trial_counts, file.path(OUT_DIR, "matched_percept_confidence_trial_counts.csv"))
write_matched_trial_counts(matched_trial_counts, file.path(OUT_DIR, "matched_percept_confidence_trial_counts.tex"))

# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

report_lines <- c(
  "SIFI multisensory participant study - v2 inferential outputs",
  "=================================================",
  "",
  "Main models:",
  "1. response2 ~ condition_cell + (1 | participant)",
  "2. confidence ~ percept_origin * SOA + (1 | participant) for fission matched percepts",
  "3. confidence ~ fusion_comparison + (1 | participant) for fusion matched percepts",
  "",
  "response2 is exported as a descriptive/manipulation-check output, not as a central inferential model.",
  "Secondary SOA tests within illusory confidence trials are exported separately.",
  "",
  paste0("Output directory: ", OUT_DIR),
  "",
  "Generated files:",
  "- main_model_tests.csv / .tex",
  "- table_illusion_descriptives.csv / .tex",
  "- matched_percept_confidence_contrasts.csv / .tex",
  "- matched_percept_confidence_trial_counts.csv / .tex",
  "- secondary_illusory_confidence_soa_tests.csv / .tex",
  "- perceptual_response_planned_contrasts.csv / .tex",
  "- response2_condition_cell_descriptives.csv",
  "- response2_condition_cell_LRT_control.csv"
)

writeLines(report_lines, con = file.path(REPORT_DIR, "model_report_v2.txt"))

message("V2 model/tables completed. Results written to: ", OUT_DIR)
message("Report written to: ", file.path(REPORT_DIR, "model_report_v2.txt"))
