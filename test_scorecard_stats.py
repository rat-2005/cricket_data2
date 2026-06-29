"""
Test that the new scorecard-based aggregate gives correct runs for Kohli
without needing the slow wagon-wheel S3 scan.
"""
from db import query_one

pid = 49752

# All formats
ci = query_one(f"""
    WITH innings AS (
        SELECT b.match_id, b.inningNumber,
            COALESCE(b.runs, 0)  AS runs,
            COALESCE(b.balls, 0) AS balls,
            COALESCE(b.sixes, 0) AS sixes
        FROM cricinfo_batting b
        JOIN cricinfo_metadata m ON b.match_id = m.match_id
        WHERE b.playerId = {pid}
          AND b.battedType = 'yes'
    )
    SELECT COALESCE(SUM(runs),0)::INT  AS runs,
           COALESCE(SUM(balls),0)::INT AS balls,
           COALESCE(SUM(sixes),0)::INT AS sixes,
           COALESCE(MAX(runs),0)::INT  AS hs
    FROM innings
""")
print("=== All Formats (from scorecard) ===")
print("Runs:", ci["runs"])
print("Balls:", ci["balls"])
print("Sixes:", ci["sixes"])
print("HS:", ci["hs"])
print()

# ODI only
ci_odi = query_one(f"""
    WITH innings AS (
        SELECT b.match_id, b.inningNumber,
            COALESCE(b.runs, 0)  AS runs,
            COALESCE(b.balls, 0) AS balls,
            COALESCE(b.sixes, 0) AS sixes
        FROM cricinfo_batting b
        JOIN cricinfo_metadata m ON b.match_id = m.match_id
        WHERE b.playerId = {pid}
          AND b.battedType = 'yes'
          AND m.format = 'ODI' AND COALESCE(m.internationalClassId, 0) = 2
          AND m.seriesName NOT ILIKE '%Under-19%'
    )
    SELECT COALESCE(SUM(runs),0)::INT  AS runs,
           COALESCE(SUM(balls),0)::INT AS balls,
           COALESCE(SUM(sixes),0)::INT AS sixes,
           COALESCE(MAX(runs),0)::INT  AS hs
    FROM innings
""")
print("=== ODI Only (from scorecard) ===")
print("Runs:", ci_odi["runs"])
print("Balls:", ci_odi["balls"])
print("Sixes:", ci_odi["sixes"])
print("HS:", ci_odi["hs"])
print()

# T20I only
ci_t20i = query_one(f"""
    WITH innings AS (
        SELECT b.match_id, b.inningNumber,
            COALESCE(b.runs, 0)  AS runs,
            COALESCE(b.balls, 0) AS balls,
            COALESCE(b.sixes, 0) AS sixes
        FROM cricinfo_batting b
        JOIN cricinfo_metadata m ON b.match_id = m.match_id
        WHERE b.playerId = {pid}
          AND b.battedType = 'yes'
          AND m.format IN ('T20', 'T20I', 'IT20') AND COALESCE(m.internationalClassId, 0) = 3
    )
    SELECT COALESCE(SUM(runs),0)::INT  AS runs,
           COALESCE(SUM(balls),0)::INT AS balls,
           COALESCE(SUM(sixes),0)::INT AS sixes,
           COALESCE(MAX(runs),0)::INT  AS hs
    FROM innings
""")
print("=== T20I Only (from scorecard) ===")
print("Runs:", ci_t20i["runs"])
print("Balls:", ci_t20i["balls"])
print("Sixes:", ci_t20i["sixes"])
print("HS:", ci_t20i["hs"])
