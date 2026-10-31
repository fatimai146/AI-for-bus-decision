"""Where do employees sit inside their official pay range?

Range penetration = (salary - range min) / (range max - range min)
Compa-ratio       = salary / range midpoint

Outputs
  range_position_by_tenure.csv
  range_position_by_agency.csv   agencies with 100+ employees
"""
from common import OUT, connect, ensure_dirs


def main():
    ensure_dirs()
    con = connect()
    by_tenure = con.execute("""
        SELECT tenure_band, count(*) AS employees,
               median(penetration) AS median_penetration,
               median(compa_ratio) AS median_compa_ratio,
               avg((penetration < 0.25)::INT) AS share_bottom_quartile,
               avg((penetration >= 0.75)::INT) AS share_top_quartile
        FROM emp GROUP BY 1 ORDER BY min(tenure)""").df()
    by_tenure.to_csv(OUT / "range_position_by_tenure.csv", index=False)
    print(by_tenure.round(3).to_string(index=False))

    by_agency = con.execute("""
        SELECT agency, agency_name, count(*) AS employees,
               median(compa_ratio) AS median_compa_ratio,
               median(penetration) AS median_penetration,
               avg((penetration < 0.25)::INT) AS share_bottom_quartile,
               count(*) FILTER (WHERE tenure >= 10) AS tenured_10y,
               avg((penetration < 0.25)::INT) FILTER (WHERE tenure >= 10) AS tenured_share_bottom_quartile
        FROM emp GROUP BY ALL HAVING count(*) >= 100
        ORDER BY median_compa_ratio""").df()
    by_agency.to_csv(OUT / "range_position_by_agency.csv", index=False)
    print(by_agency.head(10).round(3).to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()
