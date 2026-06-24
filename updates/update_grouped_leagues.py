import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace stats_batter, stats_bowler, stats_faceoff, player query blocks

def replace_league_block(match):
    # This matches the "if league == 'Series':" block and the "else" block.
    # We reconstruct it properly with the missing params and the new leagues!
    
    # Check if this is the block that has where_d, where_b, where_f, or where_clause
    block_text = match.group(0)
    
    var_prefix = "where_d"
    if "where_b.append" in block_text:
        var_prefix = "where_b"
    elif "where_f.append" in block_text:
        var_prefix = "where_f"
    elif "where_clause.append" in block_text:
        var_prefix = "where_clause"
        
    var_params = "params_d"
    if "params_b.extend" in block_text:
        var_params = "params_b"
    elif "params_f.extend" in block_text:
        var_params = "params_f"
    elif "params.extend" in block_text:
        var_params = "params"

    new_block = f"""        if league == 'Series':
            {var_prefix}.append(\"\"\"
                (
                    c.event_id IN (SELECT el.event_id FROM cricket.event_leagues el JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name ILIKE %s OR l.name ILIKE %s)
                    OR
                    c.date::date IN (SELECT DISTINCT match_date::date FROM cricket.unified_deliveries WHERE tournament ILIKE %s OR tournament ILIKE %s)
                )
            \"\"\")
            {var_params}.extend(['%tour%', '%series%', '%tour%', '%series%'])
        elif league == 'Asia Cup':
            {var_prefix}.append(\"\"\"
                (
                    c.event_id IN (SELECT el.event_id FROM cricket.event_leagues el JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name ILIKE %s)
                    OR
                    c.date::date IN (SELECT DISTINCT match_date::date FROM cricket.unified_deliveries WHERE tournament ILIKE %s)
                )
            \"\"\")
            {var_params}.extend(['%asia cup%', '%asia cup%'])
        elif league == 'Champions Trophy':
            {var_prefix}.append(\"\"\"
                (
                    c.event_id IN (SELECT el.event_id FROM cricket.event_leagues el JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name ILIKE %s)
                    OR
                    c.date::date IN (SELECT DISTINCT match_date::date FROM cricket.unified_deliveries WHERE tournament ILIKE %s)
                )
            \"\"\")
            {var_params}.extend(['%champions trophy%', '%champions trophy%'])
        elif league == 'World Cup':
            {var_prefix}.append(\"\"\"
                (
                    c.event_id IN (SELECT el.event_id FROM cricket.event_leagues el JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name ILIKE %s)
                    OR
                    c.date::date IN (SELECT DISTINCT match_date::date FROM cricket.unified_deliveries WHERE tournament ILIKE %s)
                )
            \"\"\")
            {var_params}.extend(['%world cup%', '%world cup%'])
        else:
            {var_prefix}.append(\"\"\"
                (
                    c.event_id IN (SELECT el.event_id FROM cricket.event_leagues el JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name = %s)
                    OR
                    c.date::date IN (SELECT DISTINCT match_date::date FROM cricket.unified_deliveries WHERE tournament LIKE %s)
                )
            \"\"\")
            {var_params}.extend([league, league + '%'])"""
    
    return new_block


regex = r"        if league == 'Series':\n\s*(where_\w+|where_clause)\.append\(\"\"\"\n\s*\(\n\s*c\.event_id IN \(SELECT el\.event_id FROM cricket\.event_leagues el JOIN cricket\.leagues l ON el\.league_id = l\.id WHERE l\.name ILIKE %s OR l\.name ILIKE %s\)\n\s*OR\n\s*c\.date::date IN \(SELECT DISTINCT match_date::date FROM cricket\.unified_deliveries WHERE tournament ILIKE %s OR tournament ILIKE %s\)\n\s*\)\n\s*\"\"\"\)\n\s*(?:(?:params_\w+|params)\.extend\(\['%tour%', '%series%', '%tour%', '%series%']\)\n\s*)?else:\n\s*(where_\w+|where_clause)\.append\(\"\"\"\n\s*\(\n\s*c\.event_id IN \(SELECT el\.event_id FROM cricket\.event_leagues el JOIN cricket\.leagues l ON el\.league_id = l\.id WHERE l\.name = %s\)\n\s*OR\n\s*c\.date::date IN \(SELECT DISTINCT match_date::date FROM cricket\.unified_deliveries WHERE tournament LIKE %s\)\n\s*\)\n\s*\"\"\"\)\n\s*(?:params_\w+|params)\.extend\(\[league, league \+ '%'\]\)"

content = re.sub(regex, replace_league_block, content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated app.py!")
