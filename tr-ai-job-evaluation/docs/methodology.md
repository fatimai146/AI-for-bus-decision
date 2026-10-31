# Methodology

## 1. Data

| Source | Use |
|---|---|
| SAO job description PDFs (386 files, one per job family) | Text the models read |
| SAO job class list + Comptroller FY 2026–27 salary schedule | Official salary group and range midpoint for each class (the target) |
| SAO report 27-701 (October 2026) | Jobs the Auditor recommends reallocating to a higher group (external check) |
| O\*NET 31.0 (Occupation Data, Task Statements, Job Titles) | 1,016 occupations to match against |
| Texas state payroll (Texas Tribune) | Headcount and female share per class, for weighting and the gender check only |

**Scope.** 1,246 classes parsed. Grading uses the 1,165 classes on Schedule A (248) and Schedule B (917).
Schedule C (law-enforcement ranks) has a step structure rather than salary groups, so it is excluded.

## 2. Parsing and leakage control

`parse_jobs.py` extracts text from each PDF with `pypdf`, strips page headers and footers, and splits it
into the standard SAO sections (General Description, Examples of Work Performed, Description of Levels,
Knowledge/Skills/Abilities, and so on).

- **Family text:** the family-wide sections, shared by every level in the series.
- **Level text:** the paragraph in "Description of Levels" that belongs to one class. A level marker is
  matched when its series name is at least 80% similar to the class series (this tolerates typos in the
  PDFs) and its roman numeral matches exactly. 95.1% of multi-level classes get a level paragraph.
- **Leakage scrub:** dollar amounts, salary-group codes (for example `B17`), and revision notes are removed
  before modeling, so the model cannot read the answer from the text.

## 3. Embeddings

`embed.py` encodes text with BAAI `bge-base-en-v1.5` (768 dimensions, normalized) through
`sentence-transformers` on CPU. Four sets are produced:

- job family text;
- job family text with the model's retrieval prefix, used as the query side for matching;
- class title plus level paragraph;
- O\*NET occupations: title, description, and up to 8 core task statements.

## 4. Job grading (`job_grading.py`)

**Target:** log of the official salary-range midpoint.

**Validation:** 5-fold `GroupKFold` grouped by job-family PDF, shuffled with seed 0. Every level of a
family is held out together, so the model is always grading a family it has never seen. Without grouping,
the model could interpolate between levels II and IV to get level III, which would overstate accuracy.

**Models:**

| Model | Features | Estimator |
|---|---|---|
| Baseline | none | median of training folds |
| Keyword | family + title + level text, unigrams and bigrams, `min_df=2`, sublinear tf | TF-IDF + `RidgeCV` |
| AI (three variants) | family embedding, title+level embedding, or both concatenated | `SVR(C=1, epsilon=0.05)` |
| Ensemble | average of the keyword and full AI predictions | — |

**Metrics:**
- out-of-sample R² on log midpoint;
- median and mean absolute percentage error of the midpoint;
- salary-group distance: the predicted midpoint is snapped to the nearest group on the class's schedule
  and compared with the official group, giving exact, within 1, and within 2 group shares.

**Confidence routing:** for each job, the standard deviation of official grades among its 10 most similar
training families (by embedding cosine similarity). Jobs with the lowest spread are auto-accepted, and
accuracy is reported at 80%, 60%, and 40% auto-acceptance. An earlier version used disagreement between the
keyword and AI models as the signal and did not improve accuracy, so it was replaced.

## 5. Checks (`grading_checks.py`)

**Review list.** Jobs whose ensemble grade differs from the official grade by 3 or more groups, with
current headcount. These are leads for a human review, not conclusions.

**Auditor comparison.** Class codes on "Reallocation" lines of report 27-701 are extracted (190 match the
1,165 graded classes). The AUC measures how well the AI-minus-official gap separates recommended from
non-recommended classes.

**Gender check.** Class-level regression:

\[
\text{official log midpoint} - \text{predicted log midpoint} = \alpha + \beta \cdot \text{female share} + \varepsilon
\]

Standard errors are clustered by job family, because levels of one family share text and errors.

| Specification | Detail |
|---|---|
| (1) | classes with 20 or more employees |
| (2) | (1) plus occupational-category fixed effects |
| (3) | (1) weighted by headcount |
| (4) | classes with 100 or more employees |

\(\beta\) is reported as the percentage gap between an all-female and an all-male class. With
heteroskedasticity-robust (unclustered) standard errors, specification (1) looked significant. Once errors
are clustered by family, no specification is significant, and that clustered result is the one reported.

## 6. Market matching (`market_match.py`)

**Unit:** the 386 job families. Each family is matched to 6-digit SOC codes. O\*NET detailed occupations
are collapsed to SOC6 by taking the maximum score, because BLS wage data is published at SOC6.

| Method | Score |
|---|---|
| Title | TF-IDF cosine between the family name and each occupation's title plus its O\*NET "Job Titles" list (lay titles used in job postings) |
| AI | cosine between the family-text query embedding and the O\*NET occupation embedding |
| Hybrid | the average of the two after min-max scaling each family's scores to 0–1; equal weights, no tuning |

**Labels:** 65 families were hand-labeled with a primary SOC code and any other acceptable codes, chosen
across occupational categories. The labels are published in `labels/market_match_labels.csv`. A match is correct if it is in the
acceptable set.

**Routing:** the margin between the hybrid's first and second scores. Accuracy is reported for the
most confident 75% and 50% of labeled families. Suggestions with top-3 codes and the margin are written
for all 386 families.

## 7. Reproducibility

All randomness is seeded (`SEED = 0`). Two full runs of `run_all.sh` produced byte-identical output files.
