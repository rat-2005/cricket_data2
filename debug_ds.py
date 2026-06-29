from db import query_one, query
import data_service

filters = {
    'format': 'ODI',
    'league': 'All',
    'opponent': 'All',
    'phase': 'All',
    'venue': 'All',
    'year': 'All',
    'innings': 'All',
    'bowling_type': 'All',
    'recent': 'All'
}

pid = 28081

ci_w = data_service._build_ci_where(filters)
ns = data_service._names_sql(data_service._get_player_names(pid))

sql = f"""
        WITH ci_match AS (
            SELECT cp.match_id, cp.inningNumber,
                SUM(cp.batsmanRuns) AS runs,
                SUM(CASE WHEN COALESCE(cp.wides,0)=0 THEN 1 ELSE 0 END) AS balls,
                SUM(CASE WHEN cp.batsmanRuns>=6 THEN 1 ELSE 0 END) AS sixes,
                SUM(CASE WHEN cp.batsmanRuns=0 AND COALESCE(cp.wides,0)=0 THEN 1 ELSE 0 END) AS dots
            FROM cricinfo_parquet cp
            JOIN cricinfo_metadata m ON cp.match_id = m.match_id
            WHERE cp.batsmanPlayerId = {pid}
              AND (cp.skipped IS NULL OR cp.skipped = FALSE)
              AND (cp.empty IS NULL OR cp.empty = FALSE)
              {ci_w}
            GROUP BY cp.match_id, cp.inningNumber
        )
        SELECT SUM(runs) FROM ci_match
"""
print("SQL:")
print(sql)
print("Result:", query_one(sql))
