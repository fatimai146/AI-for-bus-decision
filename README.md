# AI-for-bus-decision

Analytics projects that turn public data into business decisions.

| Project | Question | Stack |
| --- | --- | --- |
| [Credit Score Transition](credit-score-transition/) | If mortgage lenders switch from Classic FICO to FICO 10T or VantageScore 4.0, who gets approved differently and what happens to defaults? (425,000 Freddie Mac loans) | Python, DuckDB/SQL, scikit-learn, matplotlib, [Tableau](https://public.tableau.com/app/profile/iman.fatima4868/viz/CreditScoreTransitionClassicFICOvsFICO10TvsVantageScore4_0/CreditScoreSwitch) |
| [Texas State Workforce Compensation Review](tx-comp-review/) | Are long-serving employees paid fairly against new hires, where do people sit in their pay ranges, what would fixes cost, and how does pay compare with the market? (139,656 state employees) | Python, DuckDB/SQL, fixed-effects regression, BLS API, matplotlib |
| [AI for Job Evaluation and Market Matching](tr-ai-job-evaluation/) | Can open-source AI grade jobs and match them to market benchmarks well enough to help a Total Rewards team? (1,165 Texas state jobs, 386 job descriptions) | Python, Hugging Face embeddings (bge-base) via sentence-transformers, scikit-learn, pypdf, O\*NET, DuckDB |
| [Costco FY2027 Forecast and Budget-vs-Actual](costco-fpa-forecast/) | Can a driver-based budget built from public filings forecast a $300B retailer, explain each quarter's variance, and show what the 2026 gasoline spike means for FY2027? (68 quarters, 14-year backtest) | Python, statsmodels, SEC EDGAR, FRED, Excel (openpyxl formulas) |
