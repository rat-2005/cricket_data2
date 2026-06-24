import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

chart_logic = """
            # --- NEW CHART LOGIC using unified_deliveries ---
            cur.execute("SELECT full_name, short_name FROM cricket.athletes WHERE id = %s", (athlete_id,))
            a_row = cur.fetchone()
            a_names = []
            if a_row:
                if a_row['full_name']: a_names.append(a_row['full_name'].replace("'", "''"))
                if a_row['short_name']: a_names.append(a_row['short_name'].replace("'", "''"))
                if a_row['full_name']:
                    parts = a_row['full_name'].split()
                    if len(parts) > 1:
                        a_names.append(f"{parts[0][0]} {parts[-1]}".replace("'", "''"))
                        a_names.append(f"{parts[0][0]}. {parts[-1]}".replace("'", "''"))
            if not a_names:
                a_names = ['Unknown']
            names_str = ", ".join([f"'{n}'" for n in a_names])
            
            where_u = [f"((u.source_database = 'ESPN' AND u.batsman_id = %s) OR (u.source_database = 'ICC' AND u.batsman_name IN ({names_str})))"]
            params_u = [athlete_id]
            
            if fmt != 'All':
                if fmt in ('T20', 'Twenty20'):
                    where_u.append("((u.source_database = 'ESPN' AND u.match_id IN (SELECT id FROM cricket.competitions WHERE class_name IN ('T20', 'Twenty20', 'T20I', 'IPL', 'Women T20', 'Women''s T20', 'Other T20', 'Youth T20I', 'ICCT'))) OR (u.source_database = 'ICC' AND u.match_id IN (SELECT id::VARCHAR FROM cricket.cricsheet_matches WHERE format IN ('T20', 'Twenty20', 'IT20'))))")
                elif fmt == 'ODI':
                    where_u.append("((u.source_database = 'ESPN' AND u.match_id IN (SELECT id FROM cricket.competitions WHERE class_name IN ('ODI', 'Women''s ODI', 'Youth ODI', 'List A', 'Other OD'))) OR (u.source_database = 'ICC' AND u.match_id IN (SELECT id::VARCHAR FROM cricket.cricsheet_matches WHERE format = 'ODI')))")
                elif fmt == 'Test':
                    where_u.append("((u.source_database = 'ESPN' AND u.match_id IN (SELECT id FROM cricket.competitions WHERE class_name IN ('Test', 'Women''s Test', 'Youth Test', 'First-class', 'MD'))) OR (u.source_database = 'ICC' AND u.match_id IN (SELECT id::VARCHAR FROM cricket.cricsheet_matches WHERE format IN ('Test', 'MD'))))")
                else:
                    where_u.append(f"((u.source_database = 'ESPN' AND u.match_id IN (SELECT id FROM cricket.competitions WHERE class_name = '{fmt}')) OR (u.source_database = 'ICC' AND u.match_id IN (SELECT id::VARCHAR FROM cricket.cricsheet_matches WHERE format = '{fmt}')))")
                
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
                where_u.append(f"((u.source_database = 'ESPN' AND u.bowling_team_id IN (SELECT id FROM cricket.teams WHERE name ILIKE '%%{opponent}%%' OR abbreviation ILIKE '%%{opponent}%%')) OR (u.source_database = 'ICC' AND u.match_id IN (SELECT id::VARCHAR FROM cricket.cricsheet_matches WHERE team1 ILIKE '%%{opponent}%%' OR team2 ILIKE '%%{opponent}%%')))")
                
            if bowling_type != 'All':
                where_u.append(f"((u.source_database = 'ESPN' AND u.bowler_id IN (SELECT id FROM cricket.athletes WHERE bowling_style ILIKE '%%{bowling_type}%%')) OR (u.source_database = 'ICC' AND u.bowler_name IN (SELECT full_name FROM cricket.athletes WHERE bowling_style ILIKE '%%{bowling_type}%%')))")
                
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
                    u.shot_type
                FROM cricket.unified_deliveries u
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
                
                if x_coord is not None and y_coord is not None:
                    wagon_wheel.append({"x": x_coord, "y": y_coord, "runs": b_runs})
                elif zad and zad.strip():
                    parts = zad.split(',')
                    if len(parts) >= 2:
                        try:
                            angle = int(parts[1])
                            dist = int(parts[2]) if len(parts) >= 3 else 3
                            rad = math.radians(angle)
                            r_norm = dist / 6.0
                            x = -r_norm * math.sin(rad)
                            y = -r_norm * math.cos(rad)
                            wagon_wheel.append({"x": x, "y": y, "runs": b_runs})
                        except:
                            pass
                            
                if shot and shot.strip():
                    shot_name = shot.title()
                    shot_data[shot_name] = shot_data.get(shot_name, 0) + 1
                    
            # --- END NEW CHART LOGIC ---
"""

if '# --- NEW CHART LOGIC using unified_deliveries ---' in content:
    content = re.sub(r'# --- NEW CHART LOGIC using unified_deliveries ---.*?# --- END NEW CHART LOGIC ---\n', '', content, flags=re.DOTALL)

injection_target = "            dots = res['dot_balls'] or 0"
if injection_target in content:
    content = content.replace(injection_target, chart_logic + "\n" + injection_target)
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully re-injected chart logic (removed vuln_data) into app.py")
else:
    print("Could not find injection point")
