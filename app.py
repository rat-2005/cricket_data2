import os

import duckdb
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify


load_dotenv(override=True)
DB_URL = os.environ.get("DATABASE_URL")

app = Flask(__name__)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

LOCAL_TABLES = [
    "competitions",
    "event_leagues",
    "leagues",
    "athletes",
    "player_stats_mv",
    "bowler_stats_mv",
]

RAW_TABLES = ["deliveries", "dismissals"]

print("Initializing DuckDB...")
con = duckdb.connect(":memory:")


def parquet_path(table):
    return os.path.join(DATA_DIR, f"{table}.parquet")


def ensure_parquet_files():
    missing = [table for table in LOCAL_TABLES if not os.path.exists(parquet_path(table))]
    if not missing:
        return

    if not DB_URL:
        raise RuntimeError(
            "Missing required Parquet files and DATABASE_URL is not set: "
            + ", ".join(missing)
        )

    print("Downloading small dashboard tables from PostgreSQL to Parquet...")
    con.execute("INSTALL postgres;")
    con.execute("LOAD postgres;")
    con.execute(f"ATTACH '{DB_URL}' AS pg (TYPE POSTGRES);")

    for table in missing:
        filepath = parquet_path(table)
        tmp_filepath = f"{filepath}.tmp"
        print(f"Exporting cricket.{table} to {filepath}...")
        try:
            con.execute(f"COPY pg.cricket.{table} TO '{tmp_filepath}' (FORMAT PARQUET);")
            os.replace(tmp_filepath, filepath)
            print(f"  -> Successfully exported {table}.")
        except Exception:
            if os.path.exists(tmp_filepath):
                os.remove(tmp_filepath)
            raise

    print("PostgreSQL export complete.")


def setup_views():
    available_tables = LOCAL_TABLES + [
        table for table in RAW_TABLES if os.path.exists(parquet_path(table))
    ]
    for table in available_tables:
        con.execute(
            f"CREATE OR REPLACE VIEW {table} AS "
            f"SELECT * FROM read_parquet('{parquet_path(table)}')"
        )


def raw_tables_available():
    return all(os.path.exists(parquet_path(table)) for table in RAW_TABLES)


def rows_from_postgres(query):
    if not DB_URL:
        raise RuntimeError(
            "DATABASE_URL is required for exact IPL queries when raw Parquet files are absent."
        )

    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            return [dict(row) for row in cur.fetchall()]


def one_from_postgres(query):
    rows = rows_from_postgres(query)
    return rows[0] if rows else {}


def aggregate_dashboard_data(format_filter, comp_filter):
    top_batters = con.execute(f"""
        SELECT
            a.full_name,
            a.image_url,
            CAST(SUM(mv.total_runs) AS INT) as total_runs,
            CAST(SUM(mv.total_sixes) AS INT) as total_sixes,
            ROUND((SUM(mv.total_runs)::NUMERIC / NULLIF(SUM(mv.balls_faced), 0)) * 100, 2) as strike_rate
        FROM player_stats_mv mv
        JOIN athletes a ON mv.athlete_id = a.id
        {format_filter}
        GROUP BY a.full_name, a.image_url
        ORDER BY total_runs DESC NULLS LAST
        LIMIT 10;
    """).fetchdf().to_dict("records")

    top_bowlers = con.execute(f"""
        SELECT
            a.full_name,
            a.image_url,
            CAST(SUM(mv.total_wickets) AS INT) as total_wickets,
            CAST(SUM(mv.runs_conceded) AS INT) as runs_conceded,
            ROUND(SUM(mv.overs_bowled)::NUMERIC, 1) as overs_bowled,
            CASE
                WHEN SUM(mv.overs_bowled) > 0
                THEN ROUND((SUM(mv.runs_conceded)::NUMERIC / SUM(mv.overs_bowled)::NUMERIC), 2)
                ELSE 0.0
            END as economy
        FROM bowler_stats_mv mv
        JOIN athletes a ON mv.athlete_id = a.id
        {format_filter}
        GROUP BY a.full_name, a.image_url
        ORDER BY total_wickets DESC NULLS LAST, economy ASC NULLS LAST
        LIMIT 10;
    """).fetchdf().to_dict("records")

    stats = con.execute(f"""
        SELECT
            (SELECT COUNT(*) FROM competitions c {comp_filter}) as total_matches,
            (SELECT SUM(total_runs) FROM player_stats_mv mv {format_filter}) as total_runs,
            (SELECT SUM(total_wickets) FROM bowler_stats_mv mv {format_filter}) as total_wickets,
            (SELECT SUM(total_sixes) FROM player_stats_mv mv {format_filter}) as total_sixes
    """).fetchdf().to_dict("records")[0]

    return top_batters, top_bowlers, stats


def exact_dashboard_data_from_postgres(class_condition):
    top_batters = rows_from_postgres(f"""
        SELECT
            COALESCE(a.full_name, mb.player_name) as full_name,
            a.image_url,
            SUM(mb.runs)::INT as total_runs,
            SUM(mb.sixes)::INT as total_sixes,
            ROUND((SUM(mb.runs)::NUMERIC / NULLIF(SUM(mb.balls_faced), 0)) * 100, 2) as strike_rate
        FROM cricket.matchcard_batting mb
        JOIN cricket.competitions c ON mb.competition_id = c.id
        LEFT JOIN cricket.athletes a ON mb.player_id = a.id
        WHERE {class_condition}
        GROUP BY COALESCE(a.id, mb.player_name), COALESCE(a.full_name, mb.player_name), a.image_url
        ORDER BY total_runs DESC NULLS LAST
        LIMIT 10;
    """)

    top_bowlers = rows_from_postgres(f"""
        SELECT
            COALESCE(a.full_name, mbo.player_name) as full_name,
            a.image_url,
            SUM(mbo.wickets)::INT as total_wickets,
            SUM(mbo.runs_conceded)::INT as runs_conceded,
            ROUND(SUM(mbo.overs)::NUMERIC, 1) as overs_bowled,
            CASE WHEN SUM(mbo.overs) > 0 THEN ROUND((SUM(mbo.runs_conceded)::NUMERIC / SUM(mbo.overs)::NUMERIC), 2) ELSE 0.0 END as economy
        FROM cricket.matchcard_bowling mbo
        JOIN cricket.competitions c ON mbo.competition_id = c.id
        LEFT JOIN cricket.athletes a ON mbo.player_id = a.id
        WHERE {class_condition}
        GROUP BY COALESCE(a.id, mbo.player_name), COALESCE(a.full_name, mbo.player_name), a.image_url
        ORDER BY total_wickets DESC NULLS LAST, economy ASC NULLS LAST
        LIMIT 10;
    """)

    stats = one_from_postgres(f"""
        SELECT
            (SELECT COUNT(DISTINCT mb.competition_id) FROM cricket.matchcard_batting mb JOIN cricket.competitions c ON mb.competition_id = c.id WHERE {class_condition}) as total_matches,
            (SELECT SUM(mb.runs) FROM cricket.matchcard_batting mb JOIN cricket.competitions c ON mb.competition_id = c.id WHERE {class_condition}) as total_runs,
            (SELECT SUM(mbo.wickets) FROM cricket.matchcard_bowling mbo JOIN cricket.competitions c ON mbo.competition_id = c.id WHERE {class_condition}) as total_wickets,
            (SELECT SUM(mb.sixes) FROM cricket.matchcard_batting mb JOIN cricket.competitions c ON mb.competition_id = c.id WHERE {class_condition}) as total_sixes
    """)

    return top_batters, top_bowlers, stats


def ipl_dashboard_data_from_duckdb():
    top_batters = con.execute("""
        SELECT
            a.full_name,
            a.image_url,
            CAST(SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END) AS INT) as total_runs,
            CAST(SUM(CASE WHEN d.is_boundary=TRUE AND d.runs_scored >= 6 THEN 1 ELSE 0 END) AS INT) as total_sixes,
            ROUND((SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END)::NUMERIC / NULLIF(COUNT(CASE WHEN d.is_wide=FALSE THEN 1 ELSE NULL END), 0)) * 100, 2) as strike_rate
        FROM deliveries d
        JOIN competitions c ON d.competition_id = c.id
        JOIN event_leagues el ON c.event_id = el.event_id
        JOIN leagues l ON el.league_id = l.id
        JOIN athletes a ON d.batsman_id = a.id
        WHERE l.name = 'Indian Premier League'
        GROUP BY a.full_name, a.image_url
        ORDER BY total_runs DESC NULLS LAST LIMIT 10;
    """).fetchdf().to_dict("records")

    top_bowlers = con.execute("""
        SELECT
            a.full_name,
            a.image_url,
            CAST(COUNT(dis.delivery_id) AS INT) as total_wickets,
            CAST(SUM(d.bowler_conceded) AS INT) as runs_conceded,
            ROUND(SUM(d.bowler_overs)::NUMERIC, 1) as overs_bowled,
            CASE WHEN SUM(d.bowler_overs) > 0 THEN ROUND((SUM(d.bowler_conceded)::NUMERIC / SUM(d.bowler_overs)::NUMERIC), 2) ELSE 0.0 END as economy
        FROM deliveries d
        JOIN competitions c ON d.competition_id = c.id
        JOIN event_leagues el ON c.event_id = el.event_id
        JOIN leagues l ON el.league_id = l.id
        JOIN athletes a ON d.bowler_id = a.id
        LEFT JOIN dismissals dis ON d.id = dis.delivery_id AND dis.type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out')
        WHERE l.name = 'Indian Premier League'
        GROUP BY a.full_name, a.image_url
        ORDER BY total_wickets DESC NULLS LAST, economy ASC NULLS LAST LIMIT 10;
    """).fetchdf().to_dict("records")

    stats = con.execute("""
        SELECT
            (SELECT COUNT(DISTINCT c.id) FROM competitions c JOIN event_leagues el ON c.event_id = el.event_id JOIN leagues l ON el.league_id = l.id WHERE l.name = 'Indian Premier League') as total_matches,
            (SELECT SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END) FROM deliveries d JOIN competitions c ON d.competition_id = c.id JOIN event_leagues el ON c.event_id = el.event_id JOIN leagues l ON el.league_id = l.id WHERE l.name = 'Indian Premier League') as total_runs,
            (SELECT COUNT(dis.delivery_id) FROM dismissals dis JOIN deliveries d ON dis.delivery_id = d.id JOIN competitions c ON d.competition_id = c.id JOIN event_leagues el ON c.event_id = el.event_id JOIN leagues l ON el.league_id = l.id WHERE l.name = 'Indian Premier League' AND dis.type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out')) as total_wickets,
            (SELECT SUM(CASE WHEN d.is_boundary=TRUE AND d.runs_scored >= 6 THEN 1 ELSE 0 END) FROM deliveries d JOIN competitions c ON d.competition_id = c.id JOIN event_leagues el ON c.event_id = el.event_id JOIN leagues l ON el.league_id = l.id WHERE l.name = 'Indian Premier League') as total_sixes
    """).fetchdf().to_dict("records")[0]

    return top_batters, top_bowlers, stats


def ipl_dashboard_data_from_postgres():
    top_batters = rows_from_postgres("""
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

    top_bowlers = rows_from_postgres("""
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

    stats = one_from_postgres("""
        SELECT
            (SELECT COUNT(DISTINCT c.id) FROM cricket.competitions c JOIN cricket.event_leagues el ON c.event_id = el.event_id JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name = 'Indian Premier League') as total_matches,
            (SELECT SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END) FROM cricket.deliveries d JOIN cricket.competitions c ON d.competition_id = c.id JOIN cricket.event_leagues el ON c.event_id = el.event_id JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name = 'Indian Premier League') as total_runs,
            (SELECT COUNT(dis.delivery_id) FROM cricket.dismissals dis JOIN cricket.deliveries d ON dis.delivery_id = d.id JOIN cricket.competitions c ON d.competition_id = c.id JOIN cricket.event_leagues el ON c.event_id = el.event_id JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name = 'Indian Premier League' AND dis.type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out')) as total_wickets,
            (SELECT SUM(CASE WHEN d.is_boundary=TRUE AND d.runs_scored >= 6 THEN 1 ELSE 0 END) FROM cricket.deliveries d JOIN cricket.competitions c ON d.competition_id = c.id JOIN cricket.event_leagues el ON c.event_id = el.event_id JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name = 'Indian Premier League') as total_sixes
    """)

    return top_batters, top_bowlers, stats


def ipl_dashboard_data():
    if raw_tables_available():
        return ipl_dashboard_data_from_duckdb()
    return ipl_dashboard_data_from_postgres()


ensure_parquet_files()
setup_views()


@app.route("/")
def index():
    fmt = request.args.get("format", "All")

    is_ipl = False
    if fmt == "Test":
        format_filter = "WHERE mv.format = 'Test'"
        comp_filter = "WHERE class_name = 'Test'"
        class_condition = "c.class_name = 'Test'"
    elif fmt == "ODI":
        format_filter = "WHERE mv.format = 'ODI'"
        comp_filter = "WHERE class_name = 'ODI'"
        class_condition = "c.class_name = 'ODI'"
    elif fmt == "T20":
        format_filter = "WHERE mv.format IN ('T20I', 'Twenty20', 'Women T20', 'Other T20', 'Women''s T20')"
        comp_filter = "WHERE class_name IN ('T20I', 'Twenty20', 'Women T20', 'Other T20', 'Women''s T20')"
        class_condition = "c.class_name IN ('T20I', 'Twenty20', 'Women T20', 'Other T20', 'Women''s T20')"
    elif fmt == "IPL":
        is_ipl = True
        format_filter = ""
        comp_filter = ""
        class_condition = ""
    else:
        format_filter = "WHERE mv.format IN ('Test', 'ODI', 'T20I')"
        comp_filter = "WHERE class_name IN ('Test', 'ODI', 'T20I')"
        class_condition = "c.class_name IN ('Test', 'ODI', 'T20I')"
        fmt = "All"

    if is_ipl:
        top_batters, top_bowlers, stats = ipl_dashboard_data()
    else:
        top_batters, top_bowlers, stats = aggregate_dashboard_data(format_filter, comp_filter)

    return render_template(
        "index.html",
        batters=top_batters,
        bowlers=top_bowlers,
        stats=stats,
        current_format=fmt,
    )


@app.route("/api/search")
def api_search():
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify([])
    
    # We use ILIKE for case-insensitive search
    # Prioritize full name matches, then short name matches
    sql = """
        SELECT id, full_name, image_url, country_code
        FROM cricket.athletes
        WHERE full_name ILIKE %s OR short_name ILIKE %s
        ORDER BY 
            CASE WHEN full_name ILIKE %s THEN 1 ELSE 2 END,
            full_name
        LIMIT 10;
    """
    
    like_q = f"%{query}%"
    start_q = f"{query}%"
    
    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (like_q, like_q, start_q))
            results = [dict(row) for row in cur.fetchall()]
            
    return jsonify(results)


@app.route("/player/<athlete_id>")
def player_profile(athlete_id):
    # Fetch player metadata
    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM cricket.athletes WHERE id = %s
            """, (athlete_id,))
            athlete = cur.fetchone()
            
            if not athlete:
                return "Player not found", 404
                
            # Batting stats per format
            cur.execute("""
                SELECT 
                    mv.format, 
                    mv.total_runs, 
                    mv.total_sixes, 
                    mv.balls_faced,
                    (SELECT SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END) 
                     FROM cricket.deliveries d 
                     JOIN cricket.competitions c ON d.competition_id = c.id 
                     WHERE d.batsman_id = %s AND c.class_name = mv.format 
                     GROUP BY c.id ORDER BY 1 DESC NULLS LAST LIMIT 1) as highest_score,
                    (SELECT COUNT(*) 
                     FROM cricket.deliveries d 
                     JOIN cricket.competitions c ON d.competition_id = c.id 
                     WHERE d.batsman_id = %s AND c.class_name = mv.format AND d.runs_scored = 0 AND d.is_wide=FALSE AND d.is_bye=FALSE AND d.is_leg_bye=FALSE) as dot_balls
                FROM cricket.player_stats_mv mv
                WHERE mv.athlete_id = %s
            """, (athlete_id, athlete_id, athlete_id))
            batting_raw = [dict(row) for row in cur.fetchall()]
            
            batting_stats = {}
            for row in batting_raw:
                fmt = row['format']
                runs = row['total_runs'] or 0
                balls = row['balls_faced'] or 0
                dots = row['dot_balls'] or 0
                sr = round((runs / balls * 100), 2) if balls > 0 else 0
                dot_pct = round((dots / balls * 100), 1) if balls > 0 else 0
                batting_stats[fmt] = {
                    'runs': runs,
                    'balls': balls,
                    'sr': sr,
                    'sixes': row['total_sixes'] or 0,
                    'hs': row['highest_score'] or 0,
                    'dot_pct': dot_pct
                }
                
            # Bowling stats per format
            cur.execute("""
                SELECT 
                    mv.format, 
                    mv.total_wickets, 
                    mv.runs_conceded, 
                    mv.overs_bowled,
                    -- Best bowling query: max wickets, then min runs in a single match
                    (SELECT ARRAY[COUNT(dis.delivery_id)::INT, SUM(CASE WHEN d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN CASE WHEN d.is_no_ball=TRUE OR d.is_wide=TRUE THEN 1 ELSE 0 END ELSE d.runs_scored END)::INT]
                     FROM cricket.deliveries d 
                     JOIN cricket.competitions c ON d.competition_id = c.id 
                     LEFT JOIN cricket.dismissals dis ON d.id = dis.delivery_id AND dis.type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out')
                     WHERE d.bowler_id = %s AND c.class_name = mv.format 
                     GROUP BY c.id 
                     ORDER BY COUNT(dis.delivery_id) DESC NULLS LAST, SUM(CASE WHEN d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN CASE WHEN d.is_no_ball=TRUE OR d.is_wide=TRUE THEN 1 ELSE 0 END ELSE d.runs_scored END) ASC NULLS LAST LIMIT 1) as best_bowling
                FROM cricket.bowler_stats_mv mv
                WHERE mv.athlete_id = %s
            """, (athlete_id, athlete_id))
            bowling_raw = [dict(row) for row in cur.fetchall()]
            
            bowling_stats = {}
            for row in bowling_raw:
                fmt = row['format']
                w = row['total_wickets'] or 0
                rc = row['runs_conceded'] or 0
                overs = float(row['overs_bowled'] or 0)
                econ = round((rc / overs), 2) if overs > 0 else 0
                bb_arr = row['best_bowling']
                if bb_arr and bb_arr[0] is not None:
                    bb = f"{bb_arr[0]}/{bb_arr[1]}"
                else:
                    bb = "-"
                    
                bowling_stats[fmt] = {
                    'wickets': w,
                    'runs': rc,
                    'overs': overs,
                    'econ': econ,
                    'bb': bb
                }

    return render_template(
        "player.html",
        athlete=dict(athlete),
        batting=batting_stats,
        bowling=bowling_stats
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
