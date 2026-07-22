with open('d:/cricket/fresh_data/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the new APIs
new_apis = """
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
        where_cricsheet.append("d.over <= 5")
    elif phase_filter == 'Middle':
        where_d.append("d.over_number > 6 AND d.over_number <= 15")
        where_cricsheet.append("d.over > 5 AND d.over <= 14")
    elif phase_filter == 'Death':
        where_d.append("d.over_number > 15")
        where_cricsheet.append("d.over > 14")
        
    where_clause_d = " AND ".join(where_d)
    where_clause_cricsheet = " AND ".join(where_cricsheet)
    
    query = f\"\"\"
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
    \"\"\"
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params_d + params_cricsheet)
            res = cur.fetchone()
            
            return jsonify({
                "formats": sorted(res['formats']) if res and res['formats'] else [],
                "leagues": sorted(res['leagues']) if res and res['leagues'] else [],
                "venues": sorted(res['venues']) if res and res['venues'] else [],
                "phases": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"],
                "opponents": ["India", "Australia", "England", "South Africa", "New Zealand", "Pakistan", "Sri Lanka", "West Indies", "Bangladesh", "Afghanistan", "Chennai Super Kings", "Mumbai Indians", "Royal Challengers Bangalore", "Kolkata Knight Riders", "Delhi Capitals", "Rajasthan Royals", "Punjab Kings", "Sunrisers Hyderabad"]
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
        where_cricsheet.append("d.over <= 5")
    elif phase_filter == 'Middle':
        where_d.append("d.over_number > 6 AND d.over_number <= 15")
        where_cricsheet.append("d.over > 5 AND d.over <= 14")
    elif phase_filter == 'Death':
        where_d.append("d.over_number > 15")
        where_cricsheet.append("d.over > 14")
        
    where_clause_d = " AND ".join(where_d)
    where_clause_cricsheet = " AND ".join(where_cricsheet)
    
    query = f\"\"\"
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
    \"\"\"
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params_d + params_cricsheet)
            res = cur.fetchone()
            
            return jsonify({
                "formats": sorted(res['formats']) if res and res['formats'] else [],
                "leagues": sorted(res['leagues']) if res and res['leagues'] else [],
                "venues": sorted(res['venues']) if res and res['venues'] else [],
                "phases": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"],
                "opponents": ["India", "Australia", "England", "South Africa", "New Zealand", "Pakistan", "Sri Lanka", "West Indies", "Bangladesh", "Afghanistan", "Chennai Super Kings", "Mumbai Indians", "Royal Challengers Bangalore", "Kolkata Knight Riders", "Delhi Capitals", "Rajasthan Royals", "Punjab Kings", "Sunrisers Hyderabad"]
            })
"""

# Append to app.py before the if __name__ == '__main__': block
if "def batter_filters():" not in content:
    content = content.replace("if __name__ == '__main__':", new_apis + "\n\nif __name__ == '__main__':")
    with open('d:/cricket/fresh_data/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added /api/batter_filters and /api/bowler_filters")
else:
    print("APIs already exist")
