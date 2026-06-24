import re

with open('app.py', 'r') as f:
    content = f.read()

# Update league_filter where_d logic
where_d_target = """    if league_filter != 'All':
        where_d.append("l.name = %s")
        params_d.append(league_filter)
        where_cricsheet.append("1=0")"""

where_d_replacement = """    if league_filter != 'All':
        if league_filter == 'Series':
            where_d.append("(l.name ILIKE '%tour%' OR l.name ILIKE '%series%')")
            where_cricsheet.append("1=0")
        else:
            where_d.append("l.name = %s")
            params_d.append(league_filter)
            where_cricsheet.append("1=0")"""

content = content.replace(where_d_target, where_d_replacement)

# Update league_filter where_icc logic
where_icc_target_1 = """            if league_filter != 'All':
                where_icc.append("tournament = %s")
                params_icc_extra.append(league_filter)"""

where_icc_replacement_1 = """            if league_filter != 'All':
                if league_filter == 'Series':
                    where_icc.append("(tournament ILIKE '%tour%' OR tournament ILIKE '%series%')")
                else:
                    where_icc.append("tournament = %s")
                    params_icc_extra.append(league_filter)"""

content = content.replace(where_icc_target_1, where_icc_replacement_1)

# Stats batter etc where_icc logic
where_icc_target_2 = """    if league_filter != 'All':
        where_icc.append("tournament = %s")
        params_icc.append(league_filter)"""

where_icc_replacement_2 = """    if league_filter != 'All':
        if league_filter == 'Series':
            where_icc.append("(tournament ILIKE '%tour%' OR tournament ILIKE '%series%')")
        else:
            where_icc.append("tournament = %s")
            params_icc.append(league_filter)"""

content = content.replace(where_icc_target_2, where_icc_replacement_2)

# Update global filters() cache query
filters_target = """                # Get distinct leagues/competitions
                cur.execute(\"\"\"
                    SELECT DISTINCT l.name as league 
                    FROM cricket.leagues l
                    UNION
                    SELECT DISTINCT tournament as league
                    FROM cricket.unified_deliveries
                    WHERE tournament IS NOT NULL AND tournament != ''
                \"\"\")"""

filters_replacement = """                # Get distinct leagues/competitions
                cur.execute(\"\"\"
                    SELECT DISTINCT CASE WHEN l.name ILIKE '%tour%' OR l.name ILIKE '%series%' THEN 'Series' ELSE l.name END as league 
                    FROM cricket.leagues l
                    UNION
                    SELECT DISTINCT CASE WHEN tournament ILIKE '%tour%' OR tournament ILIKE '%series%' THEN 'Series' ELSE tournament END as league
                    FROM cricket.unified_deliveries
                    WHERE tournament IS NOT NULL AND tournament != ''
                \"\"\")"""

content = content.replace(filters_target, filters_replacement)

with open('app.py', 'w') as f:
    f.write(content)

print('Updated app.py league logic')
