import os, asyncio, asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print("Dropping old materialized views...")
    await conn.execute("DROP MATERIALIZED VIEW IF EXISTS cricket.player_stats_mv;")
    await conn.execute("DROP MATERIALIZED VIEW IF EXISTS cricket.bowler_stats_mv;")
    
    print("Creating new player_stats_mv...")
    await conn.execute("""
        CREATE MATERIALIZED VIEW cricket.player_stats_mv AS
        SELECT 
            pmp.athlete_id,
            c.class_name AS format,
            SUM(pmp.runs) AS total_runs,
            SUM(pmp.sixes) AS total_sixes,
            SUM(pmp.balls_faced) AS balls_faced
        FROM cricket.player_match_performances pmp
        JOIN cricket.competitors comp ON pmp.competitor_id = comp.id
        JOIN cricket.competitions c ON comp.competition_id = c.id
        WHERE pmp.is_batting = TRUE
        GROUP BY pmp.athlete_id, c.class_name;
    """)

    print("Creating new bowler_stats_mv...")
    await conn.execute("""
        CREATE MATERIALIZED VIEW cricket.bowler_stats_mv AS
        SELECT 
            pmp.athlete_id,
            c.class_name AS format,
            SUM(pmp.runs_conceded) AS runs_conceded,
            SUM(pmp.overs_bowled) AS overs_bowled,
            SUM(pmp.wickets) AS total_wickets
        FROM cricket.player_match_performances pmp
        JOIN cricket.competitors comp ON pmp.competitor_id = comp.id
        JOIN cricket.competitions c ON comp.competition_id = c.id
        WHERE pmp.is_batting = FALSE
        GROUP BY pmp.athlete_id, c.class_name;
    """)

    print("Done!")
    await conn.close()

asyncio.run(run())
