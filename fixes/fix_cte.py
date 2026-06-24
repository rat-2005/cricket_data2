import re

with open('app.py', 'r') as f:
    content = f.read()

new_select = """            WITH combined AS (
                SELECT 
                    CASE 
                        WHEN c.class_name IN ('T20', 'Twenty20', 'IPL', 'Women T20', 'Women''s T20', 'Other T20') THEN 'T20'
                        WHEN c.class_name IN ('T20I', 'ICCT') THEN 'T20I'
                        WHEN c.class_name IN ('ODI', 'Women''s ODI') THEN 'ODI'
                        WHEN c.class_name IN ('List A', 'Other OD', 'Youth ODI') THEN 'List A'
                        WHEN c.class_name IN ('Test', 'Women''s Test', 'MD') THEN 'Test'
                        WHEN c.class_name IN ('First-class', 'Youth Test') THEN 'First-class'
                        ELSE c.class_name 
                    END as format,
                    l.name as league,
                    v.full_name as venue,
                    t.name as opponent,
                    a.bowling_style as bowling_type,
                    EXTRACT(YEAR FROM c.date)::int as year_num
                FROM cricket.deliveries d
                JOIN cricket.competitions c ON c.id = d.competition_id
                LEFT JOIN cricket.event_leagues el ON c.event_id = el.event_id
                LEFT JOIN cricket.leagues l ON el.league_id = l.id
                LEFT JOIN cricket.venues v ON c.venue_id = v.id
                LEFT JOIN cricket.teams t ON d.bowling_team_id = t.id
                LEFT JOIN cricket.athletes a ON d.bowler_id = a.id
                WHERE {where_clause_d}
                
                UNION ALL
                
                SELECT 
                    CASE 
                        WHEN m.format IN ('T20', 'Twenty20') THEN 'T20'
                        WHEN m.format = 'IT20' THEN 'T20I'
                        WHEN m.format = 'ODI' THEN 'ODI'
                        WHEN m.format IN ('List A', 'Other OD') THEN 'List A'
                        WHEN m.format IN ('Test', 'MD') THEN 'Test'
                        ELSE m.format 
                    END as format,
                    NULL as league,
                    NULL as venue,
                    NULL as opponent,
                    NULL as bowling_type,
                    EXTRACT(YEAR FROM m.match_date)::int as year_num
                FROM cricket.cricsheet_deliveries d
                JOIN cricket.cricsheet_matches m ON m.id = d.match_id
                WHERE {where_clause_cricsheet}
                
                UNION ALL
                
                SELECT 
                    u.format as format,
                    u.tournament as league,
                    u.venue as venue,
                    NULL as opponent,
                    NULL as bowling_type,
                    EXTRACT(YEAR FROM u.match_date)::int as year_num
                FROM cricket.unified_deliveries u
                WHERE {where_clause_icc}
            )
            SELECT 
                array_remove(array_agg(DISTINCT format), NULL) as formats,
                array_remove(array_agg(DISTINCT CASE WHEN league ILIKE '%%tour%%' OR league ILIKE '%%series%%' THEN 'Series' ELSE league END), NULL) as leagues,
                array_remove(array_agg(DISTINCT venue), NULL) as venues,
                array_remove(array_agg(DISTINCT opponent), NULL) as opponents,
                array_remove(array_agg(DISTINCT bowling_type), NULL) as bowling_types,
                array_remove(array_agg(DISTINCT year_num), NULL) as years
            FROM combined"""

target_regex = r'WITH combined AS \(\s+SELECT\s+CASE.*?FROM combined'
match = re.search(target_regex, content, re.DOTALL)
if match:
    # We only want to replace the FIRST match (in batter_filters), not the ones in faceoff or bowler if they look similar
    content = content[:match.start()] + new_select + content[match.end():]
    with open('app.py', 'w') as f:
        f.write(content)
    print('Successfully replaced query!')
else:
    print('Could not find query using regex.')
