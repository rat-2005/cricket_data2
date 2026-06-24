import os, asyncio, asyncpg
from dotenv import load_dotenv

async def run():
    load_dotenv()
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print("=== Data Verification ===\n")
    
    # Check PMP records count
    pmp_count = await conn.fetchval("SELECT COUNT(*) FROM cricket.player_match_performances")
    print(f"Total records in player_match_performances: {pmp_count:,}\n")
    
    # Check Kohli data in PMP
    print("Kohli stats in PMP (by format):")
    kohli_data = await conn.fetch("""
        SELECT 
            c.class_name as format,
            SUM(pmp.runs)::INT as total_runs,
            COUNT(DISTINCT pmp.competitor_id) as matches
        FROM cricket.player_match_performances pmp
        JOIN cricket.athletes a ON pmp.athlete_id = a.id
        JOIN cricket.competitors comp ON pmp.competitor_id = comp.id
        JOIN cricket.competitions c ON comp.competition_id::text = c.id::text
        WHERE a.full_name = 'Virat Kohli' AND pmp.is_batting = true
        GROUP BY c.class_name
        ORDER BY total_runs DESC
    """)
    
    for row in kohli_data:
        print(f"  {row['format']}: {row['total_runs']:,} runs in {row['matches']} matches")
    
    # Check what MV shows
    print("\nKohli stats in player_stats_mv:")
    mv_data = await conn.fetch("""
        SELECT 
            format,
            total_runs,
            balls_faced
        FROM cricket.player_stats_mv mv
        JOIN cricket.athletes a ON mv.athlete_id = a.id
        WHERE a.full_name = 'Virat Kohli'
        ORDER BY total_runs DESC
    """)
    
    for row in mv_data:
        print(f"  {row['format']}: {row['total_runs']:,} runs")
    
    await conn.close()

asyncio.run(run())
