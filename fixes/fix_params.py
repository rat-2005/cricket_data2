import re

with open('app.py', 'r') as f:
    content = f.read()

# Replace %tour% and %series% with %%tour%% and %%series%% everywhere EXCEPT in the global cache query where it might not need escaping if there are no params
# Actually, escaping it as %%tour%% when no params are provided might send %%tour%% to postgres, which is bad.
# Let's just use parameters! It's much safer!

where_d_target = """        if league_filter == 'Series':
            where_d.append("(l.name ILIKE '%tour%' OR l.name ILIKE '%series%')")
            where_cricsheet.append("1=0")"""

where_d_replacement = """        if league_filter == 'Series':
            where_d.append("(l.name ILIKE %s OR l.name ILIKE %s)")
            params_d.extend(['%tour%', '%series%'])
            where_cricsheet.append("1=0")"""

content = content.replace(where_d_target, where_d_replacement)

where_icc_target_1 = """                if league_filter == 'Series':
                    where_icc.append("(tournament ILIKE '%tour%' OR tournament ILIKE '%series%')")"""

where_icc_replacement_1 = """                if league_filter == 'Series':
                    where_icc.append("(tournament ILIKE %s OR tournament ILIKE %s)")
                    params_icc_extra.extend(['%tour%', '%series%'])"""

content = content.replace(where_icc_target_1, where_icc_replacement_1)


stats_where_d_target = """        if league == 'Series':
            where_d.append(\"\"\"
                (
                    c.event_id IN (SELECT el.event_id FROM cricket.event_leagues el JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name ILIKE '%tour%' OR l.name ILIKE '%series%')
                    OR
                    c.date::date IN (SELECT DISTINCT match_date::date FROM cricket.unified_deliveries WHERE tournament ILIKE '%tour%' OR tournament ILIKE '%series%')
                )
            \"\"\")"""

stats_where_d_replacement = """        if league == 'Series':
            where_d.append(\"\"\"
                (
                    c.event_id IN (SELECT el.event_id FROM cricket.event_leagues el JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name ILIKE %s OR l.name ILIKE %s)
                    OR
                    c.date::date IN (SELECT DISTINCT match_date::date FROM cricket.unified_deliveries WHERE tournament ILIKE %s OR tournament ILIKE %s)
                )
            \"\"\")
            params_d.extend(['%tour%', '%series%', '%tour%', '%series%'])"""

content = content.replace(stats_where_d_target, stats_where_d_replacement)

stats_where_icc_target = """            if league == 'Series':
                where_icc.append(\"\"\"
                    c.date::date IN (SELECT DISTINCT match_date::date FROM cricket.unified_deliveries WHERE tournament ILIKE '%tour%' OR tournament ILIKE '%series%')
                \"\"\")"""

stats_where_icc_replacement = """            if league == 'Series':
                where_icc.append(\"\"\"
                    c.date::date IN (SELECT DISTINCT match_date::date FROM cricket.unified_deliveries WHERE tournament ILIKE %s OR tournament ILIKE %s)
                \"\"\")
                params_icc.extend(['%tour%', '%series%'])"""

content = content.replace(stats_where_icc_target, stats_where_icc_replacement)

# And for faceoff where_icc:
faceoff_where_icc_target = """        if league == 'Series':
            where_icc.append(\"(tournament ILIKE '%tour%' OR tournament ILIKE '%series%')\")"""

faceoff_where_icc_replacement = """        if league == 'Series':
            where_icc.append(\"(tournament ILIKE %s OR tournament ILIKE %s)\")
            params_icc.extend(['%tour%', '%series%'])"""

content = content.replace(faceoff_where_icc_target, faceoff_where_icc_replacement)

with open('app.py', 'w') as f:
    f.write(content)
print('Fixed parameters')
