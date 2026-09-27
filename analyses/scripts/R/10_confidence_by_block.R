# ============================================================
# Block analysis of confidence on illusory trials, with participant trajectories and group summaries.
# Run from the analyses/ directory.
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(lme4)
  library(lmerTest)
})

PROJECT_ROOT <- getwd()

CONFIDENCE_SCOPE <- "illusion_only"

candidate_data_files <- c(
  file.path(PROJECT_ROOT, "data", "processed", "model_ready_trials.csv"),
  file.path(PROJECT_ROOT, "outputs", "tables", "model_ready_trials.csv"),
  file.path(PROJECT_ROOT, "model_ready_trials.csv")
)

existing_files <- candidate_data_files[file.exists(candidate_data_files)]

if (length(existing_files) == 0) {
  stop(
    paste0(
      "Could not find model_ready_trials.csv.\n",
      "Emplacements testés :\n- ",
      paste(candidate_data_files, collapse = "\n- ")
    )
  )
}

DATA_FILE <- existing_files[1]

FIG_DIR <- file.path(PROJECT_ROOT, "outputs", "figures", "backup")
TABLE_DIR <- file.path(PROJECT_ROOT, "outputs", "tables", "confidence_by_block")
REPORT_DIR <- file.path(PROJECT_ROOT, "outputs", "reports")

dir.create(FIG_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(TABLE_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(REPORT_DIR, recursive = TRUE, showWarnings = FALSE)

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

block_candidates <- c(
  "block", "block_index", "block_num",
  "block_number", "bloc", "trial_block"
)

block_col <- block_candidates[block_candidates %in% names(raw)][1]

if (is.na(block_col)) {
  stop(
    paste0(
      "No recognized block column was found.\n",
      "Available columns: ",
      paste(names(raw), collapse = ", ")
    )
  )
}

message("Block column used: ", block_col)
message("Étendue de l'analyse : ", CONFIDENCE_SCOPE)

dat <- raw %>%
  mutate(
    participant = factor(participant),
    base_condition = as.character(base_condition),
    soa_type = as.character(soa_type),
    response2 = as.integer(response2),
    confidence = as.numeric(confidence),
    block_raw = .data[[block_col]]
  ) %>%
  filter(
    base_condition %in% c("A1V1_A2", "A1V1_V2"),
    soa_type %in% c("short", "standard"),
    response2 %in% c(0L, 1L),
    is.finite(confidence),
    !is.na(block_raw)
  ) %>%
  mutate(
    block = dense_rank(as.numeric(as.factor(block_raw))),
    illusion_type = case_when(
      base_condition == "A1V1_A2" ~ "Fission",
      base_condition == "A1V1_V2" ~ "Fusion"
    ),
    illusion = case_when(
      illusion_type == "Fission" & response2 == 1L ~ 1L,
      illusion_type == "Fission" & response2 == 0L ~ 0L,
      illusion_type == "Fusion"  & response2 == 0L ~ 1L,
      illusion_type == "Fusion"  & response2 == 1L ~ 0L
    ),
    soa_type = factor(
      soa_type,
      levels = c("standard", "short"),
      labels = c("SOA standard", "SOA court")
    ),
    illusion_type = factor(
      illusion_type,
      levels = c("Fission", "Fusion")
    )
  ) %>%
  droplevels()

if (CONFIDENCE_SCOPE == "illusion_only") {
  dat <- dat %>% filter(illusion == 1L)
} else if (CONFIDENCE_SCOPE != "all_trials") {
  stop(
    "CONFIDENCE_SCOPE doit être égal à 'illusion_only' ou 'all_trials'."
  )
}

if (nrow(dat) == 0) {
  stop("No trials remain after filtering.")
}

dat <- dat %>%
  mutate(
    block_c = block - mean(sort(unique(block)))
  )


participant_summary <- dat %>%
  group_by(participant, illusion_type, soa_type, block) %>%
  summarise(
    n_trials = n(),
    mean_confidence = mean(confidence),
    .groups = "drop"
  )

group_summary <- participant_summary %>%
  group_by(illusion_type, soa_type, block) %>%
  summarise(
    n_participants = n(),
    mean_confidence_group = mean(mean_confidence),
    sd_confidence = sd(mean_confidence),
    sem = sd_confidence / sqrt(n_participants),
    ci_low = mean_confidence_group - 1.96 * sem,
    ci_high = mean_confidence_group + 1.96 * sem,
    .groups = "drop"
  )

write_csv(
  participant_summary,
  file.path(TABLE_DIR, "confiance_par_participant_et_bloc.csv")
)

write_csv(
  group_summary,
  file.path(TABLE_DIR, "mean_confidence_par_bloc.csv")
)


safe_lmer <- function(formula, data) {
  lmer(
    formula,
    data = data,
    REML = FALSE,
    control = lmerControl(
      optimizer = "bobyqa",
      optCtrl = list(maxfun = 200000)
    )
  )
}

lrt_row <- function(reduced, full, illusion_name, test_name) {
  tab <- anova(reduced, full)

  tibble(
    illusion_type = illusion_name,
    test = test_name,
    chi_square = tab$Chisq[2],
    df = tab$`Chi Df`[2],
    p_value = tab$`Pr(>Chisq)`[2],
    AIC_reduit = AIC(reduced),
    AIC_complet = AIC(full)
  )
}

all_tests <- list()
all_slopes <- list()
model_reports <- list()

for (illusion_name in levels(dat$illusion_type)) {

  d <- dat %>%
    filter(illusion_type == illusion_name) %>%
    droplevels()

  if (nrow(d) == 0) {
    next
  }

  m_soa <- safe_lmer(
    confidence ~ soa_type + (1 | participant),
    data = d
  )

  m_additive <- safe_lmer(
    confidence ~ block_c + soa_type + (1 | participant),
    data = d
  )

  m_interaction <- safe_lmer(
    confidence ~ block_c * soa_type + (1 | participant),
    data = d
  )

  m_block_factor <- safe_lmer(
    confidence ~ factor(block) + soa_type + (1 | participant),
    data = d
  )

  all_tests[[paste0(illusion_name, "_lineaire")]] <- lrt_row(
    m_soa,
    m_additive,
    illusion_name,
    "Effet linéaire du bloc"
  )

  all_tests[[paste0(illusion_name, "_interaction")]] <- lrt_row(
    m_additive,
    m_interaction,
    illusion_name,
    "Interaction bloc × SOA"
  )

  all_tests[[paste0(illusion_name, "_omnibus")]] <- lrt_row(
    m_soa,
    m_block_factor,
    illusion_name,
    "Effet omnibus du bloc"
  )

  beta <- lme4::fixef(m_interaction)
  V <- as.matrix(vcov(m_interaction))

  block_name <- "block_c"
  interaction_name <- grep(
    "^block_c:soa_type|^soa_type.*:block_c$",
    names(beta),
    value = TRUE
  )[1]

  slope_standard <- unname(beta[block_name])
  se_standard <- sqrt(V[block_name, block_name])

  slope_short <- slope_standard + unname(beta[interaction_name])
  var_short <- (
    V[block_name, block_name] +
    V[interaction_name, interaction_name] +
    2 * V[block_name, interaction_name]
  )
  se_short <- sqrt(var_short)

  slopes <- tibble(
    soa_type = factor(
      c("SOA standard", "SOA court"),
      levels = c("SOA standard", "SOA court")
    ),
    block_slope = c(slope_standard, slope_short),
    SE = c(se_standard, se_short),
    IC95_bas = c(
      slope_standard - 1.96 * se_standard,
      slope_short - 1.96 * se_short
    ),
    IC95_haut = c(
      slope_standard + 1.96 * se_standard,
      slope_short + 1.96 * se_short
    ),
    z = c(
      slope_standard / se_standard,
      slope_short / se_short
    ),
    p_value = 2 * pnorm(
      -abs(
        c(
          slope_standard / se_standard,
          slope_short / se_short
        )
      )
    ),
    illusion_type = illusion_name
  )

  all_slopes[[illusion_name]] <- slopes

  model_reports[[illusion_name]] <- capture.output({
    cat("============================================================\n")
    cat("TYPE D'ILLUSION :", illusion_name, "\n")
    cat("============================================================\n\n")

    cat("Number of trials:", nrow(d), "\n")
    cat("Participants:", n_distinct(d$participant), "\n\n")

    cat("Model without block\n")
    print(summary(m_soa))

    cat("\nModel with a linear block effect\n")
    print(summary(m_additive))

    cat("\nModel with block × SOA interaction\n")
    print(summary(m_interaction))

    cat("\nLikelihood-ratio tests\n")
    print(anova(m_soa, m_additive))
    print(anova(m_additive, m_interaction))
    print(anova(m_soa, m_block_factor))

    cat("\nBlock slopes by SOA\n")
    print(slopes)

    cat("\nModel singularity\n")
    cat("m_soa :", isSingular(m_soa), "\n")
    cat("m_additive :", isSingular(m_additive), "\n")
    cat("m_interaction :", isSingular(m_interaction), "\n")
    cat("m_block_factor :", isSingular(m_block_factor), "\n")
  })
}

model_tests <- bind_rows(all_tests)
block_slopes <- bind_rows(all_slopes)

write_csv(
  model_tests,
  file.path(TABLE_DIR, "tests_modeles_confiance_effet_bloc.csv")
)

write_csv(
  block_slopes,
  file.path(TABLE_DIR, "pentes_confiance_bloc_par_soa.csv")
)

writeLines(
  unlist(model_reports),
  file.path(REPORT_DIR, "rapport_confiance_par_bloc.txt")
)


annotation_data <- model_tests %>%
  filter(test == "Effet omnibus du bloc") %>%
  transmute(
    illusion_type = factor(
      illusion_type,
      levels = levels(dat$illusion_type)
    ),
    symbol = case_when(
      p_value < .001 ~ "***",
      p_value < .01 ~ "**",
      p_value < .05 ~ "*",
      TRUE ~ "ns"
    )
  ) %>%
  crossing(
    soa_type = levels(dat$soa_type)
  ) %>%
  mutate(
    soa_type = factor(soa_type, levels = levels(dat$soa_type)),
    x = max(dat$block) - 0.15,
    y = min(100, max(group_summary$ci_high, na.rm = TRUE) + 1.0),
    label_text = paste0("Effet du bloc : ", symbol)
  )


titre_figure <- if (CONFIDENCE_SCOPE == "illusion_only") {
  "Évolution de la confiance associée aux percepts illusoires"
} else {
  "Évolution de la confiance au cours de l'expérience"
}

sous_titre <- if (CONFIDENCE_SCOPE == "illusion_only") {
  paste0(
    "Fission : réponses « 2 flashs » dans A1V1_A2 ; ",
    "fusion : réponses « 1 flash » dans A1V1_V2."
  )
} else {
  "Tous les essais des conditions A1V1_A2 et A1V1_V2 sont inclus."
}

y_min <- max(50, floor(min(participant_summary$mean_confidence, na.rm = TRUE) / 5) * 5)
y_max <- min(100, ceiling(max(group_summary$ci_high, na.rm = TRUE) / 5) * 5 + 2)

p <- ggplot() +
  geom_line(
    data = participant_summary,
    aes(
      x = block,
      y = mean_confidence,
      group = participant
    ),
    colour = "grey74",
    linewidth = 0.42,
    alpha = 0.38
  ) +
  geom_point(
    data = participant_summary,
    aes(
      x = block,
      y = mean_confidence,
      group = participant
    ),
    colour = "grey64",
    size = 1.0,
    alpha = 0.45
  ) +
  geom_ribbon(
    data = group_summary,
    aes(
      x = block,
      ymin = ci_low,
      ymax = ci_high,
      group = interaction(illusion_type, soa_type)
    ),
    inherit.aes = FALSE,
    fill = "grey82",
    alpha = 0.55
  ) +
  geom_line(
    data = group_summary,
    aes(
      x = block,
      y = mean_confidence_group,
      group = interaction(illusion_type, soa_type)
    ),
    inherit.aes = FALSE,
    colour = "black",
    linewidth = 1.15
  ) +
  geom_point(
    data = group_summary,
    aes(
      x = block,
      y = mean_confidence_group
    ),
    inherit.aes = FALSE,
    colour = "black",
    fill = "white",
    shape = 21,
    stroke = 0.9,
    size = 2.35
  ) +
  geom_text(
    data = annotation_data,
    aes(
      x = x,
      y = y,
      label = label_text
    ),
    inherit.aes = FALSE,
    hjust = 1,
    vjust = 1,
    size = 3.2,
    fontface = "italic"
  ) +
  facet_grid(
    rows = vars(illusion_type),
    cols = vars(soa_type)
  ) +
  scale_x_continuous(
    breaks = sort(unique(dat$block))
  ) +
  scale_y_continuous(
    limits = c(y_min, y_max),
    breaks = seq(y_min, y_max, by = 5),
    expand = expansion(mult = c(0.02, 0.04))
  ) +
  labs(
    title = titre_figure,
    subtitle = paste0(
      sous_titre,
      " Les lignes grises représentent les trajectoires individuelles ; ",
      "la ligne noire représente la mean_confidence_group de groupe."
    ),
    x = "Bloc",
    y = "Confiance mean_confidence_group (%)",
    caption = paste0(
      "La significativité indiquée correspond au test omnibus de l'effet ",
      "du bloc dans un modèle linéaire mixte gaussien ajusté pour le SOA. ",
      "ns : non significatif."
    )
  ) +
  theme_classic(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", size = 14),
    plot.subtitle = element_text(size = 10.2),
    plot.caption = element_text(
      size = 8.5,
      hjust = 0,
      margin = margin(t = 8)
    ),
    strip.background = element_blank(),
    strip.text = element_text(face = "bold", size = 11),
    axis.title = element_text(size = 11),
    axis.text = element_text(size = 10),
    legend.position = "none",
    panel.spacing = grid::unit(1.1, "lines"),
    plot.margin = margin(10, 14, 10, 10)
  )

suffix <- if (CONFIDENCE_SCOPE == "illusion_only") {
  "percepts_illusoires"
} else {
  "tous_essais"
}

pdf_path <- file.path(
  FIG_DIR,
  paste0("evolution_confiance_par_bloc_", suffix, "_fr.pdf")
)

png_path <- file.path(
  FIG_DIR,
  paste0("evolution_confiance_par_bloc_", suffix, "_fr.png")
)

ggsave(
  filename = pdf_path,
  plot = p,
  width = 10.5,
  height = 7.2,
  units = "in",
  device = cairo_pdf
)

ggsave(
  filename = png_path,
  plot = p,
  width = 10.5,
  height = 7.2,
  units = "in",
  dpi = 300
)

cat("\nAnalysis completed.\n")
cat("PDF figure: ", pdf_path, "\n", sep = "")
cat("PNG figure: ", png_path, "\n", sep = "")
cat(
  "Tests : ",
  file.path(TABLE_DIR, "tests_modeles_confiance_effet_bloc.csv"),
  "\n",
  sep = ""
)
