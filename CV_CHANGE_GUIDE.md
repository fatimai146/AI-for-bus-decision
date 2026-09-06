# CV Change Guide — 3 Versions from Your Current Resume

Your current resume is the starting point. Below are the exact changes to make for each of three versions. Anything not mentioned stays as-is.

---

## Changes Common to ALL 3 Versions

These edits apply no matter which version you're building.

### 1. PROFILE section — rewrite both bullets

**Current first bullet:**
> Data-driven Business Analytics graduate student with experience applying predictive modeling, statistical analysis, and dashboarding to solve real business problems. Proven ability to work with complex datasets, generate actionable insights, and communicate results through executive-ready storytelling

**Replace with (then tweak per version — see below):**
> Business Analytics graduate student with experience building data products end to end — from metric design and pipeline engineering to deployed dashboards — at Cloudflare and Nestlé. Proven ability to work with complex, multi-source datasets, generate actionable insights, and communicate results through executive-ready storytelling.

**Current second bullet (skills):**
> Skills: Python, SQL, CRM, AI Tools, BigQuery, Power BI, Jira, Visual Storytelling, Predictive Modelling

**Replace with:**
> Skills: Python, R, SQL, BigQuery, React, TypeScript, Power BI, Cloudflare Workers, Git/GitLab, Data Modeling, Predictive Modeling, Scheduled ELT, Data Privacy, Stakeholder Communication

Remove "CRM" and "AI Tools" — they're vague and take up space you need for real tools. Add R, React, TypeScript, Cloudflare Workers, Git/GitLab from your internship.

### 2. HEADER — update the tagline

**Current:**
> Eligible for Internship and Full-time roles

**Replace with:**
> Eligible for full-time roles starting January 2027

You're past the internship stage. This signals readiness and timeline.

### 3. EDUCATION — change Kearney dates

**Current:**
> January 2026 – Present

**Replace with:**
> January 2026 – May 2026

(Assuming the practicum ended in spring. If it's still active, keep "Present".)

### 4. WORK EXPERIENCE — add Cloudflare as the TOP entry

Insert a new entry **above** "Purdue - Kearney Industry Practicum" so it's the first thing under WORK EXPERIENCE. Format:

```
Cloudflare                                                          [City or Remote]
Talent Analytics Intern                                    June 2026 – August 2026
```

The bullets for this entry change per version — see below.

### 5. WORK EXPERIENCE — compress Nestlé

You need room for Cloudflare. Across all 3 versions, trim Nestlé to fit:

**Assistant Manager HRBP:** Keep both bullets as-is (they're already tight).

**HR Specialist:** Keep 2 of the current 3 bullets. Drop this one (it partially repeats the first):
> Delivered workforce intelligence for Agri Services (120+ employees), delivering executive-ready insights on headcount, attrition, hiring funnel, engagement, and L&D metrics to inform talent and capacity planning

Keep the dashboard bullet and the attrition/retention bullet — they're more concrete.

**Management Trainee:** Keep as-is (1 bullet, already compact).

### 6. LEADERSHIP section — add certifications line update

After your internship, update this line if you pick up any new certs. Otherwise keep as-is.

---

## Version 1: Technical (Analyst / BI / Data Engineer / ML)

This is for: Data Analyst, BI Engineer, Analytics Engineer, Data Engineer, ML Engineer, Product Analytics roles.

### Profile first bullet — tweak

Use the common rewrite above but start it with:
> Business Analytics graduate student with experience building analytics pipelines, predictive models, and deployed BI dashboards at Cloudflare and Nestlé...

### Skills bullet — tweak

Put technical tools first in the ordering:
> Skills: Python, R, SQL, BigQuery, React, TypeScript, Cloudflare Workers, Power BI, Git/GitLab, Scheduled ELT, Data Modeling, Predictive Modeling, Cross-Validation, Bias Correction, NLP, Data Privacy

### Cloudflare bullets (pick 5-6 of these)

1. Designed and deployed Recruiting Signal, a live self-service BI dashboard on the company's ATS and BigQuery data, giving recruiters at-a-glance pipeline health with drill-down from recruiter to requisition to candidate
2. Engineered an end-to-end data pipeline in R and Python integrating four enterprise sources (HRIS, surveys, ATS, performance reviews) into a merged hire-level analytical table, including dedup, cross-system ID reconciliation, and leakage-safe temporal joins
3. Designed a composite Quality-of-Hire target variable using peer z-scoring within job family and cohort, empirical-Bayes shrinkage for small groups, and Kaplan-Meier survival imputation for censored retention, with a strict pre-hire leakage firewall on all predictors
4. Built and benchmarked 12 model families (ElasticNet through XGBoost/LightGBM to MLP) with nested cross-validation, temporal splits, and Optuna hyperparameter search; diagnosed near-zero R² as range restriction and applied Thorndike Case-II corrections to recover validity
5. Built a two-stage BigQuery pipeline that rebuilt curated fact tables from source data and mirrored them into a separate reporting project, automated as a daily scheduled query with least-privilege service accounts and post-refresh validation
6. Championed responsible use — positioned the model for ranking at quintile resolution only, flagged a required fairness audit before operational use, and delivered stakeholder-ready outputs (model card, one-pager, closeout report)

**Strongest combo for a BI/Analytics Engineer role:** bullets 1, 2, 5, then 6
**Strongest combo for a Data Science/ML role:** bullets 3, 4, 2, then 6
**Strongest combo for a Product Analytics role:** bullets 1, 6, 3, then 5

### Academic Projects — keep both as-is

The Kaggle AUC result and the BigQuery spatial analysis both reinforce technical depth.

---

## Version 2: HR / People Analytics

This is for: People Analytics, Talent Analytics, Talent Acquisition Analytics, HR Tech, HRBP-with-analytics roles.

### Profile first bullet — tweak

> Business Analytics graduate student with experience designing people-data products — from metric design to deployed decision tools — at Cloudflare and Nestlé. Proven ability to partner with HR and recruiting leaders, generate actionable workforce insights, and communicate results through executive-ready storytelling.

### Skills bullet — tweak

Lead with methods, not just tools:
> Skills: People Analytics, Talent Measurement, Recruiting Funnel Analysis, SQL, BigQuery, Python, R, Power BI, React, Data Privacy/Ethics, Change Management, Stakeholder Communication

### Cloudflare bullets (pick 5-6 of these)

1. Created the organization's first fair, peer-normalized Quality-of-Hire measure, enabling talent leaders to compare hires within peer groups rather than on raw, non-comparable performance numbers
2. Identified interview signal strength as a leading, actionable indicator of hire quality and made the case to standardize and track it consistently across hiring panels
3. Analyzed sourcing channel quality to inform where recruiting effort and agency spend deliver the strongest hires, with internal mobility and referrals outperforming job boards and agencies
4. Shipped Recruiting Signal, an internal decision-support dashboard, end to end — from problem definition through design, build, deployment, and pilot — framed as a recruiter prompt rather than an automated gate
5. Embedded privacy and trust into a people-data product: masked candidate identities, excluded interviewer names, enforced read-only access, and gated the tool behind company SSO
6. Partnered directly with the Director of Recruiting Strategy and Operations to shape the narrative and roadmap, ensuring recommendations were operationally realistic for recruiters and TA leaders
7. Designed the pilot rollout and a structured feedback tracker so TA leads could report issues and requests, triaged by impact, complexity, and timing
8. Championed responsible use — positioned the metric for prioritization at group resolution only, flagged a required fairness audit before operational decisions, and delivered stakeholder-ready outputs (model card, stakeholder summary, closeout report)

**Strongest combo:** bullets 1, 2, 3, 4, 5, 6 (use all six if they fit; drop 7 or 8 first if space is tight)

### Nestlé — expand, don't compress

For this version only, **keep all 3 HR Specialist bullets** (don't drop the workforce intelligence one). The recruiting/attrition/engagement language directly supports the People Analytics narrative. If you need space, shorten the Kearney practicum to 1 bullet instead:

> Developed a Power BI dashboard with 5 executive views, enabling leadership to monitor 10+ standardized KPIs across service operations

### Academic Projects — consider swapping

The Kaggle ML project is less relevant here. If space is tight, drop it and keep only the Spatial Equity Analysis (which shows policy/equity thinking). Alternatively, replace it with a one-liner about the NCAA Data Analytics Challenge (move it up from Leadership).

---

## Version 3: Product

This is for: Product Manager, Product Analyst (product-leaning), Program Manager, Technical Program Manager roles.

### Profile first bullet — tweak

> Business Analytics graduate student with experience taking data products from concept to deployment at Cloudflare and Nestlé. Proven ability to scope problems, make product trade-offs, run pilot processes, and communicate results through executive-ready storytelling.

### Skills bullet — tweak

Lead with product methods:
> Skills: Product Thinking, Scoping & Prioritization, Roadmap Planning, Pilot Management, SQL, BigQuery, Python, React, TypeScript, Cloudflare Workers, Power BI, UX Decisions, Stakeholder Communication, Data Privacy

### Cloudflare bullets (pick 5-6 of these)

1. Shipped Recruiting Signal, an internal decision-support dashboard, from problem definition through design, build, deployment, and pilot — deliberately framed as a recruiter prompt rather than an automated gate
2. Scoped the product to three high-value surfaces: strong active candidates to accelerate, strong past finalists to re-engage, and requisitions at risk of stalling
3. Made deliberate product decisions balancing usefulness and privacy — kept the re-engagement pool shared for cross-team use while scoping a recruiter's active pipeline to only their own roles
4. Designed role-aware experiences — an admin view for recruiting operations and a scoped personal view for individual recruiters — enforced server-side rather than cosmetically hidden
5. Ran a pilot-driven process, standing up feedback intake and a triage tracker that grouped bugs and requests into themes prioritized by complexity and timing to feed a next-version roadmap
6. Drove a migration to the company design system for a consistent, on-brand, enterprise look, and simplified interactions based on early usability feedback
7. Defined and built a composite Quality-of-Hire metric, stress-tested it for robustness under alternative weightings, and reframed the work from unreliable point prediction into reliable ranking — matching the analysis to a decision the business could actually act on

**Strongest combo:** bullets 1, 2, 3, 5, 7 (lead with shipping, scope, trade-offs, then process and analytical rigor)

### Kearney — keep all 3 bullets

The consulting/stakeholder framing supports product roles well.

### Academic Projects — keep both as-is

Both show analytical breadth, which product roles value.

---

## Quick Summary: What Changes Where

| Section | Version 1 (Technical) | Version 2 (HR/People) | Version 3 (Product) |
|---------|----------------------|----------------------|---------------------|
| Header tagline | "full-time roles starting Jan 2027" | same | same |
| Profile bullet 1 | pipelines + models + dashboards | people-data products + HR partnership | concept to deployment + trade-offs |
| Profile skills | tools-first ordering | methods-first ordering | product-methods-first ordering |
| Cloudflare bullets | 5-6 from Technical list | 5-6 from HR list | 5-6 from Product list |
| Kearney | keep all 3 | trim to 1 bullet | keep all 3 |
| Nestlé HR Specialist | drop workforce intel bullet | keep all 3 bullets | drop workforce intel bullet |
| Academic Projects | keep both | consider dropping Kaggle | keep both |
| Leadership section | no change | no change | no change |

---

## Confidentiality Reminder

Every Cloudflare bullet above avoids raw internal numbers. Before posting any version publicly, send your manager a quick message confirming the bullets are safe for external use.
