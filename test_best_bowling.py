from db import query
import data_service

pid = 12894 # Ashwin
filters = {'format': 'T20I', 'league': 'All', 'opponent': 'All', 'phase': 'All', 'venue': 'All', 'year': 'All', 'innings': 'All', 'bowling_type': 'All', 'recent': 'All'}
ci_w = data_service._build_ci_where(filters)
cs_w = data_service._build_cs_where(filters)
names = data_service._get_player_names(pid)
ns = data_service._names_sql(names)

q = f"""
        WITH ci_match AS (
            SELECT cp.match_id,
                SUM(CASE WHEN cp.isWicket = TRUE 
                          AND COALESCE(cp.dismissalText,'') NOT ILIKE '%run out%'
                          AND COALESCE(cp.dismissalText,'') NOT ILIKE '%retired%'
                          AND COALESCE(cp.dismissalText,'') NOT ILIKE '%obstructing%'
                         THEN 1 ELSE 0 END) AS wickets,
                SUM(cp.batsmanRuns + COALESCE(cp.wides,0) + COALESCE(cp.noballs,0)) AS conceded,
                SUM(CASE WHEN COALESCE(cp.wides,0)=0 AND COALESCE(cp.noballs,0)=0
                         THEN 1 ELSE 0 END)::DOUBLE / 6.0 AS overs
            FROM cricinfo_parquet cp
            JOIN cricinfo_metadata m ON cp.match_id = m.match_id
            WHERE cp.bowlerPlayerId = {pid}
              AND (cp.skipped IS NULL OR cp.skipped = FALSE)
              AND (cp.empty IS NULL OR cp.empty = FALSE)
              {ci_w}
            GROUP BY cp.match_id
        ),
        cs_match AS (
            SELECT d.match_id,
                SUM(CASE WHEN d.is_wicket = TRUE
                          AND COALESCE(d.dismissal_kind,'') NOT IN
                              ('run out','retired hurt','retired out','obstructing the field')
                         THEN 1 ELSE 0 END) AS wickets,
                SUM(d.batter_runs + d.wides + d.noballs) AS conceded,
                SUM(CASE WHEN d.wides=0 AND d.noballs=0
                         THEN 1 ELSE 0 END)::DOUBLE / 6.0 AS overs
            FROM cricsheet_deliveries d
            JOIN cricsheet_matches cm ON d.match_id = cm.match_id
            WHERE d.bowler IN ({ns})
              {cs_w}
            GROUP BY d.match_id
        ),
        combined AS (
            SELECT 
                COALESCE(ci.match_id, cs.match_id) AS match_id,
                GREATEST(COALESCE(ci.wickets, 0), COALESCE(cs.wickets, 0)) AS wickets,
                GREATEST(COALESCE(ci.conceded, 0), COALESCE(cs.conceded, 0)) AS conceded,
                GREATEST(COALESCE(ci.overs, 0), COALESCE(cs.overs, 0)) AS overs
            FROM ci_match ci
            FULL OUTER JOIN cs_match cs ON ci.match_id = cs.match_id
        )
        SELECT COALESCE(SUM(wickets),0)::INT AS wickets,
               COALESCE(SUM(conceded),0)::INT AS conceded,
               COALESCE(SUM(overs),0)::DOUBLE AS overs,
               (SELECT wickets FROM combined WHERE wickets > 0 ORDER BY wickets DESC, conceded ASC LIMIT 1) AS best_w,
               (SELECT conceded FROM combined WHERE wickets > 0 ORDER BY wickets DESC, conceded ASC LIMIT 1) AS best_r
        FROM combined
"""
print(query(q))
