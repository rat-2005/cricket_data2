"""
data_service.py — Blackbox Data Service

All data-fetching logic lives here. Flask routes call these
clean Python functions and receive dicts/lists. No SQL leaks out.

Deduplication strategy:
  - Cricinfo is the PRIMARY source (deeper telemetry: wagon wheels, pitch maps)
  - Cricsheet SUPPLEMENTS for matches not present in Cricinfo
  - Overlap is eliminated via the materialized cricinfo_match_ids table
  - Player names ↔ numeric IDs mapped via player_lookup table
"""
from db import query, query_one, query_value


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

def _esc(s):
    """Escape single quotes for SQL string literals."""
    if s is None:
        return ""
    return str(s).replace("'", "''")


def _get_player_names(player_id):
    """Get cricsheet names for a player via the player_name_bridge table.

    cricinfo_parquet uses INTERNAL ESPN athlete IDs (e.g. 49752 for Kohli),
    NOT the key_cricinfo URL IDs (253802). The bridge table was built at
    startup by matching first-initial + surname across both datasets.
    """
    info = query_one("SELECT cricinfo_name AS full_name, cricinfo_name AS short_name FROM player_name_bridge WHERE internal_id = ? LIMIT 1", [int(player_id)])
    rows = query("""
        SELECT DISTINCT cricsheet_name
        FROM player_name_bridge
        WHERE internal_id = ?
    """, [int(player_id)])
    
    names = []
    if info.get("full_name"): names.append(info["full_name"])
    if info.get("short_name"): names.append(info["short_name"])

    for r in rows:
        names.append(r["cricsheet_name"])

    # Keep unique names
    names = list(set([n for n in names if n]))

    # Specific fix for Rohit Sharma's false aliases causing extra runs
    if info.get("full_name") and "Rohit Sharma" in info["full_name"]:
        allowed = {"Rohit Sharma", "RG Sharma"}
        names = [n for n in names if n in allowed]
        
    return names


def _names_sql(names):
    """Turn a list of names into a SQL IN(...) value string."""
    if not names:
        return "'__NONE__'"
    return ", ".join([f"'{_esc(n)}'" for n in names])


def _normalize_format(fmt):
    """Normalize format strings to canonical display names.
    
    cricinfo_metadata.format is UPPERCASE: 'TEST', 'T20', 'ODI', 'HUNDRED_BALL'
    """
    if fmt in ("TEST", "Test"):
        return "Test"
    if fmt in ("FIRST_CLASS", "First-class"):
        return "First-Class"
    if fmt in ("ODI",):
        return "ODI"
    if fmt in ("LIST_A", "List A"):
        return "List A"
    if fmt in ("T20I", "IT20"):
        return "T20I"
    if fmt in ("T20", "Twenty20"):
        return "T20"
    if fmt in ("HUNDRED_BALL",):
        return "The Hundred"
    return fmt

def _process_formats(raw_formats):
    """Refine formats for the UI dropdown, separating Internationals and Domestic."""
    if hasattr(raw_formats, "tolist"): raw_formats = raw_formats.tolist()
    formats = set(_normalize_format(f) for f in (raw_formats or []) if f)
    
    if "T20" in formats:
        formats.remove("T20")
        formats.add("T20I")
        
    # User specifically requested only these formats
    allowed = {"ODI", "T20I", "Test"}
    formats = formats.intersection(allowed)
        
    return sorted(list(formats))


def _ci_format_where(fmt, prefix="m"):
    """Cricinfo metadata format filter.
    
    cricinfo_metadata.format uses UPPERCASE values: 'TEST', 'T20', 'ODI', 'HUNDRED_BALL'.
    """
    m = {
        "Test": f"{prefix}.format = 'TEST' AND COALESCE({prefix}.internationalClassId, 0) = 1 AND {prefix}.seriesName NOT ILIKE '%Under-19%'",
        "First-Class": f"({prefix}.format = 'FIRST_CLASS' OR ({prefix}.format = 'TEST' AND (COALESCE({prefix}.internationalClassId, 0) != 1 OR {prefix}.seriesName ILIKE '%Under-19%')))",
        "ODI":  f"{prefix}.format = 'ODI' AND COALESCE({prefix}.internationalClassId, 0) = 2 AND {prefix}.seriesName NOT ILIKE '%Under-19%'",
        "List A": f"({prefix}.format = 'LIST_A' OR ({prefix}.format = 'ODI' AND (COALESCE({prefix}.internationalClassId, 0) != 2 OR {prefix}.seriesName ILIKE '%Under-19%')))",
        "T20I": f"{prefix}.format IN ('T20', 'T20I', 'IT20') AND COALESCE({prefix}.internationalClassId, 0) = 3",
        "T20 Domestic": f"{prefix}.format IN ('T20', 'T20I', 'IT20') AND COALESCE({prefix}.internationalClassId, 0) != 3",
        "T20":  f"{prefix}.format IN ('T20', 'T20I', 'IT20')",
        "IPL":  f"{prefix}.seriesName ILIKE '%Indian Premier League%'",
    }
    return m.get(fmt, f"UPPER({prefix}.format) = UPPER('{_esc(fmt)}')") 


def _cs_format_where(fmt, prefix="cm"):
    """Cricsheet matches format filter."""
    m = {
        "Test": f"{prefix}.match_type = 'Test'",
        "ODI":  f"{prefix}.match_type = 'ODI'",
        "T20I": f"{prefix}.match_type IN ('T20I', 'IT20')",
        "T20 Domestic": f"{prefix}.match_type = 'T20'",
        "T20":  f"{prefix}.match_type IN ('T20', 'T20I', 'IT20')",
    }
    return m.get(fmt, f"{prefix}.match_type = '{_esc(fmt)}'")


def _handle_filter(val, is_not, sql_builder_fn):
    if val == "All" or val == ["All"] or not val:
        return ""
    if not isinstance(val, list):
        val = [val]
    conds = []
    for v in val:
        c = sql_builder_fn(v)
        if c:
            conds.append(f"(NOT ({c}))" if is_not else f"({c})")
    if not conds:
        return ""
    joiner = " AND " if is_not else " OR "
    return f"({joiner.join(conds)})"

def _build_ci_where(filters, player_id_field="cp.batsmanPlayerId"):
    """Build WHERE additions for cricinfo_parquet cp + cricinfo_metadata m."""
    parts = []
    
    cond = _handle_filter(filters.get("format", "All"), filters.get("format_not", False), _ci_format_where)
    if cond: parts.append(cond)
    
    def _phase(p):
        if p == "Final": return "m.title ILIKE '%Final%' AND m.title NOT ILIKE '%Semi%' AND m.title NOT ILIKE '%Quarter%'"
        if p == "Semi-Final": return "m.title ILIKE '%Semi%'"
        if p == "Qualifier": return "m.title ILIKE '%Qualifier%'"
        if p == "Eliminator": return "m.title ILIKE '%Eliminator%'"
        if p == "Group Stage": return "m.title NOT ILIKE '%Final%' AND m.title NOT ILIKE '%Qualifier%' AND m.title NOT ILIKE '%Eliminator%' AND m.title NOT ILIKE '%Semi%' AND m.title NOT ILIKE '%Quarter%'"
        return ""
    cond = _handle_filter(filters.get("phase", "All"), filters.get("phase_not", False), _phase)
    if cond: parts.append(cond)
    
    def _inn(i):
        return f"cp.inningNumber = {i}" if i in ("1", "2", "3", "4") else ""
    cond = _handle_filter(filters.get("innings", "All"), filters.get("innings_not", False), _inn)
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("venue", "All"), filters.get("venue_not", False), lambda v: f"m.groundName = '{_esc(v)}'")
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("opponent", "All"), filters.get("opponent_not", False), lambda o: f"(m.team1Name ILIKE '%{_esc(o)}%' OR m.team2Name ILIKE '%{_esc(o)}%')")
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("year", "All"), filters.get("year_not", False), lambda y: f"EXTRACT(YEAR FROM CAST(m.startDate AS DATE)) = {int(y)}")
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("league", "All"), filters.get("league_not", False), lambda l: f"m.seriesName = '{_esc(l)}'")
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("bowling_type", "All"), filters.get("bowling_type_not", False), lambda b: f"cp.bowlerPlayerId IN (SELECT playerId FROM cricinfo_player_styles WHERE bowlingStyle = '{_esc(b)}')")
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("batting_type", "All"), filters.get("batting_type_not", False), lambda b: f"cp.batsmanPlayerId IN (SELECT playerId FROM cricinfo_player_styles WHERE battingStyle = '{_esc(b)}')")
    if cond: parts.append(cond)

    def _res(r):
        if player_id_field:
            if r == "Won": return f"m.winnerTeamId = (SELECT MAX(teamId) FROM cricinfo_batting WHERE match_id = cp.match_id AND playerId = {player_id_field})"
            if r == "Lost": return f"m.winnerTeamId IS NOT NULL AND m.winnerTeamId != (SELECT MAX(teamId) FROM cricinfo_batting WHERE match_id = cp.match_id AND playerId = {player_id_field})"
        return ""
    cond = _handle_filter(filters.get("result", "All"), filters.get("result_not", False), _res)
    if cond: parts.append(cond)

    def _wkt(w):
        return "(cp.isWicket IS NULL OR cp.isWicket = FALSE)" if w == "Not Out" else f"cp.dismissalType = '{_esc(w)}'"
    cond = _handle_filter(filters.get("wicket_type", "All"), filters.get("wicket_type_not", False), _wkt)
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("pitch_length", "All"), filters.get("pitch_length_not", False), lambda p: f"cp.pitchLength = '{_esc(p)}'")
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("pitch_line", "All"), filters.get("pitch_line_not", False), lambda p: f"cp.pitchLine = '{_esc(p)}'")
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("shot_type", "All"), filters.get("shot_type_not", False), lambda s: f"cp.shotType = '{_esc(s)}'")
    if cond: parts.append(cond)

    return (" AND " + " AND ".join(parts)) if parts else ""


def _build_cs_where(filters, player_id_field=None):
    """Build WHERE additions for cricsheet_deliveries d + cricsheet_matches cm."""
    parts = []
    
    cond = _handle_filter(filters.get("format", "All"), filters.get("format_not", False), _cs_format_where)
    if cond: parts.append(cond)
    
    def _phase(p):
        if p == "Final": return "d.match_id IN (SELECT match_id FROM cricinfo_metadata WHERE title ILIKE '%Final%' AND title NOT ILIKE '%Semi%' AND title NOT ILIKE '%Quarter%')"
        if p == "Semi-Final": return "d.match_id IN (SELECT match_id FROM cricinfo_metadata WHERE title ILIKE '%Semi%')"
        if p == "Qualifier": return "d.match_id IN (SELECT match_id FROM cricinfo_metadata WHERE title ILIKE '%Qualifier%')"
        if p == "Eliminator": return "d.match_id IN (SELECT match_id FROM cricinfo_metadata WHERE title ILIKE '%Eliminator%')"
        if p == "Group Stage": return "d.match_id IN (SELECT match_id FROM cricinfo_metadata WHERE title NOT ILIKE '%Final%' AND title NOT ILIKE '%Qualifier%' AND title NOT ILIKE '%Eliminator%' AND title NOT ILIKE '%Semi%' AND title NOT ILIKE '%Quarter%')"
        return ""
    cond = _handle_filter(filters.get("phase", "All"), filters.get("phase_not", False), _phase)
    if cond: parts.append(cond)

    def _inn(i):
        return f"d.inning = {i}" if i in ("1", "2", "3", "4") else ""
    cond = _handle_filter(filters.get("innings", "All"), filters.get("innings_not", False), _inn)
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("venue", "All"), filters.get("venue_not", False), lambda v: f"cm.venue = '{_esc(v)}'")
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("opponent", "All"), filters.get("opponent_not", False), lambda o: f"(cm.team1 ILIKE '%{_esc(o)}%' OR cm.team2 ILIKE '%{_esc(o)}%')")
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("year", "All"), filters.get("year_not", False), lambda y: f"EXTRACT(YEAR FROM CAST(cm.date AS DATE)) = {int(y)}")
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("league", "All"), filters.get("league_not", False), lambda l: f"d.match_id IN (SELECT match_id FROM cricinfo_metadata WHERE seriesName = '{_esc(l)}')")
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("bowling_type", "All"), filters.get("bowling_type_not", False), lambda b: f"d.bowler IN (SELECT pnb.cricsheet_name FROM player_name_bridge pnb JOIN cricinfo_player_styles cps ON pnb.internal_id = cps.playerId WHERE cps.bowlingStyle = '{_esc(b)}')")
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("batting_type", "All"), filters.get("batting_type_not", False), lambda b: f"d.batter IN (SELECT pnb.cricsheet_name FROM player_name_bridge pnb JOIN cricinfo_player_styles cps ON pnb.internal_id = cps.playerId WHERE cps.battingStyle = '{_esc(b)}')")
    if cond: parts.append(cond)

    def _res(r):
        if player_id_field:
            if r == "Won": return f"d.match_id IN (SELECT match_id FROM cricinfo_metadata WHERE winnerTeamId = (SELECT MAX(teamId) FROM cricinfo_batting WHERE match_id = cricinfo_metadata.match_id AND playerId = {player_id_field}))"
            if r == "Lost": return f"d.match_id IN (SELECT match_id FROM cricinfo_metadata WHERE winnerTeamId IS NOT NULL AND winnerTeamId != (SELECT MAX(teamId) FROM cricinfo_batting WHERE match_id = cricinfo_metadata.match_id AND playerId = {player_id_field}))"
        return ""
    cond = _handle_filter(filters.get("result", "All"), filters.get("result_not", False), _res)
    if cond: parts.append(cond)

    def _wkt(w):
        return "d.dismissal_kind IS NULL" if w == "Not Out" else f"d.dismissal_kind = '{_esc(w)}'"
    cond = _handle_filter(filters.get("wicket_type", "All"), filters.get("wicket_type_not", False), _wkt)
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("pitch_length", "All"), filters.get("pitch_length_not", False), lambda p: "FALSE")
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("pitch_line", "All"), filters.get("pitch_line_not", False), lambda p: "FALSE")
    if cond: parts.append(cond)

    cond = _handle_filter(filters.get("shot_type", "All"), filters.get("shot_type_not", False), lambda s: "FALSE")
    if cond: parts.append(cond)

    return (" AND " + " AND ".join(parts)) if parts else ""


def _build_ci_meta_where(fmt):
    """Simple format filter for dashboard queries on cricinfo_metadata."""
    if fmt == "All":
        return ""
    return "AND " + _ci_format_where(fmt)


# ═══════════════════════════════════════════════════════════════
#  PLAYER SEARCH & INFO
# ═══════════════════════════════════════════════════════════════

def search_players(q, against_batter=None, against_bowler=None, limit=10):
    """Search players by name using cricinfo_batting (internal ESPN athlete IDs).

    Uses internal playerId (e.g. 49752) NOT key_cricinfo (253802) — these are
    two different ESPN ID namespaces. cricinfo_parquet uses internal IDs.
    """
    like_q = f"%{q}%"
    start_q = f"{q}%"

    base_sql = """
        SELECT DISTINCT

            internal_id   AS id,
            cricinfo_name AS full_name,
            cricinfo_name AS short_name
        FROM player_name_bridge
        WHERE cricinfo_name IS NOT NULL
          AND cricinfo_name ILIKE ?
    """

    # Narrow to valid face-off opponents
    if against_batter:
        base_sql += f"""
          AND internal_id IN (
              SELECT DISTINCT bowlerPlayerId FROM cricinfo_parquet
              WHERE batsmanPlayerId = {int(against_batter)}
          )
        """
    elif against_bowler:
        base_sql += f"""
          AND internal_id IN (
              SELECT DISTINCT batsmanPlayerId FROM cricinfo_parquet
              WHERE bowlerPlayerId = {int(against_bowler)}
          )
        """

    base_sql += " ORDER BY CASE WHEN cricinfo_name ILIKE ? THEN 1 ELSE 2 END, cricinfo_name LIMIT ?"

    results = query(base_sql, [like_q, start_q, limit])
    for r in results:
        r["id"] = str(r["id"])
    return results


def get_player_info(player_id):
    """Get player metadata by internal ESPN athlete ID."""
    info = query_one("""
        SELECT DISTINCT
            internal_id AS id,
            cricinfo_name AS full_name,
            cricinfo_name AS short_name
        FROM player_name_bridge
        WHERE internal_id = ?
        LIMIT 1
    """, [int(player_id)])
    if info:
        info["id"] = str(info["id"])
    return info


# ═══════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════

def get_dashboard_data(format_filter="All"):
    """Top batters, bowlers, and aggregate stats for the home page."""
    fw = _build_ci_meta_where(format_filter)

    cw = _build_cs_where({"format": format_filter})

    top_batters = query(f"""
        WITH UnifiedBatters AS (
            SELECT
                b.playerName AS full_name,
                b.runs,
                b.balls,
                b.sixes
            FROM cricinfo_batting b
            JOIN cricinfo_metadata m ON b.match_id = m.match_id
            WHERE b.runs IS NOT NULL {fw}

            UNION ALL

            SELECT
                pb.cricinfo_name AS full_name,
                SUM(d.batter_runs)::INT AS runs,
                COUNT(d.ball)::INT AS balls,
                SUM(CASE WHEN d.batter_runs = 6 THEN 1 ELSE 0 END)::INT AS sixes
            FROM cricsheet_deliveries d
            JOIN player_name_bridge pb ON d.batter = pb.cricsheet_name
            JOIN cricsheet_matches cm ON d.match_id = cm.match_id
            WHERE cm.match_id NOT IN (SELECT match_id FROM cricinfo_metadata) {cw}
            GROUP BY d.match_id, d.inning, pb.cricinfo_name
        )
        SELECT
            full_name,
            NULL AS image_url,
            SUM(runs)::INT AS total_runs,
            SUM(sixes)::INT AS total_sixes,
            ROUND((SUM(runs) / NULLIF(SUM(balls), 0)) * 100, 2) AS strike_rate
        FROM UnifiedBatters
        GROUP BY full_name
        ORDER BY total_runs DESC NULLS LAST
        LIMIT 10
    """)

    top_bowlers = query(f"""
        WITH UnifiedBowlers AS (
            SELECT
                b.playerName AS full_name,
                b.wickets,
                b.conceded,
                b.overs
            FROM cricinfo_bowling b
            JOIN cricinfo_metadata m ON b.match_id = m.match_id
            WHERE b.wickets IS NOT NULL {fw}

            UNION ALL

            SELECT
                pb.cricinfo_name AS full_name,
                SUM(CASE WHEN d.is_wicket AND d.dismissal_kind NOT IN ('run out', 'retired hurt', 'obstructing the field') THEN 1 ELSE 0 END)::INT AS wickets,
                SUM(d.total_runs - COALESCE(d.byes, 0) - COALESCE(d.legbyes, 0))::INT AS conceded,
                (COUNT(CASE WHEN COALESCE(d.wides, 0) = 0 AND COALESCE(d.noballs, 0) = 0 THEN 1 END) / 6.0)::DOUBLE AS overs
            FROM cricsheet_deliveries d
            JOIN player_name_bridge pb ON d.bowler = pb.cricsheet_name
            JOIN cricsheet_matches cm ON d.match_id = cm.match_id
            WHERE cm.match_id NOT IN (SELECT match_id FROM cricinfo_metadata) {cw}
            GROUP BY d.match_id, d.inning, pb.cricinfo_name
        )
        SELECT
            full_name,
            NULL AS image_url,
            SUM(wickets)::INT AS total_wickets,
            SUM(conceded)::INT AS runs_conceded,
            ROUND(SUM(overs), 1) AS overs_bowled,
            CASE WHEN SUM(overs) > 0
                 THEN ROUND(SUM(conceded) / SUM(overs), 2)
                 ELSE 0.0
            END AS economy
        FROM UnifiedBowlers
        GROUP BY full_name
        ORDER BY total_wickets DESC NULLS LAST, economy ASC NULLS LAST
        LIMIT 10
    """)

    stats = query_one(f"""
        SELECT
            (
                (SELECT COUNT(DISTINCT m2.match_id) FROM cricinfo_metadata m2 WHERE 1=1 {fw.replace('m.', 'm2.')}) +
                (SELECT COUNT(DISTINCT cm2.match_id) FROM cricsheet_matches cm2 WHERE cm2.match_id NOT IN (SELECT match_id FROM cricinfo_metadata) {cw.replace('cm.', 'cm2.')})
            )::INT AS total_matches,
            (
                (SELECT COALESCE(SUM(b2.runs), 0) FROM cricinfo_batting b2 JOIN cricinfo_metadata m2 ON b2.match_id = m2.match_id WHERE 1=1 {fw.replace('m.', 'm2.')}) +
                (SELECT COALESCE(SUM(d2.batter_runs), 0) FROM cricsheet_deliveries d2 JOIN cricsheet_matches cm2 ON d2.match_id = cm2.match_id WHERE cm2.match_id NOT IN (SELECT match_id FROM cricinfo_metadata) {cw.replace('cm.', 'cm2.')})
            )::BIGINT AS total_runs,
            (
                (SELECT COALESCE(SUM(b3.wickets), 0) FROM cricinfo_bowling b3 JOIN cricinfo_metadata m3 ON b3.match_id = m3.match_id WHERE 1=1 {fw.replace('m.', 'm3.')}) +
                (SELECT COALESCE(SUM(CASE WHEN d3.is_wicket AND d3.dismissal_kind NOT IN ('run out', 'retired hurt', 'obstructing the field') THEN 1 ELSE 0 END), 0) FROM cricsheet_deliveries d3 JOIN cricsheet_matches cm3 ON d3.match_id = cm3.match_id WHERE cm3.match_id NOT IN (SELECT match_id FROM cricinfo_metadata) {cw.replace('cm.', 'cm3.')})
            )::BIGINT AS total_wickets,
            (
                (SELECT COALESCE(SUM(b4.sixes), 0) FROM cricinfo_batting b4 JOIN cricinfo_metadata m4 ON b4.match_id = m4.match_id WHERE 1=1 {fw.replace('m.', 'm4.')}) +
                (SELECT COALESCE(SUM(CASE WHEN d4.batter_runs = 6 THEN 1 ELSE 0 END), 0) FROM cricsheet_deliveries d4 JOIN cricsheet_matches cm4 ON d4.match_id = cm4.match_id WHERE cm4.match_id NOT IN (SELECT match_id FROM cricinfo_metadata) {cw.replace('cm.', 'cm4.')})
            )::BIGINT AS total_sixes
    """)

    return top_batters, top_bowlers, stats
def _get_pitch_heatmap(player_filter, ci_w):
    raw_rows = query(f"""
        SELECT cp.pitchLength AS length, cp.pitchLine AS line,
               COALESCE(NULLIF(TRIM(cp.shotType), ''), 'Unknown') AS shot,
               SUM(cp.batsmanRuns) AS runs,
               COUNT(*)::INT AS balls,
               CASE WHEN cp.isWicket = TRUE 
                          AND COALESCE(cp.dismissalText,'') NOT ILIKE '%run out%'
                          AND COALESCE(cp.dismissalText,'') NOT ILIKE '%retired%'
                          AND COALESCE(cp.dismissalText,'') NOT ILIKE '%obstructing%' 
                    THEN cp.dismissalText ELSE NULL END AS wicket_type,
               SUM(CASE WHEN cp.isWicket = TRUE 
                          AND COALESCE(cp.dismissalText,'') NOT ILIKE '%run out%'
                          AND COALESCE(cp.dismissalText,'') NOT ILIKE '%retired%'
                          AND COALESCE(cp.dismissalText,'') NOT ILIKE '%obstructing%' 
                        THEN 1 ELSE 0 END)::INT AS wickets
        FROM cricinfo_parquet cp
        JOIN cricinfo_metadata m ON cp.match_id = m.match_id
        WHERE {player_filter}
          AND cp.pitchLength IS NOT NULL AND cp.pitchLine IS NOT NULL
          AND (cp.skipped IS NULL OR cp.skipped = FALSE)
          {ci_w}
        GROUP BY cp.pitchLength, cp.pitchLine, COALESCE(NULLIF(TRIM(cp.shotType), ''), 'Unknown'),
                 CASE WHEN cp.isWicket = TRUE AND COALESCE(cp.dismissalText,'') NOT ILIKE '%run out%' AND COALESCE(cp.dismissalText,'') NOT ILIKE '%retired%' AND COALESCE(cp.dismissalText,'') NOT ILIKE '%obstructing%' THEN cp.dismissalText ELSE NULL END
    """)

    agg = {}
    for r in raw_rows:
        key = (r['length'], r['line'])
        if key not in agg:
            agg[key] = {
                'length': r['length'],
                'line': r['line'],
                'runs': 0,
                'balls': 0,
                'wickets': 0,
                'wickets': 0,
                'shots': {},
                'wicket_events': []
            }
        
        node = agg[key]
        node['runs'] += r['runs'] or 0
        node['balls'] += r['balls'] or 0
        node['wickets'] += r['wickets'] or 0
        
        if r['runs'] and r['runs'] > 0:
            s_name = r['shot']
            node['shots'][s_name] = node['shots'].get(s_name, 0) + r['runs']
            
        if r['wickets'] and r['wickets'] > 0 and r['wicket_type']:
            raw_w_name = r['wicket_type']
            w_name = raw_w_name
            if raw_w_name.startswith('{') and raw_w_name.endswith('}'):
                try:
                    import ast
                    w_dict = ast.literal_eval(raw_w_name)
                    short = w_dict.get('short', '').capitalize()
                    is_batter_page = 'batsmanplayerid' in player_filter.lower() and 'bowlerplayerid' not in player_filter.lower()
                    if is_batter_page:
                        bowler = w_dict.get('bowlerText', '')
                        if bowler:
                            w_name = f"{short} ({bowler})"
                        else:
                            w_name = short
                    else:
                        w_name = short
                except:
                    pass
            
            for _ in range(r['wickets']):
                node['wicket_events'].append({
                    'shot': r['shot'].capitalize() if r['shot'] else 'Unknown',
                    'type': w_name
                })

    return list(agg.values())

def get_batter_stats(player_id, filters):
    """Full batting stats with deduplication + wagon wheel + shot data."""
    pid = int(player_id)
    ci_w = _build_ci_where(filters)
    cs_w = _build_cs_where(filters, player_id_field=str(pid))
    names = _get_player_names(pid)
    ns = _names_sql(names)

    # ── Combined Match-Level Aggregation (Cricinfo + Cricsheet) ──
    # The user rule states: "for every query, write a code in such a way it reads all the data 
    # from both cricksheet and cricinfo and remove the duplicates using match id".
    # By grouping by match_id and taking the GREATEST of runs/balls/sixes between the two sources,
    # we correctly patch matches where Cricinfo drops deliveries with complete data from Cricsheet,
    # and vice versa, without double counting.
    stats = query_one(f"""
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
        ),
        cs_match AS (
            SELECT d.match_id, d.inning AS inningNumber,
                SUM(d.batter_runs) AS runs,
                SUM(CASE WHEN d.wides=0 THEN 1 ELSE 0 END) AS balls,
                SUM(CASE WHEN d.batter_runs>=6 THEN 1 ELSE 0 END) AS sixes,
                SUM(CASE WHEN d.batter_runs=0 AND d.wides=0 THEN 1 ELSE 0 END) AS dots
            FROM cricsheet_deliveries d
            JOIN cricsheet_matches cm ON d.match_id = cm.match_id
            WHERE d.batter IN ({ns})
              {cs_w}
            GROUP BY d.match_id, d.inning
        ),
        combined AS (
            SELECT 
                COALESCE(ci.match_id, cs.match_id) AS match_id,
                COALESCE(ci.inningNumber, cs.inningNumber) AS inningNumber,
                GREATEST(COALESCE(ci.runs, 0), COALESCE(cs.runs, 0)) AS runs,
                GREATEST(COALESCE(ci.balls, 0), COALESCE(cs.balls, 0)) AS balls,
                GREATEST(COALESCE(ci.sixes, 0), COALESCE(cs.sixes, 0)) AS sixes,
                GREATEST(COALESCE(ci.dots, 0), COALESCE(cs.dots, 0)) AS dots
            FROM ci_match ci
            FULL OUTER JOIN cs_match cs ON ci.match_id = cs.match_id AND ci.inningNumber = cs.inningNumber
        )
        SELECT COALESCE(SUM(runs),0)::INT AS runs,
               COALESCE(SUM(balls),0)::INT AS balls,
               COALESCE(SUM(sixes),0)::INT AS sixes,
               COALESCE(MAX(runs),0)::INT  AS hs,
               COALESCE(SUM(dots),0)::INT  AS dots
        FROM combined
    """)

    total_runs  = stats.get("runs") or 0
    total_balls = stats.get("balls") or 0
    total_sixes = stats.get("sixes") or 0
    hs = stats.get("hs") or 0
    dots = stats.get("dots") or 0

    # ── Wagon Wheel (Cricinfo only)
    wagon_wheel = query(f"""
        SELECT cp.wagonX AS x, cp.wagonY AS y, cp.wagonZone AS zone, cp.batsmanRuns AS runs,
               cp.shotType AS shot_type, cp.overNumber AS over, cp.ballNumber AS ball, cp.timestamp AS date,
               COALESCE(pl.cricsheet_name, pl.cricinfo_name, 'Unknown') AS bowler_name, cp.pitchLength AS length, cp.pitchLine AS line
        FROM cricinfo_parquet cp
        JOIN cricinfo_metadata m ON cp.match_id = m.match_id
        LEFT JOIN player_name_bridge pl ON cp.bowlerPlayerId = pl.internal_id
        WHERE cp.batsmanPlayerId = {pid}
          AND cp.wagonX IS NOT NULL AND cp.wagonY IS NOT NULL
          AND (cp.skipped IS NULL OR cp.skipped = FALSE)
          AND COALESCE(cp.wides, 0) = 0 AND COALESCE(cp.legbyes, 0) = 0 AND COALESCE(cp.byes, 0) = 0 AND COALESCE(cp.noballs, 0) = 0
          {ci_w}
    """)

    # ── Shot types (cricinfo only) ──
    shot_rows = query(f"""
        SELECT cp.shotType, COUNT(*)::INT AS cnt
        FROM cricinfo_parquet cp
        JOIN cricinfo_metadata m ON cp.match_id = m.match_id
        WHERE cp.batsmanPlayerId = {pid}
          AND cp.shotType IS NOT NULL AND TRIM(cp.shotType) != ''
          AND (cp.skipped IS NULL OR cp.skipped = FALSE)
          {ci_w}
        GROUP BY cp.shotType
    """)
    shot_data = {r["shotType"].title(): r["cnt"] for r in shot_rows}

    sr = round((total_runs / total_balls * 100), 2) if total_balls > 0 else 0
    dp = round((dots / total_balls * 100), 1) if total_balls > 0 else 0

    heatmap = _get_pitch_heatmap(f"cp.batsmanPlayerId = {pid}", ci_w)

    return {
        "runs": total_runs,
        "balls": total_balls,
        "sr": sr,
        "sixes": total_sixes,
        "hs": hs,
        "dot_pct": dp,
        "wagon_wheel": wagon_wheel,
        "shot_data": shot_data,
        "vuln_data": {},
        "pitch_heatmap": heatmap,
    }


# ═══════════════════════════════════════════════════════════════
#  BOWLER STATS
# ═══════════════════════════════════════════════════════════════

def get_bowler_stats(player_id, filters):
    """Full bowling stats with deduplication."""
    pid = int(player_id)
    ci_w = _build_ci_where(filters, player_id_field="cp.bowlerPlayerId")
    cs_w = _build_cs_where(filters, player_id_field=str(pid))
    names = _get_player_names(pid)
    ns = _names_sql(names)

    stats = query_one(f"""
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
               COALESCE((SELECT wickets FROM combined WHERE wickets > 0 ORDER BY wickets DESC, conceded ASC LIMIT 1),0)::INT AS best_w,
               COALESCE((SELECT conceded FROM combined WHERE wickets > 0 ORDER BY wickets DESC, conceded ASC LIMIT 1),0)::INT AS best_r
        FROM combined
    """)

    w  = stats.get("wickets") or 0
    rc = stats.get("conceded") or 0
    ov = stats.get("overs") or 0
    best_w = stats.get("best_w") or 0
    best_r = stats.get("best_r") or 0

    eco = round((rc / ov), 2) if ov > 0 else 0
    avg = round((rc / w), 2)  if w > 0 else 0
    bb = f"{best_w}/{best_r}" if best_w > 0 else "-"

    heatmap = _get_pitch_heatmap(f"cp.bowlerPlayerId = {pid}", ci_w)

    return {
        "wickets": w,
        "runs": rc,
        "overs": round(ov, 1),
        "avg": avg,
        "eco": eco,
        "best": bb,
        "pitch_heatmap": heatmap,
    }


# ═══════════════════════════════════════════════════════════════
#  FACEOFF (BATTER vs BOWLER)
# ═══════════════════════════════════════════════════════════════

def get_faceoff_stats(batter_id, bowler_id, filters):
    """Head-to-head stats with wagon wheel."""
    bid  = int(batter_id)
    boid = int(bowler_id)
    ci_w = _build_ci_where(filters)
    cs_w = _build_cs_where(filters, player_id_field=str(bid))
    bat_names = _get_player_names(bid)
    bowl_names = _get_player_names(boid)
    bn = _names_sql(bat_names)
    bwn = _names_sql(bowl_names)

    stats = query_one(f"""
        WITH ci_match AS (
            SELECT cp.match_id,
                COALESCE(SUM(cp.batsmanRuns),0)::INT AS runs,
                SUM(CASE WHEN cp.isWicket = TRUE 
                          AND COALESCE(cp.dismissalText,'') NOT ILIKE '%run out%'
                          AND COALESCE(cp.dismissalText,'') NOT ILIKE '%retired%'
                          AND COALESCE(cp.dismissalText,'') NOT ILIKE '%obstructing%'
                         THEN 1 ELSE 0 END)::INT AS dismissals,
                SUM(CASE WHEN cp.batsmanRuns=0 AND COALESCE(cp.wides,0)=0 THEN 1 ELSE 0 END)::INT AS dots,
                SUM(CASE WHEN cp.batsmanRuns>=4 THEN 1 ELSE 0 END)::INT AS boundaries,
                SUM(CASE WHEN cp.batsmanRuns>=6 THEN 1 ELSE 0 END)::INT AS sixes,
                SUM(CASE WHEN COALESCE(cp.wides,0)=0 THEN 1 ELSE 0 END)::INT AS balls
            FROM cricinfo_parquet cp
            JOIN cricinfo_metadata m ON cp.match_id = m.match_id
            WHERE cp.batsmanPlayerId = {bid} AND cp.bowlerPlayerId = {boid}
              AND (cp.skipped IS NULL OR cp.skipped = FALSE)
              AND (cp.empty IS NULL OR cp.empty = FALSE)
              {ci_w}
            GROUP BY cp.match_id
        ),
        cs_match AS (
            SELECT d.match_id,
                COALESCE(SUM(d.batter_runs),0)::INT AS runs,
                SUM(CASE WHEN d.is_wicket THEN 1 ELSE 0 END)::INT AS dismissals,
                SUM(CASE WHEN d.batter_runs=0 AND d.wides=0 THEN 1 ELSE 0 END)::INT AS dots,
                SUM(CASE WHEN d.batter_runs>=4 THEN 1 ELSE 0 END)::INT AS boundaries,
                SUM(CASE WHEN d.batter_runs>=6 THEN 1 ELSE 0 END)::INT AS sixes,
                SUM(CASE WHEN d.wides=0 THEN 1 ELSE 0 END)::INT AS balls
            FROM cricsheet_deliveries d
            JOIN cricsheet_matches cm ON d.match_id = cm.match_id
            WHERE d.batter IN ({bn}) AND d.bowler IN ({bwn})
              {cs_w}
            GROUP BY d.match_id
        ),
        combined AS (
            SELECT 
                COALESCE(ci.match_id, cs.match_id) AS match_id,
                GREATEST(COALESCE(ci.runs, 0), COALESCE(cs.runs, 0)) AS runs,
                GREATEST(COALESCE(ci.dismissals, 0), COALESCE(cs.dismissals, 0)) AS dismissals,
                GREATEST(COALESCE(ci.dots, 0), COALESCE(cs.dots, 0)) AS dots,
                GREATEST(COALESCE(ci.boundaries, 0), COALESCE(cs.boundaries, 0)) AS boundaries,
                GREATEST(COALESCE(ci.sixes, 0), COALESCE(cs.sixes, 0)) AS sixes,
                GREATEST(COALESCE(ci.balls, 0), COALESCE(cs.balls, 0)) AS balls
            FROM ci_match ci
            FULL OUTER JOIN cs_match cs ON ci.match_id = cs.match_id
        )
        SELECT COALESCE(SUM(runs),0)::INT AS runs,
               COALESCE(SUM(dismissals),0)::INT AS dismissals,
               COALESCE(SUM(dots),0)::INT AS dots,
               COALESCE(SUM(boundaries),0)::INT AS boundaries,
               COALESCE(SUM(sixes),0)::INT AS sixes,
               COALESCE(SUM(balls),0)::INT AS balls
        FROM combined
    """)

    runs  = stats.get("runs") or 0
    balls = stats.get("balls") or 0
    dism  = stats.get("dismissals") or 0
    dots  = stats.get("dots") or 0
    bnds  = stats.get("boundaries") or 0
    sxs   = stats.get("sixes") or 0

    # Wagon wheel (cricinfo only)
    wagon_wheel = query(f"""
        SELECT cp.wagonX AS x, cp.wagonY AS y, cp.wagonZone AS zone, cp.batsmanRuns AS runs,
               cp.shotType AS shot_type, cp.overNumber AS over, cp.ballNumber AS ball, cp.timestamp AS date,
               COALESCE(pl.cricsheet_name, pl.cricinfo_name, 'Unknown') AS bowler_name, cp.pitchLength AS length, cp.pitchLine AS line
        FROM cricinfo_parquet cp
        JOIN cricinfo_metadata m ON cp.match_id = m.match_id
        LEFT JOIN player_name_bridge pl ON cp.bowlerPlayerId = pl.internal_id
        WHERE cp.batsmanPlayerId = {bid} AND cp.bowlerPlayerId = {boid}
          AND cp.wagonX IS NOT NULL AND cp.wagonY IS NOT NULL
          AND (cp.skipped IS NULL OR cp.skipped = FALSE)
          AND COALESCE(cp.wides, 0) = 0 AND COALESCE(cp.legbyes, 0) = 0 AND COALESCE(cp.byes, 0) = 0 AND COALESCE(cp.noballs, 0) = 0
          {ci_w}
    """)

    # Shot types (cricinfo only)
    shot_rows = query(f"""
        SELECT cp.shotType, COUNT(*)::INT AS cnt, SUM(CASE WHEN cp.isWicket THEN 1 ELSE 0 END)::INT as dismissals
        FROM cricinfo_parquet cp
        JOIN cricinfo_metadata m ON cp.match_id = m.match_id
        WHERE cp.batsmanPlayerId = {bid} AND cp.bowlerPlayerId = {boid}
          AND cp.shotType IS NOT NULL AND TRIM(cp.shotType) != ''
          AND (cp.skipped IS NULL OR cp.skipped = FALSE)
          {ci_w}
        GROUP BY cp.shotType
    """)
    shot_data = {r["shotType"].title(): r["cnt"] for r in shot_rows}
    vuln_data = {r["shotType"].title(): r["dismissals"] for r in shot_rows if r["dismissals"] > 0}
    fav_shot = max(shot_data, key=shot_data.get) if shot_data else "Unknown"
    dang_shot = max(vuln_data, key=vuln_data.get) if vuln_data else "None"

    heatmap = _get_pitch_heatmap(f"cp.batsmanPlayerId = {bid} AND cp.bowlerPlayerId = {boid}", ci_w)

    return {
        "runs": runs,
        "balls": balls,
        "sr": round((runs / balls * 100), 2) if balls > 0 else 0,
        "dismissals": dism,
        "avg": round((runs / dism), 2) if dism > 0 else (runs if runs > 0 else 0),
        "boundaries": bnds,
        "sixes": sxs,
        "dot_pct": round((dots / balls * 100), 1) if balls > 0 else 0,
        "wagon_wheel": wagon_wheel,
        "shot_data": shot_data,
        "vuln_data": vuln_data,
        "favorite_shot": fav_shot,
        "dangerous_shot": dang_shot,
        "pitch_heatmap": heatmap,
    }


# ═══════════════════════════════════════════════════════════════
#  PLAYER PROFILE (format-wise breakdown)
# ═══════════════════════════════════════════════════════════════

def get_player_profile(player_id):
    """Full player profile with batting & bowling breakdown by format."""
    pid = int(player_id)
    player = get_player_info(pid)
    if not player:
        return None

    # ── Batting by format (Fused with Cricsheet) ──
    batting_raw = query(f"""
        WITH UnifiedBatting AS (
            -- 1. Base Cricinfo Data
            SELECT 
                b.match_id, 
                b.playerId AS internal_id, 
                b.runs, 
                b.balls, 
                b.sixes, 
                m.format, 
                m.generalClassId, 
                m.internationalClassId,
                m.seriesName
            FROM cricinfo_batting b
            JOIN cricinfo_metadata m ON b.match_id = m.match_id
            WHERE b.playerId = {pid} AND b.runs IS NOT NULL

            UNION ALL

            -- 2. Backfill Missing Matches from Cricsheet
            SELECT 
                d.match_id, 
                pb.internal_id, 
                SUM(d.batter_runs)::INT AS runs,
                COUNT(d.ball)::INT AS balls,
                SUM(CASE WHEN d.batter_runs = 6 THEN 1 ELSE 0 END)::INT AS sixes,
                UPPER(cm.match_type) AS format,
                NULL AS generalClassId,
                NULL AS internationalClassId,
                '' AS seriesName
            FROM cricsheet_deliveries d
            JOIN player_name_bridge pb ON d.batter = pb.cricsheet_name
            JOIN cricsheet_matches cm ON d.match_id = cm.match_id
            WHERE pb.internal_id = {pid} 
              AND cm.match_id NOT IN (SELECT match_id FROM cricinfo_metadata)
            GROUP BY d.match_id, d.inning, pb.internal_id, cm.match_type
        )
        SELECT 
            CASE 
                WHEN format = 'TEST' AND (internationalClassId IS NULL OR internationalClassId != 1) AND generalClassId IS NOT NULL THEN 'FIRST_CLASS'
                WHEN format = 'ODI' AND (internationalClassId IS NULL OR internationalClassId != 2) AND generalClassId IS NOT NULL THEN 'LIST_A'
                WHEN format = 'MDM' THEN 'LIST_A'
                WHEN format IN ('T20', 'T20I', 'IT20') AND internationalClassId = 3 THEN 'T20I'
                WHEN format = 'IT20' AND internationalClassId IS NULL THEN 'T20I'
                WHEN format IN ('T20', 'T20I', 'IT20') THEN 'T20_DOMESTIC'
                ELSE format 
            END AS matched_format,
            SUM(runs)::INT  AS total_runs,
            SUM(balls)::INT AS balls_faced,
            SUM(sixes)::INT AS total_sixes,
            MAX(runs)::INT  AS highest_score
        FROM UnifiedBatting
        GROUP BY 1
    """)

    allowed_formats = ['Test', 'ODI', 'T20I']

    batting_stats = {}
    for row in batting_raw:
        fmt = _normalize_format(row["matched_format"] or "Unknown")
        if fmt == "T20i":
            fmt = "T20I"
        if fmt not in allowed_formats:
            continue

        runs  = row["total_runs"] or 0
        balls = row["balls_faced"] or 0
        if fmt not in batting_stats:
            batting_stats[fmt] = {"runs": 0, "balls": 0, "sr": 0,
                                  "sixes": 0, "hs": 0, "dot_pct": 0}
        batting_stats[fmt]["runs"]  += runs
        batting_stats[fmt]["balls"] += balls
        batting_stats[fmt]["sixes"] += row["total_sixes"] or 0
        batting_stats[fmt]["hs"] = max(batting_stats[fmt]["hs"],
                                       row["highest_score"] or 0)
        b = batting_stats[fmt]["balls"]
        batting_stats[fmt]["sr"] = round(
            (batting_stats[fmt]["runs"] / b * 100), 2
        ) if b > 0 else 0


    # ── Bowling by format (Fused with Cricsheet) ──
    bowling_raw = query(f"""
        WITH UnifiedBowling AS (
            -- 1. Base Cricinfo Data
            SELECT 
                b.match_id,
                b.playerId AS internal_id,
                b.wickets,
                b.conceded,
                b.overs,
                m.format,
                m.generalClassId,
                m.internationalClassId,
                m.seriesName
            FROM cricinfo_bowling b
            JOIN cricinfo_metadata m ON b.match_id = m.match_id
            WHERE b.playerId = {pid}

            UNION ALL

            -- 2. Backfill Missing Matches from Cricsheet
            SELECT 
                d.match_id,
                pb.internal_id,
                SUM(CASE WHEN d.is_wicket AND d.dismissal_kind NOT IN ('run out', 'retired hurt', 'obstructing the field') THEN 1 ELSE 0 END)::INT AS wickets,
                SUM(d.total_runs - COALESCE(d.byes, 0) - COALESCE(d.legbyes, 0))::INT AS conceded,
                (COUNT(CASE WHEN COALESCE(d.wides, 0) = 0 AND COALESCE(d.noballs, 0) = 0 THEN 1 END) / 6.0)::DOUBLE AS overs,
                UPPER(cm.match_type) AS format,
                NULL AS generalClassId,
                NULL AS internationalClassId,
                '' AS seriesName
            FROM cricsheet_deliveries d
            JOIN player_name_bridge pb ON d.bowler = pb.cricsheet_name
            JOIN cricsheet_matches cm ON d.match_id = cm.match_id
            WHERE pb.internal_id = {pid}
              AND cm.match_id NOT IN (SELECT match_id FROM cricinfo_metadata)
            GROUP BY d.match_id, d.inning, pb.internal_id, cm.match_type
        )
        SELECT 
            CASE 
                WHEN format = 'TEST' AND (internationalClassId IS NULL OR internationalClassId != 1) AND generalClassId IS NOT NULL THEN 'FIRST_CLASS'
                WHEN format = 'ODI' AND (internationalClassId IS NULL OR internationalClassId != 2) AND generalClassId IS NOT NULL THEN 'LIST_A'
                WHEN format = 'MDM' THEN 'LIST_A'
                WHEN format IN ('T20', 'T20I', 'IT20') AND internationalClassId = 3 THEN 'T20I'
                WHEN format = 'IT20' AND internationalClassId IS NULL THEN 'T20I'
                WHEN format IN ('T20', 'T20I', 'IT20') THEN 'T20_DOMESTIC'
                ELSE format 
            END AS matched_format,
            SUM(wickets)::INT  AS total_wickets,
            SUM(conceded)::INT AS runs_conceded,
            SUM(overs)::DOUBLE AS overs_bowled
        FROM UnifiedBowling
        GROUP BY 1
    """)

    bowling_stats = {}
    for row in bowling_raw:
        fmt = _normalize_format(row["matched_format"] or "Unknown")
        if fmt == "T20i":
            fmt = "T20I"
        if fmt not in allowed_formats:
            continue

        w  = row["total_wickets"] or 0
        rc = row["runs_conceded"] or 0
        ov = float(row["overs_bowled"] or 0)
        if fmt not in bowling_stats:
            bowling_stats[fmt] = {"wickets": 0, "runs": 0, "overs": 0,
                                  "econ": 0, "bb": "-"}
        bowling_stats[fmt]["wickets"] += w
        bowling_stats[fmt]["runs"]    += rc
        bowling_stats[fmt]["overs"]   += ov
        o = bowling_stats[fmt]["overs"]
        bowling_stats[fmt]["econ"] = round(
            (bowling_stats[fmt]["runs"] / o), 2
        ) if o > 0 else 0

    return {
        "athlete": {
            "id": str(pid),
            "full_name": player["full_name"],
            "short_name": player.get("short_name"),
            "image_url": None,
        },
        "batting": batting_stats,
        "bowling": bowling_stats,
    }


# ═══════════════════════════════════════════════════════════════
#  FILTERS
# ═══════════════════════════════════════════════════════════════

def get_global_filters():
    """Static filter options for the filters dropdown."""
    return {
        "formats": ["ODI", "T20I", "Test"],
        "leagues": [],
        "phases": ["Final", "Semi-Final", "Qualifier", "Eliminator", "Group Stage"],
        "venues": [],
        "opponents": [],
        "wicket_types": [],
        "pitch_lengths": [],
        "pitch_lines": [],
        "shot_types": [],
    }


def get_batter_filters(player_id, filters):
    """Available filter values for a specific batter."""
    pid = int(player_id)
    ci_w = _build_ci_where(filters)
    cs_w = _build_cs_where(filters, player_id_field=str(pid))

    names = _get_player_names(pid)
    ns = _names_sql(names)

    res = query_one(f"""
        WITH ci_data AS (
            SELECT m.format, m.groundName AS venue, m.seriesName AS league,
                   EXTRACT(YEAR FROM CAST(m.startDate AS DATE))::INT AS year,
                   m.team1Name AS t1, m.team2Name AS t2,
                   cp.bowlerPlayerId,
                   m.winnerTeamId,
                   (SELECT MAX(teamId) FROM cricinfo_batting WHERE match_id = cp.match_id AND playerId = {pid}) as my_team,
                   cp.inningNumber as innings,
                   m.title,
                   cp.dismissalType,
                   cp.isWicket,
                   cp.pitchLength,
                   cp.pitchLine,
                   cp.shotType
            FROM cricinfo_parquet cp
            JOIN cricinfo_metadata m ON cp.match_id = m.match_id
            WHERE cp.batsmanPlayerId = {pid}
              AND (cp.skipped IS NULL OR cp.skipped = FALSE)
              {ci_w}
        ),
        cs_data AS (
            SELECT cm.match_type AS format, cm.venue, NULL AS league,
                   EXTRACT(YEAR FROM CAST(cm.date AS DATE))::INT AS year,
                   cm.team1 AS t1, cm.team2 AS t2,
                   NULL AS title,
                   d.dismissal_kind AS dismissalType,
                   CASE WHEN d.dismissal_kind IS NOT NULL THEN TRUE ELSE FALSE END AS isWicket,
                   NULL AS pitchLength,
                   NULL AS pitchLine,
                   NULL AS shotType
            FROM cricsheet_deliveries d
            JOIN cricsheet_matches cm ON d.match_id = cm.match_id
            WHERE d.batter IN ({ns})
              AND d.match_id NOT IN (SELECT match_id FROM cricinfo_match_ids)
              {cs_w}
        )
        SELECT
            (SELECT LIST(DISTINCT format) FROM (SELECT format FROM ci_data UNION SELECT format FROM cs_data)) AS formats,
            (SELECT LIST(DISTINCT venue) FROM (SELECT venue FROM ci_data UNION SELECT venue FROM cs_data)) AS venues,
            (SELECT LIST(DISTINCT league) FROM ci_data WHERE league IS NOT NULL) AS leagues,
            (SELECT LIST(DISTINCT year) FROM (SELECT year FROM ci_data UNION SELECT year FROM cs_data)) AS years,
            (SELECT LIST(DISTINCT t) FROM (SELECT t1 AS t FROM ci_data UNION SELECT t2 AS t FROM ci_data UNION SELECT t1 AS t FROM cs_data UNION SELECT t2 AS t FROM cs_data)) AS opponents,
            (SELECT LIST(DISTINCT a.bowlingStyle) FROM ci_data cd JOIN cricinfo_player_styles a ON cd.bowlerPlayerId = a.playerId WHERE a.bowlingStyle IS NOT NULL) AS bowling_types,
            (SELECT LIST(DISTINCT CASE WHEN winnerTeamId = my_team THEN 'Won' WHEN winnerTeamId IS NOT NULL AND winnerTeamId != my_team THEN 'Lost' ELSE NULL END) FROM ci_data) AS results,
            (SELECT LIST(DISTINCT CAST(innings AS VARCHAR)) FROM ci_data) AS innings_list,
            (SELECT LIST(DISTINCT CASE 
                    WHEN title ILIKE '%Final%' AND title NOT ILIKE '%Semi%' AND title NOT ILIKE '%Quarter%' THEN 'Final'
                    WHEN title ILIKE '%Semi%' THEN 'Semi-Final'
                    WHEN title ILIKE '%Qualifier%' THEN 'Qualifier'
                    WHEN title ILIKE '%Eliminator%' THEN 'Eliminator'
                    ELSE 'Group Stage' 
                END) FROM ci_data WHERE title IS NOT NULL) AS phases,
            (SELECT LIST(DISTINCT CASE WHEN isWicket = TRUE THEN CAST(dismissalType AS VARCHAR) ELSE 'Not Out' END) FROM (SELECT isWicket, dismissalType FROM ci_data UNION ALL SELECT isWicket, dismissalType FROM cs_data)) AS wicket_types,
            (SELECT LIST(DISTINCT pitchLength) FROM ci_data WHERE pitchLength IS NOT NULL) AS pitch_lengths,
            (SELECT LIST(DISTINCT pitchLine) FROM ci_data WHERE pitchLine IS NOT NULL) AS pitch_lines,
            (SELECT LIST(DISTINCT shotType) FROM ci_data WHERE shotType IS NOT NULL) AS shot_types
    """)

    formats = _process_formats(res.get("formats"))

    def _extract_list(k):
        v = res.get(k)
        if hasattr(v, "tolist"): return v.tolist()
        return v or []

    venues = sorted(v for v in _extract_list("venues") if v)
    leagues = sorted(l for l in _extract_list("leagues") if l)
    years = sorted((y for y in _extract_list("years") if y), reverse=True)
    opp1, opp2 = _extract_list("opp1"), _extract_list("opp2") # wait, batter uses t!
    # batter uses opponents from SQL
    opponents = sorted(list(set(o for o in _extract_list("opponents") if o)))
    bowling_types = sorted(b for b in _extract_list("bowling_types") if b)
    results = sorted(r for r in _extract_list("results") if r)
    innings_list = sorted(i for i in _extract_list("innings_list") if i)
    
    valid_phases = set(p for p in _extract_list("phases") if p)
    all_phases = ["Final", "Semi-Final", "Qualifier", "Eliminator", "Group Stage"]
    phases = [p for p in all_phases if p in valid_phases]

    wicket_types = sorted(w for w in _extract_list("wicket_types") if w)
    pitch_lengths = sorted(p for p in _extract_list("pitch_lengths") if p)
    pitch_lines = sorted(p for p in _extract_list("pitch_lines") if p)
    shot_types = sorted(s for s in _extract_list("shot_types") if s)

    return {
        "formats": formats,
        "leagues": leagues,
        "venues": venues,
        "years": years,
        "opponents": opponents,
        "phases": phases,
        "bowling_types": bowling_types,
        "results": results,
        "innings": innings_list,
        "wicket_types": wicket_types,
        "pitch_lengths": pitch_lengths,
        "pitch_lines": pitch_lines,
        "shot_types": shot_types,
    }


def get_bowler_filters(player_id, filters):
    """Available filter values for a specific bowler."""
    pid = int(player_id)
    ci_w = _build_ci_where(filters, player_id_field="cp.bowlerPlayerId")
    cs_w = _build_cs_where(filters, player_id_field=str(pid))

    names = _get_player_names(pid)
    ns = _names_sql(names)

    res = query_one(f"""
        WITH ci_data AS (
            SELECT m.format, m.groundName AS venue, m.seriesName AS league, 
                   EXTRACT(YEAR FROM CAST(m.startDate AS DATE))::INT AS year,
                   m.team1Name AS t1, m.team2Name AS t2, m.title,
                   cp.batsmanPlayerId,
                   m.winnerTeamId,
                   (SELECT MAX(teamId) FROM cricinfo_batting WHERE match_id = cp.match_id AND playerId = {pid}) as my_team,
                   cp.inningNumber as innings,
                   cp.dismissalType,
                   cp.isWicket,
                   cp.pitchLength,
                   cp.pitchLine,
                   cp.shotType
            FROM cricinfo_parquet cp
            JOIN cricinfo_metadata m ON cp.match_id = m.match_id
            WHERE cp.bowlerPlayerId = {pid}
              AND (cp.skipped IS NULL OR cp.skipped = FALSE)
              {ci_w}
        ),
        cs_data AS (
            SELECT cm.match_type AS format, cm.venue, NULL AS league, 
                   EXTRACT(YEAR FROM CAST(cm.date AS DATE))::INT AS year,
                   cm.team1 AS t1, cm.team2 AS t2, NULL AS title,
                   NULL AS batsmanPlayerId,
                   NULL AS winnerTeamId,
                   NULL AS my_team,
                   d.inning as innings,
                   d.dismissal_kind AS dismissalType,
                   CASE WHEN d.dismissal_kind IS NOT NULL THEN TRUE ELSE FALSE END AS isWicket,
                   NULL AS pitchLength,
                   NULL AS pitchLine,
                   NULL AS shotType
            FROM cricsheet_deliveries d
            JOIN cricsheet_matches cm ON d.match_id = cm.match_id
            WHERE d.bowler IN ({ns})
              AND d.match_id NOT IN (SELECT match_id FROM cricinfo_match_ids)
              {cs_w}
        )
        SELECT 
            (SELECT LIST(DISTINCT format) FROM (SELECT format FROM ci_data UNION SELECT format FROM cs_data)) AS formats,
            (SELECT LIST(DISTINCT venue) FROM (SELECT venue FROM ci_data UNION SELECT venue FROM cs_data)) AS venues,
            (SELECT LIST(DISTINCT league) FROM ci_data WHERE league IS NOT NULL) AS leagues,
            (SELECT LIST(DISTINCT year) FROM (SELECT year FROM ci_data UNION SELECT year FROM cs_data)) AS years,
            (SELECT LIST(DISTINCT t) FROM (SELECT t1 AS t FROM ci_data UNION SELECT t2 AS t FROM ci_data UNION SELECT t1 AS t FROM cs_data UNION SELECT t2 AS t FROM cs_data)) AS opponents,
            (SELECT LIST(DISTINCT a.battingStyle) FROM ci_data cd JOIN cricinfo_player_styles a ON cd.batsmanPlayerId = a.playerId WHERE a.battingStyle IS NOT NULL) AS batting_types,
            (SELECT LIST(DISTINCT CASE WHEN winnerTeamId = my_team THEN 'Won' WHEN winnerTeamId IS NOT NULL AND winnerTeamId != my_team THEN 'Lost' ELSE NULL END) FROM ci_data) AS results,
            (SELECT LIST(DISTINCT CAST(innings AS VARCHAR)) FROM ci_data) AS innings_list,
            (SELECT LIST(DISTINCT CASE 
                    WHEN title ILIKE '%Final%' AND title NOT ILIKE '%Semi%' AND title NOT ILIKE '%Quarter%' THEN 'Final'
                    WHEN title ILIKE '%Semi%' THEN 'Semi-Final'
                    WHEN title ILIKE '%Qualifier%' THEN 'Qualifier'
                    WHEN title ILIKE '%Eliminator%' THEN 'Eliminator'
                    ELSE 'Group Stage' 
                END) FROM ci_data WHERE title IS NOT NULL) AS phases,
            (SELECT LIST(DISTINCT CASE WHEN isWicket = TRUE THEN CAST(dismissalType AS VARCHAR) ELSE 'Not Out' END) FROM (SELECT isWicket, dismissalType FROM ci_data UNION ALL SELECT isWicket, dismissalType FROM cs_data)) AS wicket_types,
            (SELECT LIST(DISTINCT pitchLength) FROM ci_data WHERE pitchLength IS NOT NULL) AS pitch_lengths,
            (SELECT LIST(DISTINCT pitchLine) FROM ci_data WHERE pitchLine IS NOT NULL) AS pitch_lines,
            (SELECT LIST(DISTINCT shotType) FROM ci_data WHERE shotType IS NOT NULL) AS shot_types
    """)

    formats = _process_formats(res.get("formats"))

    def _extract_list(k):
        v = res.get(k)
        if hasattr(v, "tolist"): return v.tolist()
        return v or []

    venues = sorted(v for v in _extract_list("venues") if v)
    leagues = sorted(l for l in _extract_list("leagues") if l)
    years = sorted((y for y in _extract_list("years") if y), reverse=True)
    opponents = sorted(list(set(o for o in _extract_list("opponents") if o)))
    batting_types = sorted(b for b in _extract_list("batting_types") if b)
    results = sorted(r for r in _extract_list("results") if r)
    innings_list = sorted(i for i in _extract_list("innings_list") if i)
    
    valid_phases = set(p for p in _extract_list("phases") if p)
    all_phases = ["Final", "Semi-Final", "Qualifier", "Eliminator", "Group Stage"]
    phases = [p for p in all_phases if p in valid_phases]

    wicket_types = sorted(w for w in _extract_list("wicket_types") if w)
    pitch_lengths = sorted(p for p in _extract_list("pitch_lengths") if p)
    pitch_lines = sorted(p for p in _extract_list("pitch_lines") if p)
    shot_types = sorted(s for s in _extract_list("shot_types") if s)

    return {
        "formats": formats,
        "leagues": leagues,
        "venues": venues,
        "years": years,
        "opponents": opponents,
        "phases": phases,
        "batting_types": batting_types,
        "results": results,
        "innings": innings_list,
        "wicket_types": wicket_types,
        "pitch_lengths": pitch_lengths,
        "pitch_lines": pitch_lines,
        "shot_types": shot_types,
    }


def get_faceoff_filters(batter_id, bowler_id, filters):
    """Available filter values for a batter-bowler faceoff."""
    bid  = int(batter_id)
    boid = int(bowler_id)
    ci_w = _build_ci_where(filters)
    cs_w = _build_cs_where(filters, player_id_field=str(bid))

    bat_names = _get_player_names(bid)
    bowl_names = _get_player_names(boid)
    bn = _names_sql(bat_names)
    bwn = _names_sql(bowl_names)

    res = query_one(f"""
        WITH ci_data AS (
            SELECT m.format, m.groundName AS venue, m.seriesName AS league, 
                   EXTRACT(YEAR FROM CAST(m.startDate AS DATE))::INT AS year,
                   m.team1Name AS t1, m.team2Name AS t2, m.title,
                   m.winnerTeamId,
                   (SELECT MAX(teamId) FROM cricinfo_batting WHERE match_id = cp.match_id AND playerId = {bid}) as my_team,
                   cp.inningNumber as innings,
                   cp.dismissalType,
                   cp.isWicket,
                   cp.pitchLength,
                   cp.pitchLine,
                   cp.shotType
            FROM cricinfo_parquet cp
            JOIN cricinfo_metadata m ON cp.match_id = m.match_id
            WHERE cp.batsmanPlayerId = {bid} AND cp.bowlerPlayerId = {boid}
              AND (cp.skipped IS NULL OR cp.skipped = FALSE)
              {ci_w}
        ),
        cs_data AS (
            SELECT cm.match_type AS format, cm.venue, NULL AS league, 
                   EXTRACT(YEAR FROM CAST(cm.date AS DATE))::INT AS year,
                   cm.team1 AS t1, cm.team2 AS t2, NULL AS title,
                   NULL AS winnerTeamId,
                   NULL AS my_team,
                   d.inning as innings,
                   d.dismissal_kind AS dismissalType,
                   CASE WHEN d.dismissal_kind IS NOT NULL THEN TRUE ELSE FALSE END AS isWicket,
                   NULL AS pitchLength,
                   NULL AS pitchLine,
                   NULL AS shotType
            FROM cricsheet_deliveries d
            JOIN cricsheet_matches cm ON d.match_id = cm.match_id
            WHERE d.batter IN ({bn}) AND d.bowler IN ({bwn})
              AND d.match_id NOT IN (SELECT match_id FROM cricinfo_match_ids)
              {cs_w}
        )
        SELECT 
            (SELECT LIST(DISTINCT format) FROM (SELECT format FROM ci_data UNION SELECT format FROM cs_data)) AS formats,
            (SELECT LIST(DISTINCT venue) FROM (SELECT venue FROM ci_data UNION SELECT venue FROM cs_data)) AS venues,
            (SELECT LIST(DISTINCT league) FROM ci_data WHERE league IS NOT NULL) AS leagues,
            (SELECT LIST(DISTINCT year) FROM (SELECT year FROM ci_data UNION SELECT year FROM cs_data)) AS years,
            (SELECT LIST(DISTINCT t) FROM (SELECT t1 AS t FROM ci_data UNION SELECT t2 AS t FROM ci_data UNION SELECT t1 AS t FROM cs_data UNION SELECT t2 AS t FROM cs_data)) AS opponents,
            (SELECT LIST(DISTINCT CASE WHEN winnerTeamId = my_team THEN 'Won' WHEN winnerTeamId IS NOT NULL AND winnerTeamId != my_team THEN 'Lost' ELSE NULL END) FROM ci_data) AS results,
            (SELECT LIST(DISTINCT CAST(innings AS VARCHAR)) FROM ci_data) AS innings_list,
            (SELECT LIST(DISTINCT CASE 
                    WHEN title ILIKE '%Final%' AND title NOT ILIKE '%Semi%' AND title NOT ILIKE '%Quarter%' THEN 'Final'
                    WHEN title ILIKE '%Semi%' THEN 'Semi-Final'
                    WHEN title ILIKE '%Qualifier%' THEN 'Qualifier'
                    WHEN title ILIKE '%Eliminator%' THEN 'Eliminator'
                    ELSE 'Group Stage' 
                END) FROM ci_data WHERE title IS NOT NULL) AS phases,
            (SELECT LIST(DISTINCT CASE WHEN isWicket = TRUE THEN CAST(dismissalType AS VARCHAR) ELSE 'Not Out' END) FROM (SELECT isWicket, dismissalType FROM ci_data UNION ALL SELECT isWicket, dismissalType FROM cs_data)) AS wicket_types,
            (SELECT LIST(DISTINCT pitchLength) FROM ci_data WHERE pitchLength IS NOT NULL) AS pitch_lengths,
            (SELECT LIST(DISTINCT pitchLine) FROM ci_data WHERE pitchLine IS NOT NULL) AS pitch_lines,
            (SELECT LIST(DISTINCT shotType) FROM ci_data WHERE shotType IS NOT NULL) AS shot_types
    """)

    formats = _process_formats(res.get("formats"))

    def _extract_list(k):
        v = res.get(k)
        if hasattr(v, "tolist"): return v.tolist()
        return v or []

    venues = sorted(v for v in _extract_list("venues") if v)
    leagues = sorted(l for l in _extract_list("leagues") if l)
    years = sorted((y for y in _extract_list("years") if y), reverse=True)
    opponents = sorted(list(set(o for o in _extract_list("opponents") if o)))
    results = sorted(r for r in _extract_list("results") if r)
    innings_list = sorted(i for i in _extract_list("innings_list") if i)
    
    valid_phases = set(p for p in _extract_list("phases") if p)
    all_phases = ["Final", "Semi-Final", "Qualifier", "Eliminator", "Group Stage"]
    phases = [p for p in all_phases if p in valid_phases]

    wicket_types = sorted(w for w in _extract_list("wicket_types") if w)
    pitch_lengths = sorted(p for p in _extract_list("pitch_lengths") if p)
    pitch_lines = sorted(p for p in _extract_list("pitch_lines") if p)
    shot_types = sorted(s for s in _extract_list("shot_types") if s)

    return {
        "formats": formats,
        "leagues": leagues,
        "venues": venues,
        "years": years,
        "opponents": opponents,
        "phases": phases,
        "results": results,
        "innings": innings_list,
        "wicket_types": wicket_types,
        "pitch_lengths": pitch_lengths,
        "pitch_lines": pitch_lines,
        "shot_types": shot_types,
    }
