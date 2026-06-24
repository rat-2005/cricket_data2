import re

with open('app.py', 'r') as f:
    content = f.read()

target = """    if league != 'All':
        where_d.append(\"\"\"
            (
                c.event_id IN (SELECT el.event_id FROM cricket.event_leagues el JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name = %s)
                OR
                c.date::date IN (SELECT DISTINCT match_date::date FROM cricket.unified_deliveries WHERE tournament LIKE %s)
            )
        \"\"\")
        params_d.extend([league, league + '%'])"""

replacement = """    if league != 'All':
        if league == 'Series':
            where_d.append(\"\"\"
                (
                    c.event_id IN (SELECT el.event_id FROM cricket.event_leagues el JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name ILIKE '%tour%' OR l.name ILIKE '%series%')
                    OR
                    c.date::date IN (SELECT DISTINCT match_date::date FROM cricket.unified_deliveries WHERE tournament ILIKE '%tour%' OR tournament ILIKE '%series%')
                )
            \"\"\")
        else:
            where_d.append(\"\"\"
                (
                    c.event_id IN (SELECT el.event_id FROM cricket.event_leagues el JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name = %s)
                    OR
                    c.date::date IN (SELECT DISTINCT match_date::date FROM cricket.unified_deliveries WHERE tournament LIKE %s)
                )
            \"\"\")
            params_d.extend([league, league + '%'])"""

content = content.replace(target, replacement)

# Need to also replace the where_icc logic for stats_faceoff, batter, bowler which uses tournament LIKE %s
target_icc_batter = """        if league != 'All':
            where_icc.append(\"\"\"
                c.date::date IN (SELECT DISTINCT match_date::date FROM cricket.unified_deliveries WHERE tournament LIKE %s)
            \"\"\")
            params_icc.append(league + '%')"""

replacement_icc_batter = """        if league != 'All':
            if league == 'Series':
                where_icc.append(\"\"\"
                    c.date::date IN (SELECT DISTINCT match_date::date FROM cricket.unified_deliveries WHERE tournament ILIKE '%tour%' OR tournament ILIKE '%series%')
                \"\"\")
            else:
                where_icc.append(\"\"\"
                    c.date::date IN (SELECT DISTINCT match_date::date FROM cricket.unified_deliveries WHERE tournament LIKE %s)
                \"\"\")
                params_icc.append(league + '%')"""

content = content.replace(target_icc_batter, replacement_icc_batter)

# and for faceoff it might be different, it uses where_icc.append("tournament = %s") which we already replaced in update_league.py!
# Wait, faceoff where_icc is NOT target_icc_batter.
# Let's write the file.
with open('app.py', 'w') as f:
    f.write(content)

print('Updated stats logic')
