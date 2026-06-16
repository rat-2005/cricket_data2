import os
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)
DB_URL = os.environ.get("DATABASE_URL")

# Initialize Flask App
app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(DB_URL)
    return conn

@app.route("/")
def index():
    fmt = request.args.get('format', 'All')
    
    is_ipl = False
    if fmt == 'Test':
        format_filter = "WHERE mv.format = 'Test'"
        comp_filter = "WHERE class_name = 'Test'"
    elif fmt == 'ODI':
        format_filter = "WHERE mv.format = 'ODI'"
        comp_filter = "WHERE class_name = 'ODI'"
    elif fmt == 'T20':
        format_filter = "WHERE mv.format IN ('T20I', 'Twenty20', 'Women T20', 'Other T20')"
        comp_filter = "WHERE class_name IN ('T20I', 'Twenty20', 'Women T20', 'Other T20')"
    elif fmt == 'IPL':
        is_ipl = True
        format_filter = ""
        comp_filter = ""
    else:
        format_filter = ""
        comp_filter = ""
        fmt = 'All'

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if is_ipl:
        cur.execute("""
            SELECT 
                a.full_name, 
                a.image_url, 
                SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END)::INT as total_runs, 
                SUM(CASE WHEN d.is_boundary=TRUE AND d.runs_scored >= 6 THEN 1 ELSE 0 END)::INT as total_sixes,
                ROUND((SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END)::NUMERIC / NULLIF(COUNT(CASE WHEN d.is_wide=FALSE THEN 1 ELSE NULL END), 0)) * 100, 2) as strike_rate
            FROM cricket.deliveries d
            JOIN cricket.competitions c ON d.competition_id = c.id
            JOIN cricket.event_leagues el ON c.event_id = el.event_id
            JOIN cricket.leagues l ON el.league_id = l.id
            JOIN cricket.athletes a ON d.batsman_id = a.id
            WHERE l.name = 'Indian Premier League'
            GROUP BY a.full_name, a.image_url
            ORDER BY total_runs DESC NULLS LAST LIMIT 10;
        """)
        top_batters = cur.fetchall()

        cur.execute("""
            SELECT 
                a.full_name, 
                a.image_url, 
                COUNT(dis.delivery_id)::INT as total_wickets, 
                SUM(d.bowler_conceded)::INT as runs_conceded,
                ROUND(SUM(d.bowler_overs)::NUMERIC, 1) as overs_bowled,
                CASE WHEN SUM(d.bowler_overs) > 0 THEN ROUND((SUM(d.bowler_conceded)::NUMERIC / SUM(d.bowler_overs)::NUMERIC), 2) ELSE 0.0 END as economy
            FROM cricket.deliveries d
            JOIN cricket.competitions c ON d.competition_id = c.id
            JOIN cricket.event_leagues el ON c.event_id = el.event_id
            JOIN cricket.leagues l ON el.league_id = l.id
            JOIN cricket.athletes a ON d.bowler_id = a.id
            LEFT JOIN cricket.dismissals dis ON d.id = dis.delivery_id AND dis.type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out')
            WHERE l.name = 'Indian Premier League'
            GROUP BY a.full_name, a.image_url
            ORDER BY total_wickets DESC NULLS LAST, economy ASC NULLS LAST LIMIT 10;
        """)
        top_bowlers = cur.fetchall()
        
        cur.execute("""
            SELECT 
                (SELECT COUNT(DISTINCT c.id) FROM cricket.competitions c JOIN cricket.event_leagues el ON c.event_id = el.event_id JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name = 'Indian Premier League') as total_matches,
                (SELECT SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END) FROM cricket.deliveries d JOIN cricket.competitions c ON d.competition_id = c.id JOIN cricket.event_leagues el ON c.event_id = el.event_id JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name = 'Indian Premier League') as total_runs,
                (SELECT COUNT(dis.delivery_id) FROM cricket.dismissals dis JOIN cricket.deliveries d ON dis.delivery_id = d.id JOIN cricket.competitions c ON d.competition_id = c.id JOIN cricket.event_leagues el ON c.event_id = el.event_id JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name = 'Indian Premier League' AND dis.type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out')) as total_wickets,
                (SELECT SUM(CASE WHEN d.is_boundary=TRUE AND d.runs_scored >= 6 THEN 1 ELSE 0 END) FROM cricket.deliveries d JOIN cricket.competitions c ON d.competition_id = c.id JOIN cricket.event_leagues el ON c.event_id = el.event_id JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name = 'Indian Premier League') as total_sixes
        """)
        stats = cur.fetchone()

    else:
        # Top Batters Query (Uses fast Materialized View)
        cur.execute(f"""
            SELECT 
                a.full_name, 
                a.image_url, 
                SUM(mv.total_runs)::INT as total_runs, 
                SUM(mv.total_sixes)::INT as total_sixes,
                ROUND((SUM(mv.total_runs)::NUMERIC / NULLIF(SUM(mv.balls_faced), 0)) * 100, 2) as strike_rate
            FROM cricket.player_stats_mv mv
            JOIN cricket.athletes a ON mv.athlete_id = a.id
            {format_filter}
            GROUP BY a.full_name, a.image_url
            ORDER BY total_runs DESC NULLS LAST 
            LIMIT 10;
        """)
        top_batters = cur.fetchall()

        # Top Bowlers Query (Uses fast Materialized View)
        cur.execute(f"""
            SELECT 
                a.full_name, 
                a.image_url, 
                SUM(mv.total_wickets)::INT as total_wickets, 
                SUM(mv.runs_conceded)::INT as runs_conceded,
                ROUND(SUM(mv.overs_bowled)::NUMERIC, 1) as overs_bowled,
                CASE 
                    WHEN SUM(mv.overs_bowled) > 0 
                    THEN ROUND((SUM(mv.runs_conceded)::NUMERIC / SUM(mv.overs_bowled)::NUMERIC), 2)
                    ELSE 0.0
                END as economy
            FROM cricket.bowler_stats_mv mv
            JOIN cricket.athletes a ON mv.athlete_id = a.id
            {format_filter}
            GROUP BY a.full_name, a.image_url
            ORDER BY total_wickets DESC NULLS LAST, economy ASC NULLS LAST
            LIMIT 10;
        """)
        top_bowlers = cur.fetchall()
        
        # Overview Stats Query
        cur.execute(f"""
            SELECT 
                (SELECT COUNT(*) FROM cricket.competitions {comp_filter}) as total_matches,
                (SELECT SUM(total_runs) FROM cricket.player_stats_mv mv {format_filter}) as total_runs,
                (SELECT SUM(total_wickets) FROM cricket.bowler_stats_mv mv {format_filter}) as total_wickets,
                (SELECT SUM(total_sixes) FROM cricket.player_stats_mv mv {format_filter}) as total_sixes
        """)
        stats = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("index.html", batters=top_batters, bowlers=top_bowlers, stats=stats, current_format=fmt)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
