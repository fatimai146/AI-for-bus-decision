# Methodology and Data-Quality Audit

## 1. Source files

| File | Format | Records |
| --- | --- | --- |
| `sample_orig_YYYY.txt` (2018–2026) | Pipe-delimited, no header, 31 fields (Release 47+ layout) | 50,000 per year; 25,000 for 2026 |
| `sample_perf_YYYY.txt` | Pipe-delimited, no header, 35 fields, one row per loan-month | ~0.5M–9M rows per year |
| `FRE_FICO10T_SFLLD_Historical.txt` | Pipe-delimited with header | 22,805,996 loans (2013–Q3 2025) |
| `FRE_VS4_SFLLD_Historical.txt` | Pipe-delimited with header, CRLF line endings | 20,196,180 loans (2013–2022) |
| `FRE_VS4_2023-Q32025_SFLLD_Historical.txt` | Pipe-delimited with header, LF line endings | 2,621,321 loans (2023–Q3 2025) |

Column layouts are in [`src/schema.py`](../src/schema.py). Release 47 (July 2026) added
VantageScore 4.0 as the last origination field and moved Servicer Name and the mortgage-insurance
cancellation indicator to the performance file.

Note: the two VantageScore files have different line endings. DuckDB's multi-file `read_csv`
silently dropped the second file, so each file is read separately and stacked.

## 2. Join

All tables join on the 12-character **Loan Identifier** (`PYYQnXXXXXXX`: product, year, quarter,
random digits). The historical score files cover the full SFLLD population; the sample loans are a
subset, so the score files are semi-joined to the sample.

## 3. Database tables (`data/sflld.duckdb`)

| Table | Grain | Key derived fields |
| --- | --- | --- |
| `orig` | loan | `vintage`, `fico` (9999 → null), `ltv`/`cltv`/`dti`/`mi_pct` (999 → null) |
| `perf_loan` | loan | `age_first_d90`: first loan age at 90+ days delinquent or credit-loss termination; `age_first_d60`; `zero_bal_code`; `ever_forbearance`; `actual_loss` |
| `scores` | loan | FICO 10T and VS4: Current Method, Tri-Merge average, Bi-Merge lowest / median / highest |

## 4. Definitions

| Term | Definition |
| --- | --- |
| Default (headline) | Delinquency status ≥ 3 (90+ days) **or** zero-balance code 02 / 03 / 09 / 15 (third-party sale, short sale / charge-off, REO, whole-loan sale) at loan age ≤ 24 months |
| Default (alternative) | 60+ days delinquent at loan age ≤ 24 months |
| Prepaid loans | Counted as non-default (standard "ever-bad within window" convention) |
| Current Method | Middle of 3 bureau scores (or lower of 2) per borrower, then lowest borrower; matches Classic FICO |
| Tri-Merge average | Average of available bureau scores per borrower, then average across borrowers |
| Bi-Merge lowest | Lowest of the three possible two-bureau average combinations |
| Gini | 2 × AUC − 1, with lower score = higher predicted risk |
| KS | Maximum gap between cumulative default and non-default distributions |
| Capture @10% | Share of all defaults among the lowest-scored 10% of loans (ties broken randomly, fixed seed) |
| Swap set | Loans approved under one score but declined under the other at the same decline rate |
| Expected loss | Defaulted original balance × 25% assumed severity ÷ approved original balance |

**Loss severity.** Only 275 sample loans have realized losses in the window (mean ~26% of the
balance at removal), so the simulator uses a fixed 25% severity rather than modelling loss.

**Bootstrap.** 300 paired resamples of the headline cohort; each resample computes Gini for both
scores on the same loans, giving a confidence interval for the difference.

## 5. Data-quality audit (`src/audit.py`)

| Check | Result |
| --- | --- |
| Duplicate loan IDs (origination, FICO 10T, VS4) | 0 / 0 / 0 |
| Classic FICO present | 100% of 2018–2025 loans |
| FICO 10T and VS4 matched | 99.8–100% of 2018–2024 loans; 64% of 2025 (files end Q3 2025); 0% of 2026 |
| Score ranges | All within 300–850 (Classic FICO 427–848; FICO 10T 434–850; VS4 421–850) |
| Bi-merge ordering (lowest ≤ median ≤ highest) | Holds for every loan with all three values |
| Correlations | Classic FICO vs FICO 10T 0.80; Classic FICO vs VS4 0.74; FICO 10T vs VS4 0.84 |
| Interest rates by vintage | 2.97% (2021) to 6.74% (2023), matching the market rate path |
| Refinance share | Peaks in 2020–2021 (purchase share 30–34%), matching the refinance boom |
| Prepayment | 80% of 2018 loans prepaid, matching the 2020–21 refinance wave |
| COVID signal | Forbearance flags peak in 2018–2019 vintages (6.5–7.0% of loans) |
| Default monotonic in Classic FICO | <660: 7.7% · 660–699: 4.8% · 700–739: 3.1% · 740–779: 1.6% · 780+: 0.7% |

Two pipeline bugs were caught during the audit and fixed before any results were produced:
1. A null-handling error in SQL averages (nulls dropped instead of counted as "no event") briefly
   showed ~99% of loans as prepaid.
2. The second VantageScore file was silently skipped on load (line-ending mismatch, see §1).

## 6. Cohort choice

| Cohort | Loans | Defaults | Why |
| --- | --- | --- | --- |
| 2021–2023 (headline) | 149,860 | 2,300 | Full 24-month window observed; little COVID forbearance |
| 2018–2020 (robustness) | 149,858 | 4,476 | Default flag inflated by 2020–21 forbearance-related delinquency |
| 2024–2026 | Excluded | | 24-month window not yet complete |

## 7. Limitations

1. **Selection.** All loans were approved and purchased using Classic FICO; declined applicants
   are not observed. Tested in [`src/robustness.py`](../src/robustness.py) (incremental models and
   within-band Gini), but effects on declined applicants cannot be estimated.
2. **Archive timing.** The new scores come from bureau archives taken near, not at, the lender's
   credit pull. Similar lift for early and later defaults suggests this doesn't drive the results.
3. **Archive content.** Later reporting changes (e.g., medical collections, rent reporting) are not
   reflected in older archives.
4. **Sample.** SFLLD standard sample files (50,000 loans per year) exclude the non-standard
   population (e.g., government-insured loans).
