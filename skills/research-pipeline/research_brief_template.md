# Research Brief: [Title of Your Research Project]

<!-- RESEARCH BRIEF TEMPLATE v1.0
     Single source of truth for all domain-specific configuration in the
     generalized research pipeline. The 10 pipeline skills read this file;
     they contain no domain knowledge of their own.
     Instructions appear in HTML comments. Delete them after filling in.
     Lines starting with "e.g." are examples — replace with your content. -->

## 1. Problem Statement

**Domain**: <!-- e.g., computational biology, econometrics, NLP -->
**Research area**: <!-- e.g., protein structure prediction, causal inference -->

**Core challenge**: <!-- 1-2 sentences. What is hard and why? -->

**Why existing approaches fall short**:
<!-- Bullet list: what current methods miss, get wrong, or cannot handle. -->

**Abstract problem formulation**:
<!-- Strip away domain specifics so the methodology architect can search
     across disciplines. Format as a blockquote. -->
> Given [input/setting], how do you optimally [objective] — while being
> robust to [key failure mode]?

## 2. Data Assets

### Primary Dataset
- **Description**: <!-- What does each row represent? -->
- **Location**: <!-- Relative path, e.g., data/trials_data.csv -->
- **Size**: <!-- e.g., 35 rows x 8 columns, 10 GB images -->
- **Key columns/features**: <!-- List the columns or features that matter -->
- **Response/outcome variable**: <!-- What are we trying to estimate or predict? -->

### Secondary Datasets
<!-- Repeat the block above for each additional dataset, or write "None." -->

### Data Quirks and Known Issues
<!-- Missing values, class imbalance, measurement error, censoring, etc. -->

### Infrastructure Code
<!-- Existing scripts for data loading/cleaning/preprocessing.
     e.g., data_curation.py — loading, cleaning, simulation -->

## 3. Domain Context

### Key Terminology
<!-- Define 5-15 terms a non-specialist needs. Use a definition-list format. -->

### Domain Constraints
<!-- Regulatory, ethical, computational, or practical constraints.
     e.g., FDA requires pre-specified analysis plans -->

### Standards and Conventions
<!-- Notation, workflow, or evaluation protocols the field uses.
     e.g., CONSORT reporting, ImageNet benchmark protocol -->

### Practitioner Expectations
<!-- What does the target audience need from a new method?
     e.g., interpretability, reproducibility, toolchain integration -->

## 4. Target Venue

**Name**: <!-- Default candidate set: JASA, JRSS-B, JRSS-C, Biometrika,
     Biometrics, Annals of Statistics, Annals of Applied Statistics,
     Bayesian Analysis. Pick one or list 2-3 candidates; methodology and
     evaluation drive the final choice. -->

### Audience
<!-- Who reads this venue? What is their background? -->

### Quality Expectations
<!-- Default for top-tier statistics venues: aim high on all of the below.
     Override only with explicit reason. -->
- [x] Rigorous theory (proofs, convergence guarantees, identifiability)
- [x] Comprehensive empirical evaluation (simulation + real data)
- [x] Comparison to established baselines
- [x] Reproducibility (code, data availability)
- [x] Clear practical value to statisticians and applied users
- [ ] Real-world application / case study (required for JRSS-C, AoAS,
      Biometrics; optional for AoS, Biometrika)

### Format Requirements (optional — fill at submission time)
<!-- Leave blank during drafting. Fill in only when you've chosen a specific
     submission target and are ready to format. The pipeline aims for
     top-tier journal quality regardless of formatting until ready to
     submit. Run with `venue_compliance=on` once these are filled. -->
- **Document class / template**: <!-- e.g., jasa.cls, biomka.cls -->
- **Page/word limit**: <!-- e.g., 30 pages main text -->
- **Citation style**: <!-- e.g., author-year -->
- **Supplementary material**: <!-- Allowed? Required? Separate file? -->

## 5. Success Criteria

### Primary Metric(s)
<!-- Name, definition, meaningful improvement threshold.
     e.g., MSE of point estimates; 5%+ improvement over best baseline -->

### Secondary Metrics
<!-- Additional metrics that matter but are not the headline result. -->

### Calibration / Uncertainty
<!-- e.g., 95% CI coverage in [0.90, 0.97]; well-calibrated probabilities -->

### Robustness
<!-- What should the method withstand? e.g., irrelevant sources, missing data -->

### Computational Requirements
<!-- e.g., interactive speed (< 10 sec), trainable overnight on 1 GPU -->

### Deployability
<!-- Can practitioners use this? What infrastructure does it assume? -->

### Interpretability
<!-- How important is it that users understand WHY the method gives its answer? -->

## 6. Comparator Methods

<!-- ALL listed comparators MUST appear in ALL evaluation tables — the pipeline
     enforces this. 4-8 comparators is typical. -->

| # | Name | Reference | Brief Description | Why Included |
|---|------|-----------|-------------------|--------------|
| 1 | <!-- e.g., Pooled --> | <!-- citation --> | <!-- 1 sentence --> | <!-- reason --> |
| 2 | | | | |
| 3 | | | | |

## 7. Adjacent Fields

<!-- Helps the methodology architect search OUTSIDE your home field. -->

**Abstract version of the problem**:
<!-- Restate the problem in domain-neutral language (can repeat from Sec 1). -->

**Fields with analogous challenges** (list 3-6):

| Field | Analogous Concept | Key Reference |
|-------|-------------------|---------------|
| <!-- e.g., transfer learning --> | <!-- e.g., domain adaptation with source selection --> | <!-- author, year --> |
| | | |
| | | |

## 8. Evaluation Design

### Computational Budgets

| Stage | Replicates | Time Limit | Purpose |
|-------|-----------|------------|---------|
| Quick validation | <!-- e.g., 200 --> | <!-- e.g., 5 min --> | Sanity check during development |
| Stress test | <!-- e.g., 500 --> | <!-- e.g., 30 min --> | Robustness under edge cases |
| Production | <!-- e.g., 2000 --> | <!-- e.g., 2 hr --> | Final numbers for the paper |

### Evaluation Types
<!-- Check all that apply. -->
- [ ] Simulation study (synthetic data, known ground truth)
- [ ] Cross-validation (leave-one-out, k-fold, etc.)
- [ ] Held-out real data
- [ ] Sensitivity analysis (hyperparameters, assumptions)
- [ ] Robustness / stress tests (adversarial scenarios)
- [ ] Scalability benchmarks

### Random Seed Convention
<!-- e.g., base seed 42, increment by 1 per replicate -->

### Key Stress-Test Scenarios
<!-- Specific scenarios the method must survive.
     e.g., "Add 10 irrelevant sources, verify < 2% degradation" -->

## 9. Scope and Non-Goals

<!-- This section is intentionally light. Aim for the highest-quality
     contribution; do not pre-emptively narrow scope to fit a perceived
     constraint. If a constraint genuinely caps the contribution,
     methodology-architect will surface it during Phase 1. -->

### Known Limitations to Acknowledge
<!-- Real, structural limitations to state upfront in the paper rather than
     try to fix. e.g., "Assumes exchangeability of historical trials." -->

### Out-of-Scope (only if truly necessary)
<!-- Leave blank unless there is a concrete reason to exclude a direction.
     A blank list is better than a defensive one. -->
<!-- e.g., "Time-to-event extension — orthogonal modeling effort, separate
     paper." -->

## 10. Reference Papers

**Directory**: <!-- e.g., reference/ -->

### Key Papers
<!-- Optional: 3-5 must-read papers with one-line descriptions.
     e.g., Schmidli et al. (2014) — robust MAP prior for historical borrowing -->
