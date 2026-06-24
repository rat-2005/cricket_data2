import psycopg2
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor()
        query = """
    WITH combined_deliveries AS (
        SELECT 
            d.competition_id as match_id,
            d.batsman_runs,
            d.is_wide,
            d.is_bye,
            d.is_leg_bye
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON c.id = d.competition_id
        WHERE d.batsman_id = %s AND d.bowler_id = %s
        AND (
            c.event_id IN (SELECT el.event_id FROM cricket.event_leagues el JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name = %s)
            OR
            c.date::date IN (SELECT DISTINCT match_date::date FROM cricket.unified_deliveries WHERE tournament LIKE %s)
        )
    )
    SELECT SUM(batsman_runs) FROM combined_deliveries
        """
        cur.execute(query, ['253802', '311592', 'ICC Cricket World Cup, 2023', 'ICC Cricket World Cup, 2023%'])
        print(cur.fetchall())

if __name__ == '__main__':
    test()
