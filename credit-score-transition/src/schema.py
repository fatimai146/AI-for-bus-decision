"""Column layouts for the Freddie Mac SFLLD standard sample files (Release 47+ layout)."""

ORIG_COLS = [
    "fico", "first_pay_date", "first_time_buyer", "maturity_date", "msa", "mi_pct",
    "units", "occupancy", "cltv", "dti", "orig_upb", "ltv", "orig_rate", "channel",
    "ppm_flag", "amort_type", "state", "property_type", "postal3", "loan_id",
    "loan_purpose", "orig_term", "num_borrowers", "seller_name", "super_conforming",
    "pre_harp_id", "special_eligibility", "harp_flag", "valuation_method", "io_flag",
    "vs4_orig",
]

PERF_COLS = [
    "loan_id", "period", "current_upb", "dlq_status", "loan_age", "rem_months",
    "defect_date", "mod_flag", "zero_bal_code", "zero_bal_date", "current_rate",
    "non_int_upb", "ddlpi", "mi_recoveries", "net_sales", "non_mi_recoveries",
    "total_expenses", "legal_costs", "maint_costs", "taxes_ins", "misc_expenses",
    "actual_loss", "cum_mod_cost", "step_mod", "payment_deferral", "eltv",
    "zb_removal_upb", "dlq_accrued_int", "disaster_dlq", "assistance_plan",
    "current_mod_cost", "int_bearing_upb", "mi_cancel", "servicer_name",
    "cramdown_costs",
]

SCORE_COLS_SUFFIX = ["current_method", "trimerge", "bi_lowest", "bi_median", "bi_highest"]
