# Cloudflare Internship Bullet Bank — Per-Role Customization Guide

> **How to use this file:** Pick the 3-6 strongest bullets for each specific job application. Match the "lens" to the JD. Every bullet below is confidential-free. Keep the detailed internal numbers (706,934 applications, $38.1M, exact headcounts) in your back pocket for interviews only — after confirming with your manager.

---

## One-Line Resume Header Options (pick per role)

| Role family | Header |
|-------------|--------|
| Business Analytics | Built a Quality-of-Hire analytics product, from metric design to a deployed recruiter decision tool |
| HR / People Analytics | Moved recruiting from measuring speed to measuring and acting on hire quality |
| Product | Shipped an internal, access-controlled recruiting decision tool end to end |
| BI / Analytics Engineer | Designed the data model and automated pipeline behind a live recruiting dashboard |
| Data Science / ML | Built and honestly validated a Quality-of-Hire ranking model, then operationalized it |

---

## Lens 1: Business Analytics

**Project descriptor:** Built an end-to-end analytics product that measured hiring quality and turned the findings into a decision tool used by recruiters.

- Defined and built a composite Quality-of-Hire metric that combined measured performance and potential with adjustments for early attrition and accelerated promotion, peer-normalized within job family and cohort so comparisons were fair
- Stress-tested the metric for robustness, confirming the resulting ranking stayed stable under alternative component weightings, so recommendations did not depend on arbitrary assumptions
- Translated the analysis into a short set of low-cost, high-leverage operating recommendations spanning interview signal, sourcing mix, and interview process efficiency
- Reframed the work from unreliable individual prediction into reliable ranking of who is likely to be a strong hire, matching the analysis to a decision the business could actually act on
- Delivered findings as an executive-ready narrative and a live tool, closing the gap between a one-time analysis and everyday recruiter decisions

**Skills line:** Metric design, hypothesis testing, cohort analysis, robustness/sensitivity analysis, stakeholder storytelling, SQL, BigQuery

---

## Lens 2: HR / People Analytics

**Project descriptor:** People analytics work that moved recruiting from measuring hiring speed to measuring and acting on hiring quality.

- Created a fair, like-for-like Quality-of-Hire measure that let talent leaders compare hires within peer groups instead of on raw, non-comparable performance data
- Identified interview signal strength as a leading, actionable indicator of hire quality, and made the case to standardize and track it consistently across hiring panels
- Analyzed sourcing channel quality to inform where recruiting effort and agency spend deliver the strongest hires
- Partnered directly with recruiting operations leadership to shape the narrative and roadmap, keeping recommendations realistic for recruiters and TA leaders
- Embedded privacy and trust into a people-data product by masking candidate identities, excluding interviewer names, enforcing read-only access, and gating the tool behind company SSO
- Designed the pilot rollout and a structured feedback tracker so TA leads could report issues and requests, triaged by impact, complexity, and timing

**Skills line:** People analytics, talent measurement, recruiting funnel analysis, stakeholder partnership, data privacy/ethics, change management

---

## Lens 3: Product

**Project descriptor:** Took a data insight from concept to a shipped, access-controlled internal product used by recruiters.

- Shipped Recruiting Signal, an internal decision-support dashboard, from problem definition through design, build, deployment, and pilot, deliberately framed as a recruiter prompt rather than an automated gate
- Scoped the product to three high-value surfaces: strong active candidates to accelerate, strong past finalists to re-engage, and requisitions at risk of stalling
- Made deliberate product decisions balancing usefulness and privacy, such as keeping the re-engagement pool shared while scoping a recruiter's active pipeline to their own roles
- Designed role-aware experiences — an admin view for recruiting operations and a scoped personal view for individual recruiters — enforced on the server rather than cosmetically hidden
- Ran a pilot-driven process, standing up feedback intake and a triage tracker that grouped bugs and requests into themes prioritized by complexity and timing to feed a next-version roadmap
- Drove a migration to the company design system for a consistent, on-brand, enterprise look, and simplified interactions based on early usability feedback

**Skills line:** Product thinking, scoping and prioritization, roadmap planning, UX decisions, pilot management, stakeholder feedback loops

---

## Lens 4: Business Intelligence / Analytics Engineering

**Project descriptor:** Designed and deployed the data model, pipeline, and reporting layer behind a live recruiting analytics dashboard.

- Designed a curated set of fact tables (requisition health, hiring funnel, active candidate signals, re-engagement pool, candidate journey) as a clean reporting layer, decoupling the dashboard from raw, sensitive source data
- Built a two-stage BigQuery pipeline that rebuilt curated tables from source data and mirrored them into a separate reporting project, then automated it as a daily scheduled query aligned to the upstream data refresh
- Implemented least-privilege access with a dedicated read-only service account for the dashboard runtime and a separate identity for the refresh job, so a credential issue could not expose write access or raw data
- Standardized business definitions directly in the data — such as consistent requisition health categories and a data quality check that separated stale or evergreen roles from genuine risk — so every user saw one version of the truth
- Added post-refresh validation and privacy checks to catch data quality or privacy regressions before they reached users
- Documented the architecture, refresh runbook, and ownership handoff so the pipeline could outlive any single contributor

**Skills line:** Dimensional/fact table modeling, BigQuery, scheduled queries/ELT, data governance, least-privilege access, data validation, documentation

---

## Lens 5: Data Science / ML Engineering

**Project descriptor:** Built and validated a predictive quality model, and stayed disciplined about what it could and could not claim.

- Engineered a Quality-of-Hire target from performance, potential, tenure, and promotion signals, peer-normalized within job family and cohort to reduce structural bias in comparisons
- Evaluated predictive strength honestly, correcting for range restriction, while clearly cautioning that individual point prediction was unreliable due to selection bias from only observing hired candidates
- Reframed the model around ranking rather than point estimates once the analysis showed ranking was the trustworthy use case, matching the model to what it could actually support
- Surfaced and communicated key limitations and bias risks, and recommended a fairness audit before the model influenced real decisions
- Turned validated signals into a real-time scoring surface for open pipelines, back-tested against historical hires before exposing anything to recruiters
- Laid out a staged model-maturity path grounded in the reality that future gains would come from richer data and matured cohorts rather than a more complex algorithm

**Skills line:** Feature engineering, predictive modeling, bias correction (range restriction, selection bias), model validation/back-testing, responsible AI framing, SQL/BigQuery

---

## Technical Stack to List (adjust emphasis per role)

| Category | Items |
|----------|-------|
| Languages | SQL, Python, R, TypeScript, VBA |
| Data platforms | BigQuery, Google Cloud |
| Web/App | React, Cloudflare Workers, Cloudflare Access |
| BI/Viz | Power BI, dashboard/BI design |
| Infrastructure | Git/GitLab, scheduled ELT, service account/access control |
| Methods | Data modeling, predictive modeling, NLP, survival analysis, A/B testing |
| Soft | Stakeholder communication, data privacy, change management |

---

## Swapping Guide: Quick Reference

**For a Product Analytics role at a tech company:**
Use Technical resume base. Lead with Product lens bullet 1 (shipped end-to-end). Add Business Analytics bullet about ranking reframe. Include BI bullet about fact table design. Close with Data Science bullet about responsible AI.

**For a Data Engineer role:**
Use Technical resume base. Lead with BI lens bullets 1-3 (fact tables, pipeline, least-privilege). Add Data Science bullet about target engineering. Include BI bullet about documentation/handoff.

**For an ML Engineer role:**
Use Technical resume base. Lead with Data Science lens bullets 1-3 (target engineering, honest evaluation, ranking reframe). Add BI bullet about pipeline automation. Include Business Analytics bullet about robustness testing.

**For a People Analytics role at a tech company:**
Use HR resume base. Lead with HR lens bullets 1-3 (fair metric, interview signal, sourcing). Add Product lens bullet about role-aware design. Include HR lens bullet about privacy/trust.

**For an HRBP or Talent Acquisition role:**
Use HR resume base. Lead with HR lens bullets 1 and 4 (fair metric, partnered with leadership). Add HR lens bullets 5-6 (privacy, pilot rollout). Emphasize Nestle HRBP experience more (expand those bullets). Consider dropping the Kaggle project in favor of more HR depth.

**For a BI/Analytics Engineer role:**
Use Technical resume base. Lead with BI lens bullets 1-4 (fact tables, pipeline, access control, definitions). Add Business Analytics bullet about metric robustness. Close with BI documentation bullet.
