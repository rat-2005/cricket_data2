import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# I will write a function to dynamically inject chart logic into stats_batter before the jsonify return

chart_logic = """
        # --- NEW CHART LOGIC using unified_deliveries ---
        # We build a separate query for charts from unified_deliveries to take advantage of 'zad' for ICC matches.
        
        where_u = ["u.batsman_id = %s"]
        params_u = [athlete_id]
        
        if fmt != 'All':
            where_u.append("u.format = %s")
            params_u.append(fmt)
            
        if league != 'All':
            if league == 'Internationals':
                where_u.append("(u.tournament NOT ILIKE '%%world cup%%' AND u.tournament NOT ILIKE '%%world twenty20%%' AND u.tournament NOT ILIKE '%%t20 world cup%%' AND u.tournament NOT ILIKE '%%championship%%' AND u.tournament NOT ILIKE '%%asia cup%%' AND u.tournament NOT ILIKE '%%champions trophy%%' AND u.tournament NOT ILIKE '%%premier league%%' AND u.tournament NOT ILIKE '%%ipl%%' OR u.tournament IS NULL)")
            elif league == 'World Cup':
                where_u.append("(u.tournament ILIKE '%%world cup%%' OR u.tournament ILIKE '%%world twenty20%%' OR u.tournament ILIKE '%%t20 world cup%%' OR u.tournament ILIKE '%%championship%%')")
            elif league == 'Asia Cup':
                where_u.append("u.tournament ILIKE '%%asia cup%%'")
            elif league == 'Champions Trophy':
                where_u.append("u.tournament ILIKE '%%champions trophy%%'")
            elif league == 'IPL':
                where_u.append("(u.tournament ILIKE '%%premier league%%' OR u.tournament ILIKE '%%ipl%%')")
                
        if venue != 'All':
            where_u.append("u.venue = %s")
            params_u.append(venue)
            
        if phase != 'All':
            if phase == 'Powerplay':
                where_u.append("u.over_number <= 6")
            elif phase == 'Middle':
                where_u.append("u.over_number > 6 AND u.over_number <= 15")
            elif phase == 'Death':
                where_u.append("u.over_number > 15")
                
        if opponent != 'All':
            where_u.append(f"u.bowling_team_id IN (SELECT id FROM cricket.teams WHERE name ILIKE '%%{opponent}%%' OR abbreviation ILIKE '%%{opponent}%%')")
            
        if bowling_type != 'All':
            where_u.append(f"u.bowler_id IN (SELECT id FROM cricket.athletes WHERE bowling_style ILIKE '%%{bowling_type}%%')")
            
        if year != 'All':
            where_u.append("EXTRACT(YEAR FROM u.match_date::date) = %s")
            params_u.append(int(year))
            
        if innings != 'All':
            where_u.append("u.period = %s")
            if innings == '1st Innings': params_u.append(1)
            elif innings == '2nd Innings': params_u.append(2)
            elif innings == '3rd Innings': params_u.append(3)
            elif innings == '4th Innings': params_u.append(4)
            
        recent_limit_u = ""
        if recent == 'Last 5 Matches': recent_limit_u = 'ORDER BY match_date DESC LIMIT 5'
        elif recent == 'Last 10 Matches': recent_limit_u = 'ORDER BY match_date DESC LIMIT 10'
        elif recent == 'Last 20 Matches': recent_limit_u = 'ORDER BY match_date DESC LIMIT 20'
        elif recent == 'Last 50 Matches': recent_limit_u = 'ORDER BY match_date DESC LIMIT 50'
        
        # We need to filter match IDs if recent is used.
        match_filter_u = ""
        if recent_limit_u:
            match_filter_u = f"AND u.match_id IN (SELECT match_id FROM (SELECT match_id, MAX(match_date) as match_date FROM cricket.unified_deliveries u2 WHERE {' AND '.join([w.replace('u.', 'u2.') for w in where_u])} GROUP BY match_id {recent_limit_u}) as sub)"
        
        where_clause_u = " AND ".join(where_u)
        
        chart_query = f\"\"\"
            SELECT 
                u.x_coordinate, 
                u.y_coordinate, 
                u.zad, 
                u.batsman_runs,
                u.shot_type,
                a.bowling_style,
                u.is_wicket,
                u.dismissal_type
            FROM cricket.unified_deliveries u
            LEFT JOIN cricket.athletes a ON u.bowler_id = a.id
            WHERE {where_clause_u} {match_filter_u}
        \"\"\"
        
        cur.execute(chart_query, tuple(params_u * 2 if recent_limit_u else params_u))
        chart_rows = cur.fetchall()
        
        import math
        wagon_wheel = []
        shot_data = {}
        vuln_data = {}
        
        for r in chart_rows:
            x_coord = r['x_coordinate']
            y_coord = r['y_coordinate']
            zad = r['zad']
            b_runs = r['batsman_runs']
            shot = r['shot_type']
            bowling_style = r['bowling_style']
            is_wkt = r['is_wicket']
            dismissal = r['dismissal_type']
            
            # 1. Wagon Wheel Coordinates
            if x_coord is not None and y_coord is not None:
                wagon_wheel.append({"x": x_coord, "y": y_coord, "runs": b_runs})
            elif zad and zad.strip():
                parts = zad.split(',')
                if len(parts) >= 2:
                    try:
                        angle = int(parts[1])
                        dist = int(parts[2]) if len(parts) >= 3 else 3
                        # Normalized r (-1 to 1) based on dist (1 to 6)
                        # The canvas draws from center. Maximum radius is 1.0. 
                        # dist=6 implies boundary (1.0). dist=1 implies close to pitch (0.16)
                        rad = math.radians(angle)
                        r_norm = dist / 6.0
                        
                        # Correct polar translation logic:
                        x = -r_norm * math.sin(rad)
                        y = -r_norm * math.cos(rad)
                        
                        wagon_wheel.append({"x": x, "y": y, "runs": b_runs})
                    except:
                        pass
                        
            # 2. Shot Mastery
            if shot and shot.strip():
                # Clean up shot name if needed
                shot_name = shot.title()
                shot_data[shot_name] = shot_data.get(shot_name, 0) + 1
                
            # 3. Vulnerability (Dismissals by Bowling Style)
            if is_wkt and dismissal and dismissal.lower() != 'run out':
                style = bowling_style if bowling_style else "Unknown"
                style = style.title()
                vuln_data[style] = vuln_data.get(style, 0) + 1
        
        # --- END NEW CHART LOGIC ---
"""

# Find the injection point: right before "dots = res['dot_balls'] or 0"
injection_target = "            dots = res['dot_balls'] or 0"
if injection_target in content:
    content = content.replace(injection_target, chart_logic + "\n" + injection_target)
    
    # Also we need to inject the chart arrays into the JSON response!
    return_target = "                \"dot_pct\": round((dots / balls * 100), 1) if balls > 0 else 0\n            })"
    return_replacement = "                \"dot_pct\": round((dots / balls * 100), 1) if balls > 0 else 0,\n                \"wagon_wheel\": wagon_wheel,\n                \"shot_data\": shot_data,\n                \"vuln_data\": vuln_data\n            })"
    content = content.replace(return_target, return_replacement)
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully injected chart logic into app.py")
else:
    print("Could not find injection point")

