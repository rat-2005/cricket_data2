import os

import duckdb
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from contextlib import closing, contextmanager
from psycopg2 import pool


load_dotenv(override=True)
DB_URL = os.environ.get("DATABASE_URL")

app = Flask(__name__)

# Global connection pool
db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, DB_URL)

@contextmanager
def get_db_connection():
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)


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

RAW_TABLES = ["deliveries", "dismissals", "cricsheet_matches", "cricsheet_deliveries"]

def get_format_where_clause(format_filter, where_d, params_d, where_cricsheet, params_cricsheet):
    if format_filter == 'All':
        return
    if format_filter in ('T20', 'Twenty20'):
        where_d.append("c.class_name IN ('T20', 'Twenty20', 'T20I', 'IPL', 'Women T20', 'Women''s T20', 'Other T20', 'Youth T20I', 'ICCT')")
        where_cricsheet.append("m.format IN ('T20', 'Twenty20', 'IT20')")
    elif format_filter == 'ODI':
        where_d.append("c.class_name IN ('ODI', 'Women''s ODI', 'Youth ODI', 'List A', 'Other OD')")
        where_cricsheet.append("m.format = 'ODI'")
    elif format_filter == 'Test':
        where_d.append("c.class_name IN ('Test', 'Women''s Test', 'Youth Test', 'First-class', 'MD')")
        where_cricsheet.append("m.format IN ('Test', 'MD')")
    else:
        where_d.append("c.class_name = %s")
        params_d.append(format_filter)
        where_cricsheet.append("m.format = %s")
        params_cricsheet.append(format_filter)

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

    with get_db_connection() as conn:
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


@app.route("/batter")
def batter_page():
    athlete_id = request.args.get('id')
    return render_template("batter.html", athlete_id=athlete_id)

@app.route("/bowler")
def bowler_page():
    athlete_id = request.args.get('id')
    return render_template("bowler.html", athlete_id=athlete_id)

@app.route("/faceoff")
def faceoff_page():
    batter_id = request.args.get('batter_id')
    bowler_id = request.args.get('bowler_id')
    return render_template("faceoff.html", batter_id=batter_id, bowler_id=bowler_id)

@app.route("/api/search")
def search():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 1:
        return jsonify([])
        
    like_q = f"%{query}%"
    start_q = f"{query}%"
    
    against_batter = request.args.get('against_batter')
    against_bowler = request.args.get('against_bowler')
    
    valid_ids = None
    if against_batter:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT bowler_id FROM cricket.deliveries WHERE batsman_id = %s
                    UNION
                    SELECT DISTINCT bowler_id FROM cricket.cricsheet_deliveries WHERE batsman_id = %s
                """, (against_batter, against_batter))
                valid_ids = [str(row[0]) for row in cur.fetchall()]
    elif against_bowler:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT batsman_id FROM cricket.deliveries WHERE bowler_id = %s
                    UNION
                    SELECT DISTINCT batsman_id FROM cricket.cricsheet_deliveries WHERE bowler_id = %s
                """, (against_bowler, against_bowler))
                valid_ids = [str(row[0]) for row in cur.fetchall()]
                
    sql = "SELECT id, full_name, country_code FROM athletes WHERE (full_name ILIKE ? OR short_name ILIKE ?)"
    params = [like_q, like_q]
    
    if valid_ids is not None:
        if not valid_ids:
            return jsonify([])
        placeholders = ','.join(['?'] * len(valid_ids))
        sql += f" AND id IN ({placeholders})"
        params.extend(valid_ids)
        
    sql += " ORDER BY CASE WHEN full_name ILIKE ? THEN 1 ELSE 2 END, full_name LIMIT 10"
    params.append(start_q)
    
    # Use DuckDB for instant local searching instead of remote Postgres
    results = con.execute(sql, params).fetchdf().to_dict('records')
    
    # Cast id back to string to match previous API response
    for r in results:
        r['id'] = str(r['id'])
        
    return jsonify(results)



@app.route("/player")
def player_search():
    return render_template("player.html", athlete=None, batting=None, bowling=None)

@app.route("/player/<athlete_id>")
def player_profile(athlete_id):
    # Fetch player metadata
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM cricket.athletes WHERE id = %s
            """, (athlete_id,))
            athlete = cur.fetchone()
            
            if not athlete:
                return "Player not found", 404
                
            # Batting stats optimized (no materialized views)
            batting_query = """
            WITH combined_deliveries AS (
                SELECT 
                    d.batsman_id as athlete_id,
                    c.class_name as format,
                    d.competition_id as match_id,
                    d.batsman_runs,
                    d.is_wide,
                    d.is_bye,
                    d.is_leg_bye,
                    l.name as league_name
                FROM cricket.deliveries d
                JOIN cricket.competitions c ON c.id = d.competition_id
                LEFT JOIN cricket.event_leagues el ON c.event_id = el.event_id
                LEFT JOIN cricket.leagues l ON el.league_id = l.id
                WHERE d.batsman_id = %s
                
                UNION ALL
                
                SELECT 
                    d.batsman_id as athlete_id,
                    CASE WHEN m.format = 'MD' THEN 'Test' ELSE m.format END as format,
                    d.match_id as match_id,
                    d.batsman_runs,
                    d.is_wide,
                    d.is_bye,
                    d.is_leg_bye,
                    NULL as league_name
                FROM cricket.cricsheet_deliveries d
                JOIN cricket.cricsheet_matches m ON m.id = d.match_id
                WHERE d.batsman_id = %s
            ),
            match_aggregates AS (
                SELECT 
                    athlete_id, 
                    CASE WHEN league_name = 'Indian Premier League' THEN 'IPL' ELSE format END as format,
                    match_id,
                    SUM(batsman_runs) as match_score,
                    SUM(CASE WHEN batsman_runs = 0 AND is_wide = false AND is_bye = false AND is_leg_bye = false THEN 1 ELSE 0 END) as match_dots,
                    SUM(CASE WHEN batsman_runs >= 6 THEN 1 ELSE 0 END) as match_sixes,
                    SUM(CASE WHEN is_wide = false THEN 1 ELSE 0 END) as match_balls_faced
                FROM combined_deliveries
                GROUP BY athlete_id, CASE WHEN league_name = 'Indian Premier League' THEN 'IPL' ELSE format END, match_id
            )
            SELECT 
                format,
                SUM(match_score)::integer as total_runs,
                SUM(match_sixes)::integer as total_sixes,
                SUM(match_balls_faced)::integer as balls_faced,
                MAX(match_score)::integer as highest_score,
                SUM(match_dots)::integer as dot_balls
            FROM match_aggregates
            GROUP BY format
            """
            cur.execute(batting_query, (athlete_id, athlete_id))
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
                
            # Bowling stats optimized (no materialized views)
            bowling_query = """
            WITH combined_bowling AS (
                SELECT 
                    d.bowler_id as athlete_id,
                    c.class_name as format,
                    d.competition_id as match_id,
                    CASE WHEN dis.delivery_id IS NOT NULL THEN 1 ELSE 0 END as is_wicket,
                    d.bowler_conceded,
                    d.bowler_overs,
                    l.name as league_name
                FROM cricket.deliveries d
                JOIN cricket.competitions c ON c.id = d.competition_id
                LEFT JOIN cricket.dismissals dis ON d.id = dis.delivery_id AND dis.type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out')
                LEFT JOIN cricket.event_leagues el ON c.event_id = el.event_id
                LEFT JOIN cricket.leagues l ON el.league_id = l.id
                WHERE d.bowler_id = %s
                
                UNION ALL
                
                SELECT 
                    d.bowler_id as athlete_id,
                    CASE WHEN m.format = 'MD' THEN 'Test' ELSE m.format END as format,
                    d.match_id as match_id,
                    CASE WHEN d.dismissal_type IS NOT NULL AND d.dismissal_type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out') THEN 1 ELSE 0 END as is_wicket,
                    CASE WHEN d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN CASE WHEN d.is_no_ball=TRUE OR d.is_wide=TRUE THEN 1 ELSE 0 END ELSE d.runs_scored END as bowler_conceded,
                    CASE WHEN d.is_wide=TRUE OR d.is_no_ball=TRUE THEN 0 ELSE 1.0/6.0 END as bowler_overs,
                    NULL as league_name
                FROM cricket.cricsheet_deliveries d
                JOIN cricket.cricsheet_matches m ON m.id = d.match_id
                WHERE d.bowler_id = %s
            ),
            match_aggregates AS (
                SELECT 
                    athlete_id, 
                    CASE WHEN league_name = 'Indian Premier League' THEN 'IPL' ELSE format END as format,
                    match_id,
                    SUM(is_wicket) as match_wickets,
                    SUM(bowler_conceded) as match_runs_conceded,
                    SUM(bowler_overs) as match_overs_bowled
                FROM combined_bowling
                GROUP BY athlete_id, CASE WHEN league_name = 'Indian Premier League' THEN 'IPL' ELSE format END, match_id
            )
            SELECT 
                format,
                SUM(match_wickets)::integer as total_wickets,
                SUM(match_runs_conceded)::integer as runs_conceded,
                SUM(match_overs_bowled) as overs_bowled,
                MAX(match_wickets)::integer as best_wickets,
                (
                    SELECT MIN(m2.match_runs_conceded) 
                    FROM match_aggregates m2 
                    WHERE m2.format = match_aggregates.format 
                    AND m2.match_wickets = MAX(match_aggregates.match_wickets)
                )::integer as best_runs
            FROM match_aggregates
            GROUP BY format
            """
            cur.execute(bowling_query, (athlete_id, athlete_id))
            bowling_raw = [dict(row) for row in cur.fetchall()]
            
            bowling_stats = {}
            for row in bowling_raw:
                fmt = row['format']
                w = row['total_wickets'] or 0
                rc = row['runs_conceded'] or 0
                
                overs = float(row['overs_bowled'] or 0)
                econ = round((rc / overs), 2) if overs > 0 else 0
                
                best_w = row['best_wickets'] or 0
                best_r = row['best_runs'] or 0
                
                if best_w > 0:
                    bb = f"{best_w}/{best_r}"
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
# Global cache for static filter data to avoid 3-second DB queries on every page load
_filters_cache = None

@app.route("/api/filters")
def filters():
    global _filters_cache
    if _filters_cache is None:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get distinct leagues/competitions
                cur.execute("""
                    SELECT DISTINCT l.name as league 
                    FROM cricket.leagues l
                """)
                leagues = [row['league'] for row in cur.fetchall()]
                
                # Get distinct venues
                cur.execute("SELECT DISTINCT full_name FROM cricket.venues WHERE full_name IS NOT NULL")
                venues = [row['full_name'] for row in cur.fetchall()]
                
        _filters_cache = {
            "formats": ["T20", "ODI", "Test"],
            "leagues": sorted(leagues),
            "phases": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"],
            "venues": sorted(venues),
            "opponents": ["India", "Australia", "England", "South Africa", "New Zealand", "Pakistan", "Sri Lanka", "West Indies", "Bangladesh", "Afghanistan", "Chennai Super Kings", "Mumbai Indians", "Royal Challengers Bangalore", "Kolkata Knight Riders", "Delhi Capitals", "Rajasthan Royals", "Punjab Kings", "Sunrisers Hyderabad"]
        }
        
    return jsonify(_filters_cache)

@app.route("/api/faceoff_filters")
def faceoff_filters():
    batter_id = request.args.get('batter_id')
    bowler_id = request.args.get('bowler_id')
    format_filter = request.args.get('format', 'All')
    league_filter = request.args.get('league', 'All')
    venue_filter = request.args.get('venue', 'All')
    phase_filter = request.args.get('phase', 'All')
    
    if not batter_id or not bowler_id:
        return jsonify({"formats": [], "leagues": [], "venues": [], "phases": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"]})
        
    where_d = ["d.batsman_id = %s", "d.bowler_id = %s"]
    where_cricsheet = ["d.batsman_id = %s", "d.bowler_id = %s"]
    params_d = [batter_id, bowler_id]
    params_cricsheet = [batter_id, bowler_id]
    
    if format_filter != 'All':
        get_format_where_clause(format_filter, where_d, params_d, where_cricsheet, params_cricsheet)
        
    if league_filter != 'All':
        where_d.append("l.name = %s")
        params_d.append(league_filter)
        # Note: cricsheet doesn't support league natively in this CTE
        where_cricsheet.append("1=0") 
        
    if venue_filter != 'All':
        where_d.append("v.full_name = %s")
        params_d.append(venue_filter)
        # Note: m.venue doesn't exist
        where_cricsheet.append("1=0")
        
    if phase_filter == 'Powerplay':
        where_d.append("d.over_number <= 6")
        where_cricsheet.append("d.over_number <= 5")
    elif phase_filter == 'Middle':
        where_d.append("d.over_number > 6 AND d.over_number <= 15")
        where_cricsheet.append("d.over_number > 5 AND d.over_number <= 14")
    elif phase_filter == 'Death':
        where_d.append("d.over_number > 15")
        where_cricsheet.append("d.over_number > 14")
        
    where_clause_d = " AND ".join(where_d)
    where_clause_cricsheet = " AND ".join(where_cricsheet)
    
    query = f"""
    WITH combined_faceoff AS (
        SELECT 
            CASE 
                WHEN c.class_name IN ('T20', 'Twenty20', 'T20I', 'IPL', 'Women T20', 'Women''s T20', 'Other T20', 'Youth T20I', 'ICCT') THEN 'T20'
                WHEN c.class_name IN ('ODI', 'Women''s ODI', 'Youth ODI', 'List A', 'Other OD') THEN 'ODI'
                WHEN c.class_name IN ('Test', 'Women''s Test', 'Youth Test', 'First-class', 'MD') THEN 'Test'
                ELSE c.class_name 
            END as format,
            l.name as league,
            v.full_name as venue
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON c.id = d.competition_id
        LEFT JOIN cricket.event_leagues el ON c.event_id = el.event_id
        LEFT JOIN cricket.leagues l ON el.league_id = l.id
        LEFT JOIN cricket.venues v ON c.venue_id = v.id
        WHERE {where_clause_d}
        
        UNION ALL
        
        SELECT 
            CASE 
                WHEN m.format IN ('T20', 'Twenty20', 'IT20') THEN 'T20'
                WHEN m.format = 'ODI' THEN 'ODI'
                WHEN m.format IN ('Test', 'MD') THEN 'Test'
                ELSE m.format 
            END as format,
            NULL as league,
            NULL as venue
        FROM cricket.cricsheet_deliveries d
        JOIN cricket.cricsheet_matches m ON m.id = d.match_id
        WHERE {where_clause_cricsheet}
    )
    SELECT 
        array_remove(array_agg(DISTINCT format), NULL) as formats,
        array_remove(array_agg(DISTINCT league), NULL) as leagues,
        array_remove(array_agg(DISTINCT venue), NULL) as venues
    FROM combined_faceoff
    """
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params_d + params_cricsheet)
            res = cur.fetchone()
            
            return jsonify({
                "formats": sorted(res['formats']) if res and res['formats'] else [],
                "leagues": sorted(res['leagues']) if res and res['leagues'] else [],
                "venues": sorted(res['venues']) if res and res['venues'] else [],
                "phases": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"]
            })

@app.route("/api/athlete/<athlete_id>")
def athlete_api(athlete_id):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM cricket.athletes WHERE id = %s", (athlete_id,))
            athlete = cur.fetchone()
            if athlete:
                return jsonify(dict(athlete))
            return jsonify({"error": "not found"}), 404

@app.route("/api/stats/batter")
def stats_batter():
    athlete_id = request.args.get('id')
    if not athlete_id:
        return jsonify({"error": "missing id"}), 400
        
    fmt = request.args.get('format', 'All')
    league = request.args.get('league', 'All')
    opponent = request.args.get('opponent', 'All')
    phase = request.args.get('phase', 'All')
    venue = request.args.get('venue', 'All')
    
    # We will build the where clauses dynamically
    where_d = ["d.batsman_id = %s"]
    where_cricsheet = ["d.batsman_id = %s"]
    params_d = [athlete_id]
    params_cricsheet = [athlete_id]
    
    get_format_where_clause(fmt, where_d, params_d, where_cricsheet, params_cricsheet)
        
    if league != 'All':
        where_d.append("l.name = %s")
        params_d.append(league)
        where_cricsheet.append("1=0")
        
    if venue != 'All':
        where_d.append("v.full_name = %s")
        params_d.append(venue)
        where_cricsheet.append("1=0")
        
    if phase == 'Powerplay':
        where_d.append("d.over_number <= 6")
        where_cricsheet.append("d.over_number <= 5") # 0-indexed in cricsheet
    elif phase == 'Middle':
        where_d.append("d.over_number > 6 AND d.over_number <= 15")
        where_cricsheet.append("d.over_number > 5 AND d.over_number <= 14")
    elif phase == 'Death':
        where_d.append("d.over_number > 15")
        where_cricsheet.append("d.over_number > 14")
        
    # NOTE: Opponent team is tricky as we need to join innings/match_teams
    # For now we'll skip opponent team strict filtering in this optimized query
    # unless we join match_teams which slows it down.
        
    where_clause_d = " AND ".join(where_d)
    where_clause_cricsheet = " AND ".join(where_cricsheet)
    
    query = f"""
    WITH combined_deliveries AS (
        SELECT 
            d.competition_id as match_id,
            d.batsman_runs,
            d.is_wide,
            d.is_bye,
            d.is_leg_bye
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON c.id = d.competition_id
        LEFT JOIN cricket.event_leagues el ON c.event_id = el.event_id
        LEFT JOIN cricket.leagues l ON el.league_id = l.id
        LEFT JOIN cricket.venues v ON c.venue_id = v.id
        WHERE {where_clause_d}
        
        UNION ALL
        
        SELECT 
            d.match_id as match_id,
            d.batsman_runs,
            d.is_wide,
            d.is_bye,
            d.is_leg_bye
        FROM cricket.cricsheet_deliveries d
        JOIN cricket.cricsheet_matches m ON m.id = d.match_id
        WHERE {where_clause_cricsheet}
    ),
    match_aggregates AS (
        SELECT 
            match_id,
            SUM(batsman_runs) as match_score,
            SUM(CASE WHEN batsman_runs = 0 AND is_wide = false AND is_bye = false AND is_leg_bye = false THEN 1 ELSE 0 END) as match_dots,
            SUM(CASE WHEN batsman_runs >= 6 THEN 1 ELSE 0 END) as match_sixes,
            SUM(CASE WHEN is_wide = false THEN 1 ELSE 0 END) as match_balls_faced
        FROM combined_deliveries
        GROUP BY match_id
    )
    SELECT 
        SUM(match_score)::integer as total_runs,
        SUM(match_sixes)::integer as total_sixes,
        SUM(match_balls_faced)::integer as balls_faced,
        MAX(match_score)::integer as highest_score,
        SUM(match_dots)::integer as dot_balls
    FROM match_aggregates
    """
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params_d + params_cricsheet)
            res = cur.fetchone()
            
            runs = res['total_runs'] or 0
            balls = res['balls_faced'] or 0
            dots = res['dot_balls'] or 0
            
            return jsonify({
                "runs": runs,
                "balls": balls,
                "sr": round((runs / balls * 100), 2) if balls > 0 else 0,
                "sixes": res['total_sixes'] or 0,
                "hs": res['highest_score'] or 0,
                "dot_pct": round((dots / balls * 100), 1) if balls > 0 else 0
            })

@app.route("/api/stats/bowler")
def stats_bowler():
    athlete_id = request.args.get('id')
    if not athlete_id:
        return jsonify({"error": "missing id"}), 400
        
    fmt = request.args.get('format', 'All')
    league = request.args.get('league', 'All')
    opponent = request.args.get('opponent', 'All')
    phase = request.args.get('phase', 'All')
    venue = request.args.get('venue', 'All')
    
    where_d = ["d.bowler_id = %s"]
    where_cricsheet = ["d.bowler_id = %s"]
    params_d = [athlete_id]
    params_cricsheet = [athlete_id]
    
    get_format_where_clause(fmt, where_d, params_d, where_cricsheet, params_cricsheet)
        
    if league != 'All':
        where_d.append("l.name = %s")
        params_d.append(league)
        where_cricsheet.append("1=0")
        
    if venue != 'All':
        where_d.append("v.full_name = %s")
        params_d.append(venue)
        where_cricsheet.append("1=0")
        
    if phase == 'Powerplay':
        where_d.append("d.over_number <= 6")
        where_cricsheet.append("d.over_number <= 5")
    elif phase == 'Middle':
        where_d.append("d.over_number > 6 AND d.over_number <= 15")
        where_cricsheet.append("d.over_number > 5 AND d.over_number <= 14")
    elif phase == 'Death':
        where_d.append("d.over_number > 15")
        where_cricsheet.append("d.over_number > 14")
        
    where_clause_d = " AND ".join(where_d)
    where_clause_cricsheet = " AND ".join(where_cricsheet)
    
    query = f"""
    WITH combined_bowling AS (
        SELECT 
            d.competition_id as match_id,
            CASE WHEN dis.delivery_id IS NOT NULL THEN 1 ELSE 0 END as is_wicket,
            d.bowler_conceded,
            d.bowler_overs
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON c.id = d.competition_id
        LEFT JOIN cricket.event_leagues el ON c.event_id = el.event_id
        LEFT JOIN cricket.leagues l ON el.league_id = l.id
        LEFT JOIN cricket.venues v ON c.venue_id = v.id
        LEFT JOIN cricket.dismissals dis ON d.id = dis.delivery_id AND dis.type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out')
        WHERE {where_clause_d}
        
        UNION ALL
        
        SELECT 
            d.match_id as match_id,
            CASE WHEN d.dismissal_type IS NOT NULL AND d.dismissal_type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out') THEN 1 ELSE 0 END as is_wicket,
            CASE WHEN d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN CASE WHEN d.is_no_ball=TRUE OR d.is_wide=TRUE THEN 1 ELSE 0 END ELSE d.runs_scored END as bowler_conceded,
            CASE WHEN d.is_wide=TRUE OR d.is_no_ball=TRUE THEN 0 ELSE 1.0/6.0 END as bowler_overs
        FROM cricket.cricsheet_deliveries d
        JOIN cricket.cricsheet_matches m ON m.id = d.match_id
        WHERE {where_clause_cricsheet}
    ),
    match_aggregates AS (
        SELECT 
            match_id,
            SUM(is_wicket) as match_wickets,
            SUM(bowler_conceded) as match_runs_conceded,
            SUM(bowler_overs) as match_overs_bowled
        FROM combined_bowling
        GROUP BY match_id
    )
    SELECT 
        SUM(match_wickets)::integer as total_wickets,
        SUM(match_runs_conceded)::integer as runs_conceded,
        SUM(match_overs_bowled) as overs_bowled,
        MAX(match_wickets)::integer as best_wickets,
        (
            SELECT MIN(m2.match_runs_conceded) 
            FROM match_aggregates m2 
            WHERE m2.match_wickets = MAX(match_aggregates.match_wickets)
        )::integer as best_runs
    FROM match_aggregates
    """
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params_d + params_cricsheet)
            res = cur.fetchone()
            
            w = res['total_wickets'] or 0
            rc = res['runs_conceded'] or 0
            ov = float(res['overs_bowled'] or 0)
            
            avg = round((rc / w), 2) if w > 0 else 0
            eco = round((rc / ov), 2) if ov > 0 else 0
            
            best_w = res['best_wickets'] or 0
            best_r = res['best_runs'] or 0
            best_bowling = f"{best_w}/{best_r}" if best_w > 0 else "-"
            
            return jsonify({
                "wickets": w,
                "runs": rc,
                "overs": round(ov, 1),
                "avg": avg,
                "eco": eco,
                "best": best_bowling
            })

@app.route("/api/stats/faceoff")
def stats_faceoff():
    batter_id = request.args.get('batter_id')
    bowler_id = request.args.get('bowler_id')
    
    if not batter_id or not bowler_id:
        return jsonify({"error": "missing ids"}), 400
        
    fmt = request.args.get('format', 'All')
    league = request.args.get('league', 'All')
    phase = request.args.get('phase', 'All')
    venue = request.args.get('venue', 'All')
    
    where_d = ["d.batsman_id = %s", "d.bowler_id = %s"]
    where_cricsheet = ["d.batsman_id = %s", "d.bowler_id = %s"]
    params_d = [batter_id, bowler_id]
    params_cricsheet = [batter_id, bowler_id]
    
    get_format_where_clause(fmt, where_d, params_d, where_cricsheet, params_cricsheet)
        
    if league != 'All':
        where_d.append("l.name = %s")
        params_d.append(league)
        where_cricsheet.append("1=0")
        
    if venue != 'All':
        where_d.append("v.full_name = %s")
        params_d.append(venue)
        where_cricsheet.append("1=0")
        
    if phase == 'Powerplay':
        where_d.append("d.over_number <= 6")
        where_cricsheet.append("d.over_number <= 5")
    elif phase == 'Middle':
        where_d.append("d.over_number > 6 AND d.over_number <= 15")
        where_cricsheet.append("d.over_number > 5 AND d.over_number <= 14")
    elif phase == 'Death':
        where_d.append("d.over_number > 15")
        where_cricsheet.append("d.over_number > 14")
        
    where_clause_d = " AND ".join(where_d)
    where_clause_cricsheet = " AND ".join(where_cricsheet)
    
    query = f"""
    WITH combined_faceoff AS (
        SELECT 
            d.batsman_runs,
            CASE WHEN dis.delivery_id IS NOT NULL AND dis.type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out') THEN 1 ELSE 0 END as is_wicket,
            d.is_wide,
            d.is_bye,
            d.is_leg_bye
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON c.id = d.competition_id
        LEFT JOIN cricket.event_leagues el ON c.event_id = el.event_id
        LEFT JOIN cricket.leagues l ON el.league_id = l.id
        LEFT JOIN cricket.venues v ON c.venue_id = v.id
        LEFT JOIN cricket.dismissals dis ON d.id = dis.delivery_id
        WHERE {where_clause_d}
        
        UNION ALL
        
        SELECT 
            d.batsman_runs,
            CASE WHEN d.dismissal_type IS NOT NULL AND d.dismissal_type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out') THEN 1 ELSE 0 END as is_wicket,
            d.is_wide,
            d.is_bye,
            d.is_leg_bye
        FROM cricket.cricsheet_deliveries d
        JOIN cricket.cricsheet_matches m ON m.id = d.match_id
        WHERE {where_clause_cricsheet}
    )
    SELECT 
        SUM(batsman_runs)::integer as total_runs,
        SUM(is_wicket)::integer as total_dismissals,
        SUM(CASE WHEN batsman_runs = 0 AND is_wide = false AND is_bye = false AND is_leg_bye = false THEN 1 ELSE 0 END)::integer as dot_balls,
        SUM(CASE WHEN batsman_runs >= 4 THEN 1 ELSE 0 END)::integer as boundaries,
        SUM(CASE WHEN batsman_runs >= 6 THEN 1 ELSE 0 END)::integer as sixes,
        SUM(CASE WHEN is_wide = false THEN 1 ELSE 0 END)::integer as balls_faced
    FROM combined_faceoff
    """
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params_d + params_cricsheet)
            res = cur.fetchone()
            
            runs = res['total_runs'] or 0
            balls = res['balls_faced'] or 0
            dots = res['dot_balls'] or 0
            dismissals = res['total_dismissals'] or 0
            
            return jsonify({
                "runs": runs,
                "balls": balls,
                "sr": round((runs / balls * 100), 2) if balls > 0 else 0,
                "dismissals": dismissals,
                "avg": round((runs / dismissals), 2) if dismissals > 0 else (runs if runs > 0 else 0),
                "boundaries": res['boundaries'] or 0,
                "sixes": res['sixes'] or 0,
                "dot_pct": round((dots / balls * 100), 1) if balls > 0 else 0
            })

@app.route("/api/batter_filters")
def batter_filters():
    athlete_id = request.args.get('id')
    if not athlete_id:
        return jsonify({"formats": [], "leagues": [], "venues": [], "phases": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"], "opponents": []})
        
    format_filter = request.args.get('format', 'All')
    league_filter = request.args.get('league', 'All')
    venue_filter = request.args.get('venue', 'All')
    phase_filter = request.args.get('phase', 'All')
    
    where_d = ["d.batsman_id = %s"]
    where_cricsheet = ["d.batsman_id = %s"]
    params_d = [athlete_id]
    params_cricsheet = [athlete_id]
    
    get_format_where_clause(format_filter, where_d, params_d, where_cricsheet, params_cricsheet)
        
    if league_filter != 'All':
        where_d.append("l.name = %s")
        params_d.append(league_filter)
        where_cricsheet.append("1=0") 
        
    if venue_filter != 'All':
        where_d.append("v.full_name = %s")
        params_d.append(venue_filter)
        where_cricsheet.append("1=0")
        
    if phase_filter == 'Powerplay':
        where_d.append("d.over_number <= 6")
        where_cricsheet.append("d.over_number <= 5")
    elif phase_filter == 'Middle':
        where_d.append("d.over_number > 6 AND d.over_number <= 15")
        where_cricsheet.append("d.over_number > 5 AND d.over_number <= 14")
    elif phase_filter == 'Death':
        where_d.append("d.over_number > 15")
        where_cricsheet.append("d.over_number > 14")
        
    where_clause_d = " AND ".join(where_d)
    where_clause_cricsheet = " AND ".join(where_cricsheet)
    
    query = f"""
    WITH combined AS (
        SELECT 
            CASE 
                WHEN c.class_name IN ('T20', 'Twenty20', 'T20I', 'IPL', 'Women T20', 'Women''s T20', 'Other T20', 'Youth T20I', 'ICCT') THEN 'T20'
                WHEN c.class_name IN ('ODI', 'Women''s ODI', 'Youth ODI', 'List A', 'Other OD') THEN 'ODI'
                WHEN c.class_name IN ('Test', 'Women''s Test', 'Youth Test', 'First-class', 'MD') THEN 'Test'
                ELSE c.class_name 
            END as format,
            l.name as league,
            v.full_name as venue
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON c.id = d.competition_id
        LEFT JOIN cricket.event_leagues el ON c.event_id = el.event_id
        LEFT JOIN cricket.leagues l ON el.league_id = l.id
        LEFT JOIN cricket.venues v ON c.venue_id = v.id
        WHERE {where_clause_d}
        
        UNION ALL
        
        SELECT 
            CASE 
                WHEN m.format IN ('T20', 'Twenty20', 'IT20') THEN 'T20'
                WHEN m.format = 'ODI' THEN 'ODI'
                WHEN m.format IN ('Test', 'MD') THEN 'Test'
                ELSE m.format 
            END as format,
            NULL as league,
            NULL as venue
        FROM cricket.cricsheet_deliveries d
        JOIN cricket.cricsheet_matches m ON m.id = d.match_id
        WHERE {where_clause_cricsheet}
    )
    SELECT 
        array_remove(array_agg(DISTINCT format), NULL) as formats,
        array_remove(array_agg(DISTINCT league), NULL) as leagues,
        array_remove(array_agg(DISTINCT venue), NULL) as venues
    FROM combined
    """
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params_d + params_cricsheet)
            res = cur.fetchone()
            
            return jsonify({
                "formats": sorted(res['formats']) if res and res['formats'] else [],
                "leagues": sorted(res['leagues']) if res and res['leagues'] else [],
                "venues": sorted(res['venues']) if res and res['venues'] else [],
                "phases": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"]
            })

@app.route("/api/bowler_filters")
def bowler_filters():
    athlete_id = request.args.get('id')
    if not athlete_id:
        return jsonify({"formats": [], "leagues": [], "venues": [], "phases": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"], "opponents": []})
        
    format_filter = request.args.get('format', 'All')
    league_filter = request.args.get('league', 'All')
    venue_filter = request.args.get('venue', 'All')
    phase_filter = request.args.get('phase', 'All')
    
    where_d = ["d.bowler_id = %s"]
    where_cricsheet = ["d.bowler_id = %s"]
    params_d = [athlete_id]
    params_cricsheet = [athlete_id]
    
    get_format_where_clause(format_filter, where_d, params_d, where_cricsheet, params_cricsheet)
        
    if league_filter != 'All':
        where_d.append("l.name = %s")
        params_d.append(league_filter)
        where_cricsheet.append("1=0") 
        
    if venue_filter != 'All':
        where_d.append("v.full_name = %s")
        params_d.append(venue_filter)
        where_cricsheet.append("1=0")
        
    if phase_filter == 'Powerplay':
        where_d.append("d.over_number <= 6")
        where_cricsheet.append("d.over_number <= 5")
    elif phase_filter == 'Middle':
        where_d.append("d.over_number > 6 AND d.over_number <= 15")
        where_cricsheet.append("d.over_number > 5 AND d.over_number <= 14")
    elif phase_filter == 'Death':
        where_d.append("d.over_number > 15")
        where_cricsheet.append("d.over_number > 14")
        
    where_clause_d = " AND ".join(where_d)
    where_clause_cricsheet = " AND ".join(where_cricsheet)
    
    query = f"""
    WITH combined AS (
        SELECT 
            CASE 
                WHEN c.class_name IN ('T20', 'Twenty20', 'T20I', 'IPL', 'Women T20', 'Women''s T20', 'Other T20', 'Youth T20I', 'ICCT') THEN 'T20'
                WHEN c.class_name IN ('ODI', 'Women''s ODI', 'Youth ODI', 'List A', 'Other OD') THEN 'ODI'
                WHEN c.class_name IN ('Test', 'Women''s Test', 'Youth Test', 'First-class', 'MD') THEN 'Test'
                ELSE c.class_name 
            END as format,
            l.name as league,
            v.full_name as venue
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON c.id = d.competition_id
        LEFT JOIN cricket.event_leagues el ON c.event_id = el.event_id
        LEFT JOIN cricket.leagues l ON el.league_id = l.id
        LEFT JOIN cricket.venues v ON c.venue_id = v.id
        WHERE {where_clause_d}
        
        UNION ALL
        
        SELECT 
            CASE 
                WHEN m.format IN ('T20', 'Twenty20', 'IT20') THEN 'T20'
                WHEN m.format = 'ODI' THEN 'ODI'
                WHEN m.format IN ('Test', 'MD') THEN 'Test'
                ELSE m.format 
            END as format,
            NULL as league,
            NULL as venue
        FROM cricket.cricsheet_deliveries d
        JOIN cricket.cricsheet_matches m ON m.id = d.match_id
        WHERE {where_clause_cricsheet}
    )
    SELECT 
        array_remove(array_agg(DISTINCT format), NULL) as formats,
        array_remove(array_agg(DISTINCT league), NULL) as leagues,
        array_remove(array_agg(DISTINCT venue), NULL) as venues
    FROM combined
    """
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params_d + params_cricsheet)
            res = cur.fetchone()
            
            return jsonify({
                "formats": sorted(res['formats']) if res and res['formats'] else [],
                "leagues": sorted(res['leagues']) if res and res['leagues'] else [],
                "venues": sorted(res['venues']) if res and res['venues'] else [],
                "phases": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"]
            })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
