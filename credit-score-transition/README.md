# Credit Score Transition: Classic FICO vs FICO 10T vs VantageScore 4.0

In 2026 the mortgage market began moving off Classic FICO. FHFA cleared lenders to deliver
VantageScore 4.0, and Freddie Mac published historical FICO 10T and VantageScore 4.0 scores
for loans it already owns. This project asks the business question a lender or investor faces:
**if we switch scores, who gets approved differently, and what happens to default rates?**

## Data

| Source | What it gives | Rows used |
| --- | --- | --- |
| Freddie Mac Single-Family Loan-Level Dataset, Release 48 (sample files, 2018–2026 vintages) | Origination attributes, Classic FICO, monthly performance through June 2026 | 425,000 loans |
| Freddie Mac historical FICO 10T file for SFLLD (July 2026) | FICO 10T at origination, five merge methods | 381,722 matched loans |
| Freddie Mac historical VantageScore 4.0 files for SFLLD (July 2024 + July 2026 supplement) | VantageScore 4.0 at origination, five merge methods | 381,804 matched loans |

Raw data is not redistributed. Register at Freddie Mac Clarity (SFLLD) and InvestorSet
(historical score files), then place the unzipped files in `data/extract/`.

## Method

- **Outcome:** 90+ days delinquent, or a credit-loss termination, within 24 months of first payment.
- **Headline cohort:** 2021–2023 vintages (149,860 loans, 2,300 defaults), which avoids COVID
  forbearance distorting delinquency. 2018–2020 vintages are reported as a robustness check.
- **Like-for-like scoring:** the main comparison uses each new score's "Current Method"
  (middle-of-three bureaus, then lowest borrower), which matches how Classic FICO is reported.
- **Metrics:** Gini, KS, share of defaults captured in the lowest-scored 10% / 20%, paired
  bootstrap 95% confidence intervals on the Gini difference, and swap-set analysis at equal decline rates.

## First results (2021–2023 vintages)

| Score | Gini | KS | Defaults caught in lowest 10% |
| --- | --- | --- | --- |
| Classic FICO | 0.515 | 0.403 | 35.5% |
| FICO 10T | 0.585 | 0.451 | 42.4% |
| VantageScore 4.0 | 0.552 | 0.424 | 40.5% |

- FICO 10T lifts Gini by **+7.0 points** over Classic FICO (95% CI +5.8 to +8.2);
  VantageScore 4.0 by **+3.7 points** (95% CI +2.2 to +5.0).
- **Swap sets:** declining the lowest-scored 10% under FICO 10T instead of Classic FICO swaps
  about 6,500 borrowers each way. The newly declined group defaults at 5.3%, compared with 2.5%
  for the newly approved group: about 11 fewer defaults per 10,000 loans at the same approval rate.
- **Biggest gain is among sub-700 borrowers:** within Classic FICO < 700, Classic FICO's Gini is
  0.19 while FICO 10T reaches 0.37, which means it nearly doubles rank-ordering where lending
  decisions are hardest.
- **Bi-merge does not lose power:** the bi-merge lowest and tri-merge average versions of both
  new scores rank risk slightly better than the tri-merge Current Method.
- The ranking holds in the COVID-affected 2018–2020 vintages (FICO 10T +3.5 Gini points), and
  for both early (months 1–12) and later (months 13–24) defaults.

## Caveats

- **Selection effect:** every loan was approved using Classic FICO, so its range is truncated in
  this population. That likely understates Classic FICO's power relative to the new scores.
- **Archive timing:** the new scores come from bureau archives that may not match the exact
  date of the lender's credit pull (Freddie Mac disclaimer 2). Similar lift for early and late
  defaults suggests this isn't driving the result, but it can't be ruled out.
- **Survivorship:** only originated, GSE-acquired loans are observed; declined applicants are not.

## Reproduce

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python src/build_db.py       # builds data/sflld.duckdb (~10 s)
.venv/bin/python src/audit.py          # data quality / realism checks
.venv/bin/python src/compare_scores.py # writes outputs/*.csv
```
