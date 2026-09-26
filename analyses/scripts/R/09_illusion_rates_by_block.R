# ============================================================
# Trial-level block analysis of fission and fusion illusion rates, with participant trajectories and group summaries.
# Run from the repository root unless stated otherwise.
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(lme4)
  library(emmeans)
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
TABLE_DIR <- file.path(PROJECT_ROOT, "outputs", "tables", "illusion_by_block")
REPORT_DIR <- file.path(PROJECT_ROOT, "outputs", "reports")

dir.create(FIG_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(TABLE_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(REPORT_DIR, recursive = TRUE, showWarnings = FALSE)

raw <- read_csv(DATA_FILE, show_col_types = FALSE)

required_columns <- c("participant", "base_condition", "soa_type", "response2")
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

dat <- raw %>%
  mutate(
    participant = factor(participant),
    base_condition = as.character(base_condition),
    soa_type = as.character(soa_type),
    response2 = as.integer(response2),
    block_raw = .data[[block_col]]
  ) %>%
  filter(
    base_condition %in% c("A1V1_A2", "A1V1_V2"),
    soa_type %in% c("short", "standard"),
    response2 %in% c(0L, 1L),
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
    ),
    block_c = block - mean(sort(unique(block)))
  ) %>%
  droplevels()

participant_rates <- dat %>%
  group_by(participant, illusion_type, soa_type, block) %>%
  summarise(
    n_trials = n(),
    n_illusions = sum(illusion),
    illusion_rate = mean(illusion),
    .groups = "drop"
  )

group_rates <- participant_rates %>%
  group_by(illusion_type, soa_type, block) %>%
  summarise(
    n_participants = n(),
    mean_rate = mean(illusion_rate),
    sd_rate = sd(illusion_rate),
    sem = sd_rate / sqrt(n_participants),
    ci_low = pmax(0, mean_rate - 1.96 * sem),
    ci_high = pmin(1, mean_rate + 1.96 * sem),
    .groups = "drop"
  )

safe_glmer <- function(formula, data) {
  glmer(
    formula,
    data = data,
    family = binomial(link = "logit"),
    control = glmerControl(
      optimizer = "bobyqa",
      optCtrl = list(maxfun = 200000)
    )
  )
}

lrt_row <- function(reduced, full, illusion_name, test_name) {
  tab <- anova(reduced, full, test = "Chisq")
  tibble(
    illusion_type = illusion_name,
    test = test_name,
    chi_square = tab$Chisq[2],
    df = tab$Df[2],
    p_value = tab$`Pr(>Chisq)`[2]
  )
}

all_tests <- list()
all_slopes <- list()
model_reports <- list()

for (illusion_name in levels(dat$illusion_type)) {

  d <- dat %>%
    filter(illusion_type == illusion_name) %>%
    droplevels()

  m_soa <- safe_glmer(
    illusion ~ soa_type + (1 | participant),
    data = d
  )

  m_additive <- safe_glmer(
    illusion ~ block_c + soa_type + (1 | participant),
    data = d
  )

  m_interaction <- safe_glmer(
    illusion ~ block_c * soa_type + (1 | participant),
    data = d
  )

  m_block_factor <- safe_glmer(
    illusion ~ factor(block) + soa_type + (1 | participant),
    data = d
  )

  all_tests[[paste0(illusion_name, "_lineaire")]] <- lrt_row(
    m_soa, m_additive, illusion_name, "Effet linéaire du bloc"
  )

  all_tests[[paste0(illusion_name, "_interaction")]] <- lrt_row(
    m_additive, m_interaction, illusion_name, "Interaction bloc × SOA"
  )

  all_tests[[paste0(illusion_name, "_omnibus")]] <- lrt_row(
    m_soa, m_block_factor, illusion_name, "Effet omnibus du bloc"
  )

  slopes <- emtrends(
    m_interaction,
    specs = ~ soa_type,
    var = "block_c"
  ) %>%
    summary(infer = c(TRUE, TRUE)) %>%
    as.data.frame() %>%
    as_tibble() %>%
    mutate(illusion_type = illusion_name)

  all_slopes[[illusion_name]] <- slopes

  model_reports[[illusion_name]] <- capture.output({
    cat("============================================================\n")
    cat("ILLUSION :", illusion_name, "\n")
    cat("============================================================\n\n")
    cat("Likelihood-ratio tests\n")
    print(anova(m_soa, m_additive, test = "Chisq"))
    print(anova(m_additive, m_interaction, test = "Chisq"))
    print(anova(m_soa, m_block_factor, test = "Chisq"))
    cat("\nBlock slopes by SOA\n")
    print(slopes)
  })
}

model_tests <- bind_rows(all_tests)
block_slopes <- bind_rows(all_slopes)

write_csv(
  participant_rates,
  file.path(TABLE_DIR, "illusion_rate_par_participant_et_bloc.csv")
)

write_csv(
  group_rates,
  file.path(TABLE_DIR, "illusion_rate_moyen_par_bloc.csv")
)

write_csv(
  model_tests,
  file.path(TABLE_DIR, "tests_modeles_effet_bloc.csv")
)

write_csv(
  block_slopes,
  file.path(TABLE_DIR, "pentes_bloc_par_soa.csv")
)

writeLines(
  unlist(model_reports),
  file.path(REPORT_DIR, "rapport_modeles_illusion_rate_par_bloc.txt")
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
    y = 0.965,
    label_text = paste0("Effet du bloc : ", symbol)
  )

p <- ggplot() +
  geom_line(
    data = participant_rates,
    aes(
      x = block,
      y = illusion_rate,
      group = participant
    ),
    colour = "grey74",
    linewidth = 0.42,
    alpha = 0.38
  ) +
  geom_point(
    data = participant_rates,
    aes(
      x = block,
      y = illusion_rate,
      group = participant
    ),
    colour = "grey64",
    size = 1.0,
    alpha = 0.45
  ) +
  geom_ribbon(
    data = group_rates,
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
    data = group_rates,
    aes(
      x = block,
      y = mean_rate,
      group = interaction(illusion_type, soa_type)
    ),
    inherit.aes = FALSE,
    colour = "black",
    linewidth = 1.15
  ) +
  geom_point(
    data = group_rates,
    aes(
      x = block,
      y = mean_rate
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
    limits = c(0, 1),
    breaks = seq(0, 1, 0.2),
    labels = label_percent(accuracy = 1),
    expand = expansion(mult = c(0.02, 0.04))
  ) +
  labs(
    title = "Évolution du taux d'illusion au cours de l'expérience",
    subtitle = paste0(
      "Les lignes grises représentent les trajectoires individuelles ; ",
      "la ligne noire représente la mean_rate de groupe."
    ),
    x = "Bloc",
    y = "Taux d'illusion",
    caption = paste0(
      "La significativité indiquée correspond au test omnibus de l'effet ",
      "du bloc dans un GLMM binomial ajusté pour le SOA. ",
      "ns : non significatif."
    )
  ) +
  theme_classic(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", size = 14),
    plot.subtitle = element_text(size = 10.5),
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

ggsave(
  filename = file.path(FIG_DIR, "evolution_illusion_rate_par_bloc_fr.pdf"),
  plot = p,
  width = 10.5,
  height = 7.2,
  units = "in",
  device = cairo_pdf
)

ggsave(
  filename = file.path(FIG_DIR, "evolution_illusion_rate_par_bloc_fr.png"),
  plot = p,
  width = 10.5,
  height = 7.2,
  units = "in",
  dpi = 300
)

cat("\nAnalysis completed.\n")
cat(
  "Figure: ",
  file.path(FIG_DIR, "evolution_illusion_rate_par_bloc_fr.pdf"),
  "\n",
  sep = ""
)
