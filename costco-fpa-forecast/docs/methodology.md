# Methodology

## 1. Data

**Earnings releases.** The model uses every Costco 8-K exhibit filed from 2005 onward and keeps the 84
that announce quarterly results. From each release's Exhibit 99.1 it takes:

- **Income statement:** the current quarter and the prior-year column. Older releases report in
  thousands and are converted to millions. Net sales, membership fees, merchandise costs, SG&A,
  preopening and impairment ("other operating expense"), and operating income reconcile to within
  $1M in every quarter from FY2010 to FY2026.
- **Comparable sales**, both reported and excluding the effects of gasoline prices and foreign
  exchange (Costco calls the latter "adjusted"), for the total company and the U.S. Costco has
  laid these out four different ways since 2010: two separate tables introduced by "excluding..."
  sentences, tables without week headers, "w/o gas inflation & FX" columns (FY2018), and paired
  "Adjusted*" columns (FY2019 onward). The parser handles each. Coverage is complete from FY2010 Q1
  to FY2026 Q4, a total of 68 quarters.
- **Warehouse count** from the "currently operates N warehouses" sentence. From Exhibit 99.2, the
  slide supplement published since FY2024, it also takes the membership renewal rate and paid
  memberships.

The XBRL company facts were also downloaded. They cannot be the main source because, from FY2019,
Costco tags net sales and membership fees with a dimension that the company-facts feed drops.
`build_actuals.py` keeps them as a cross-check on totals. Total revenue and operating income agree
within 0.5% in all 66 quarters where XBRL has both. For FY2026 Q3 and Q4, XBRL has only operating
income, and it matches exactly.

**Monthly sales.** Costco's monthly sales releases are not filed with the SEC, except for the
February month, which is bundled with Q2 results. Its investor-relations site blocks automated
access. The model is therefore quarterly.

**FRED.** Weekly U.S. regular gasoline prices (GASREGW) and daily exchange rates for the seven
largest foreign markets by warehouse count: Canada, Mexico, Japan, the U.K., Korea, Australia, and
Taiwan. Each series is averaged over Costco's exact fiscal-quarter dates. The FX basket is weighted
by warehouse count as of September 2026.

## 2. The sales identity

For each quarter:

```
calendar  = weeks this year / weeks in the same quarter last year      (53-week years: FY2012, FY2017, FY2023)
g         = net sales / (last year's net sales x calendar) - 1
comp_adj  = comparable sales excluding gas and FX
gas_fx    = reported comp - comp_adj
non_comp  = g - reported comp                                          (mostly new warehouses)
```

so that `net sales = LY x calendar x (1 + comp_adj + gas_fx + non_comp)` holds exactly.

## 3. The annual budget

The budget is set at the start of each fiscal year using only quarters already released:

| Driver | Budget assumption |
|---|---|
| Underlying comp | Weeks-weighted average of the last four quarters' adjusted comps |
| Non-comp growth | Weeks-weighted average of the last four quarters |
| Gas and FX | Zero: constant prices and budget exchange rates |
| Membership fees | Last year's quarter x calendar x (1 + latest quarter's fee growth) |
| Gross margin %, SG&A %, other opex % | Last year's same-quarter rate, with disclosed one-time items removed |

Membership fees use the latest quarter's growth rather than a four-quarter average because Costco
recognizes fees ratably over the membership year. The latest quarter shows how much of a fee
increase has already lapped. This choice left the fee forecast about the same (2.5% average full-year
error either way). It lowered the operating-income error from 5.7% to 5.0%.

The only one-time item normalized is the FY2026 Q4 IEEPA tariff refund. Costco disclosed it as +9
basis points of gross margin ("Other", net of reinvestment in member prices), which is about $84M.

**Operating income** = net sales x (GM% − SG&A% − other%) + membership fees.

## 4. Baselines

- **Last year, no growth:** last year's quarter x calendar.
- **Last year's growth repeated:** last year's quarter x calendar x (1 + trailing four-quarter total
  growth). This baseline carries forward whatever gas and FX did last year.
- **Holt-Winters:** additive damped trend and additive seasonality on log weekly sales, trained on
  every quarter from FY2006 up to the budget date and forecasting four quarters ahead (statsmodels).

## 5. Bridges

**Sales.** With `k = LY x calendar`:

```
actual - budget = k x (comp_adj_actual - comp_adj_budget)
                + k x (gas_fx_actual - gas_fx_budget)
                + k x (non_comp_actual - non_comp_budget)
```

**Operating income:**

```
actual - budget = (sales_A - sales_B) x budget margin rate          sales volume
                + sales_A x (GM%_A - GM%_B)                         gross margin rate
                - sales_A x (SG&A%_A - SG&A%_B)                     SG&A rate
                - sales_A x (other%_A - other%_B)                   other opex rate
                + (fees_A - fees_B)                                 membership fees
```

Both bridges are exact. Python asserts that they close, and the Excel sheet has a check row.

## 6. Rolling reforecast

After Q1, Q2, and Q3, the remaining quarters are reforecast with these changes:

- Underlying comps, non-comp growth, and fee growth switch to year-to-date averages.
- The gas and FX effect is held at the latest quarter's level.
- Margin rates move by the year-to-date change against last year.

The full-year forecast is year-to-date actuals plus the forecast for the remaining quarters.

## 7. Gas and FX model

Least squares with no intercept (no price change means no effect), fit on 68 quarters:

```
gas_fx effect = 0.096 x gas price change (YoY) + 0.247 x FX basket change (YoY)      R² = 0.95
```

A 10% rise in gasoline prices adds about 1 point to reported comps. The FX coefficient roughly
matches the foreign share of Costco's sales.

**SG&A leverage:**

```
SG&A rate change (bps) = 27.9 − 5.2 x adjusted comp (pts) − 6.8 x gas/FX effect (pts)    R² = 0.71
```

Each point of underlying comp lowers the SG&A rate by about 5 bps. Gas inflation also lowers it, but
only because it inflates the sales denominator.

## 8. FY2027 scenarios

The FY2027 budget is built from FY2026 actuals. Each scenario changes one set of inputs:

- **Spot gas and FX:** today's gasoline price (four-week average) and today's exchange rates (about
  four-week average), held for the year. They are compared with each FY2026 quarter's average and
  converted to a sales effect with the coefficients above.
- **Gas price shocks:** +25% and −15% against FY2026.
- **Comps 2 points lower:** core sales fall, and the SG&A rate rises by 5.2 bps per point.

Gasoline is assumed to add sales but no operating profit. FX translates the whole foreign P&L.
Membership fees are unchanged across scenarios.

## 9. Reproducibility

`run_all.sh` rebuilds everything. The Excel plan was recalculated in LibreOffice and matches Python
to the dollar: $322,169.7M net sales and $12,509.6M operating income. With the switches set to
"comps −2 and spot gas and FX", it also matches the Python scenario exactly.
