with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
start_idx = content.find('def stats_faceoff():')
if start_idx != -1:
    end_idx = content.find('def stats_match(', start_idx)
    if end_idx == -1: end_idx = len(content)
    
    faceoff_block = content[start_idx:end_idx]
    
    faceoff_block = re.sub(r'# --- NEW CHART LOGIC using unified_deliveries ---.*?# --- END NEW CHART LOGIC ---\n', '', faceoff_block, flags=re.DOTALL)
    
    new_chart_logic = """
            # --- NEW CHART LOGIC using unified_deliveries FOR FACEOFF ---
            cur.execute("SELECT full_name, short_name FROM cricket.athletes WHERE id = %s", (batter_id,))
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

            cur.execute("SELECT full_name, short_name FROM cricket.athletes WHERE id = %s", (bowler_id,))
            b_row = cur.fetchone()
            b_names = []
            if b_row:
                if b_row['full_name']: b_names.append(b_row['full_name'].replace("'", "''"))
                if b_row['short_name']: b_names.append(b_row['short_name'].replace("'", "''"))
                if b_row['full_name']:
                    parts = b_row['full_name'].split()
                    if len(parts) > 1:
                        b_names.append(f"{parts[0][0]} {parts[-1]}".replace("'", "''"))
                        b_names.append(f"{parts[0][0]}. {parts[-1]}".replace("'", "''"))
            if not b_names:
                b_names = ['Unknown']
            b_names_str = ", ".join([f"'{n}'" for n in b_names])
            
            where_u = [f"((u.source_database = 'ESPN' AND u.batsman_id = %s AND u.bowler_id = %s) OR (u.source_database = 'ICC' AND u.batsman_name IN ({names_str}) AND u.bowler_name IN ({b_names_str})))"]
            params_u = [batter_id, bowler_id]
            
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
                    
            where_clause_u = " AND ".join(where_u)
            
            chart_query = f\"\"\"
                SELECT 
                    u.x_coordinate, 
                    u.y_coordinate, 
                    u.zad, 
                    u.batsman_runs,
                    u.shot_type
                FROM cricket.unified_deliveries u
                WHERE {where_clause_u}
            \"\"\"
            
            cur.execute(chart_query, tuple(params_u))
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
                    
            # --- END NEW CHART LOGIC FOR FACEOFF ---
"""

    faceoff_block = faceoff_block.replace("            dots = res['dot_balls'] or 0", new_chart_logic + "\n            dots = res['dot_balls'] or 0")
    content = content[:start_idx] + faceoff_block + content[end_idx:]
    with open('app.py', 'w', encoding='utf-8') as f: 
        f.write(content)
    print('Successfully updated stats_faceoff')
else:
    print('Failed to find stats_faceoff')
