# Methodology

## 1. Sources

| File | Source | Notes |
|---|---|---|
| `tx_payroll.csv` | Texas Tribune, non-duplicated employees file dated 2026-10-01 | Obtained by the Tribune from the Texas Comptroller under the Texas Public Information Act. One row per employee job. |
| `sao_job_classes.html` | Texas State Auditor's Office job classification index | Class code, title, salary group and occupational category for 1,246 classified titles. |
| `salary_schedule_fy26_27.html` | Texas Comptroller, FY2026–27 salary schedules | Annual min/max for Schedule A (A5–A22) and B (B10–B37). Schedule C (law enforcement) uses tenure steps, not ranges. |
| `oews_api.json` | BLS OEWS May 2025 via `api.bls.gov` | Employment and 25th/50th/75th percentile annual wages for 19 occupation codes in Texas and the Austin-Round Rock-San Marcos metro area. |

## 2. Analysis population

Starting from 154,795 payroll rows:

1. Keep **regular full-time classified** employees (`CRF`, 145,822).
2. Drop records the Tribune flags as part of a multi-job person (`duplicated`).
3. Drop 3 records with hire dates after the snapshot (2069–2073, data-entry errors).
4. Keep employees whose job class maps to a **Schedule A or B** salary group
   (drops 6,159 Schedule C law-enforcement employees).

Result: **139,656 employees, 103 agencies, 1,081 job titles**. All are on a
40-hour week. Every one maps to an official job class; none is above the range
maximum. 921 are below the minimum, but the median shortfall is $0.08
(rounding), and only 3 are short by more than $1.

**Tenure** = years from hire date to October 1, 2026. Bands: 0–2, 2–5, 5–10,
10–20, 20+. A "new hire" has under 2 years; "tenured" means 10+ years.

## 3. Compression

**Tenure premium.** For employee *i* in group *g*:

log(salary) = Σ β_b · 1[tenure band = b] + α_g + ε

with the 0–2 year band as reference. Three versions:

| Version | Group fixed effect α_g | Purpose |
|---|---|---|
| Same job title, same agency | agency × class code | Main estimate |
| Same job series, same agency | agency × series (e.g. all Accountant levels) | Includes promotions |
| Entry-level titles only | agency × class code, entry-level titles only | Robustness check (see below) |

Fixed effects are removed by demeaning within group. Standard errors are
clustered by group. Premiums are reported as exp(β) − 1.

**Robustness to the hire-date limitation.** The payroll's hire date may predate
entry into the current title. A veteran promoted into a title last year would
look like a long-tenured incumbent and could make compression look worse.
Entry-level titles (the lowest level of a multi-level series, e.g.
Accountant I) cannot be reached by promotion from below in the same series. The
premium there is similar (6.9% at 10–20 years vs 5.3% overall), so the finding
is not explained by this.

**Title-level test.** For each job title with at least 20 new hires (<2 years)
and 20 staff with 10+ years, restricted to those two groups:

log(salary) = β · 1[10+ years] + α_agency + ε

β is estimated by demeaning within agency, with heteroskedasticity-robust
(HC1) standard errors. Each title is classified as: new hires paid
significantly more (CI entirely below 0); no significant difference (CI
includes 0); veterans paid more but under 5%; or veterans paid 5%+ more.

**Why raw median ratios are not used.** A common shortcut is to compare the
new-hire median with the 10+ year median in each agency × title group and call
the group "compressed" (ratio ≥ 0.95) or "inverted" (≥ 1.00). A shuffle test
shows this is uninformative here. Tenure is randomly permuted within each group
200 times, which removes any real tenure effect. Under that null, 93% of the
353 groups look compressed and 66% look inverted, versus 69% and 41% in the
real data. Small groups and many identical salaries make median comparisons
noisy. Statewide (cross-agency) medians are also confounded by which agencies
are hiring. For example, Human Resources Specialist IV shows new hires 12%
ahead statewide, but within agencies veterans are 1.9% ahead (not significant).

## 4. Range position

- Range penetration = (salary − range min) ÷ (range max − range min)
- Compa-ratio = salary ÷ range midpoint

## 5. Cost to fix

New-hire reference = the median salary of employees with under 2 years in the
same agency × job title, where there are at least 5 such hires.

| Scenario | Who is eligible | Target |
|---|---|---|
| A. Compression floor | 5+ years of tenure | New-hire median |
| B. Floor + tenure step | 2+ years of tenure | New-hire median × (1 + 1% × (tenure − 2)), with the step capped at 10% |

Raise = max(0, min(target, range max) − salary). Totals are annual base pay,
excluding benefits and payroll taxes. These cost a policy; they are not
estimates of underpayment, because some gap below any median is ordinary pay
spread.

## 6. Pay equity

Four nested models of log(salary), each with indicators for female and for
each ethnicity (reference: White):

1. No controls (raw gap)
2. Job-title fixed effects
3. Agency × job-title fixed effects
4. Model 3 + tenure and tenure²

Standard errors are clustered by agency × job title. Per-agency gender gaps use
model 4 within each of the 28 agencies with 300+ employees and 50+ of each
gender. A gap is flagged if its 95% confidence interval excludes zero.

## 7. Market comparison

Each benchmark state job series (all levels pooled) is mapped to one 2018 SOC
code:

| State series | SOC | Federal occupation |
|---|---|---|
| Accountant, Auditor | 13-2011 | Accountants and Auditors |
| Budget Analyst | 13-2031 | Budget Analysts |
| Financial Analyst | 13-2051 | Financial and Investment Analysts |
| Human Resources Specialist | 13-1071 | Human Resources Specialists |
| Training and Development Specialist | 13-1151 | Training and Development Specialists |
| Purchaser | 13-1020 | Buyers and Purchasing Agents |
| Management Analyst | 13-1111 | Management Analysts |
| Project Manager | 13-1082 | Project Management Specialists |
| Data Analyst | 15-2051 | Data Scientists |
| Systems Analyst, IT Business Analyst | 15-1211 | Computer Systems Analysts |
| Programmer | 15-1251 | Computer Programmers |
| Systems Administrator | 15-1244 | Network and Computer Systems Administrators |
| Network Specialist | 15-1231 | Computer Network Support Specialists |
| IT Support Specialist | 15-1232 | Computer User Support Specialists |
| Cybersecurity Analyst | 15-1212 | Information Security Analysts |
| Database Administrator | 15-1242 | Database Administrators |
| Attorney | 23-1011 | Lawyers |
| Legal Assistant | 23-2011 | Paralegals and Legal Assistants |
| Planner | 19-3051 | Urban and Regional Planners |

**Aging.** OEWS May 2025 wages are aged 17 months to the payroll date at an
assumed 3.5% annual salary-increase rate (factor 1.0499). This is standard
practice for survey data.

**Market index** = state median ÷ aged Texas median. Austin is shown for
reference only, because the payroll has no work location. OEWS cross-industry
estimates cover all employers, including government, so the benchmark is the
whole Texas labor market rather than private employers alone.

## 8. Privacy

The raw payroll contains names. It is not committed. Published tables are
aggregates, and the Tableau extract suppresses any agency × title × tenure
band × gender group with fewer than 5 people. No individual is named.

## 9. Reproducibility

`run_all.sh` rebuilds everything from `data/raw/`. Rows are ordered by state
employee number before every computation, and two consecutive runs produce
byte-identical outputs.
