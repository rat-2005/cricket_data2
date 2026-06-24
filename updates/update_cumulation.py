import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the CASE statement for generating the array_agg in batter_filters, bowler_filters, faceoff_filters
# The old one might look like:
# CASE WHEN league ILIKE '%%tour%%' OR league ILIKE '%%series%%' THEN 'Series' WHEN league ILIKE '%%asia cup%%' THEN 'Asia Cup' WHEN league ILIKE '%%champions trophy%%' THEN 'Champions Trophy' WHEN league ILIKE '%%world cup%%' THEN 'World Cup' ELSE league END
# We want to replace it entirely.

new_case_statement = """CASE 
                WHEN league ILIKE '%%world cup%%' OR league ILIKE '%%world twenty20%%' OR league ILIKE '%%t20 world cup%%' OR league ILIKE '%%championship%%' THEN 'World Cup'
                WHEN league ILIKE '%%asia cup%%' THEN 'Asia Cup'
                WHEN league ILIKE '%%champions trophy%%' THEN 'Champions Trophy'
                WHEN league ILIKE '%%premier league%%' OR league ILIKE '%%ipl%%' THEN 'Indian Premier League'
                ELSE 'Series' END"""

# Let's replace the array_agg part
content = re.sub(
    r"CASE\s*WHEN league ILIKE '%%tour%%'.*?ELSE league END",
    new_case_statement,
    content,
    flags=re.DOTALL
)

# 2. Update the `/api/filters` endpoint
# It has: CASE WHEN l.name ILIKE '%tour%' OR l.name ILIKE '%series%' THEN 'Series' ELSE l.name END as league
filters_l_case = """CASE 
                        WHEN l.name ILIKE '%world cup%' OR l.name ILIKE '%world twenty20%' OR l.name ILIKE '%t20 world cup%' OR l.name ILIKE '%championship%' THEN 'World Cup'
                        WHEN l.name ILIKE '%asia cup%' THEN 'Asia Cup'
                        WHEN l.name ILIKE '%champions trophy%' THEN 'Champions Trophy'
                        WHEN l.name ILIKE '%premier league%' OR l.name ILIKE '%ipl%' THEN 'Indian Premier League'
                        ELSE 'Series' END as league"""

filters_t_case = """CASE 
                        WHEN tournament ILIKE '%world cup%' OR tournament ILIKE '%world twenty20%' OR tournament ILIKE '%t20 world cup%' OR tournament ILIKE '%championship%' THEN 'World Cup'
                        WHEN tournament ILIKE '%asia cup%' THEN 'Asia Cup'
                        WHEN tournament ILIKE '%champions trophy%' THEN 'Champions Trophy'
                        WHEN tournament ILIKE '%premier league%' OR tournament ILIKE '%ipl%' THEN 'Indian Premier League'
                        ELSE 'Series' END as league"""

content = re.sub(
    r"CASE WHEN l\.name ILIKE '%tour%' OR l\.name ILIKE '%series%' THEN 'Series' ELSE l\.name END as league",
    filters_l_case,
    content
)
content = re.sub(
    r"CASE WHEN tournament ILIKE '%tour%' OR tournament ILIKE '%series%' THEN 'Series' ELSE tournament END as league",
    filters_t_case,
    content
)

# 3. We also need to update the python logic for `if league_filter == ...:` inside stats_batter etc.
# We have a block that looks like:
#         if league_filter == 'Series':
#             where_d.append("(l.name ILIKE '%%tour%%' OR l.name ILIKE '%%series%%')")
#             where_cricsheet.append("1=0")
#         elif league_filter == 'Asia Cup':
#             where_d.append("l.name ILIKE '%%asia cup%%'")
#             where_cricsheet.append("1=0")
#         ...
# We will write a function to replace it globally.

def replace_league_conditions(match):
    prefix = match.group(1) # e.g. "where_d"
    prefix_param = match.group(2) # e.g. "params_d"
    return f"""        if league_filter == 'Series':
            {prefix}.append("(l.name NOT ILIKE '%%world cup%%' AND l.name NOT ILIKE '%%world twenty20%%' AND l.name NOT ILIKE '%%t20 world cup%%' AND l.name NOT ILIKE '%%championship%%' AND l.name NOT ILIKE '%%asia cup%%' AND l.name NOT ILIKE '%%champions trophy%%' AND l.name NOT ILIKE '%%premier league%%' AND l.name NOT ILIKE '%%ipl%%')")
            where_cricsheet.append("(match_date::date > '1900-01-01')") # everything else goes to series
            where_icc.append("(tournament NOT ILIKE '%%world cup%%' AND tournament NOT ILIKE '%%world twenty20%%' AND tournament NOT ILIKE '%%t20 world cup%%' AND tournament NOT ILIKE '%%championship%%' AND tournament NOT ILIKE '%%asia cup%%' AND tournament NOT ILIKE '%%champions trophy%%' AND tournament NOT ILIKE '%%premier league%%' AND tournament NOT ILIKE '%%ipl%%')")
        elif league_filter == 'World Cup':
            {prefix}.append("(l.name ILIKE '%%world cup%%' OR l.name ILIKE '%%world twenty20%%' OR l.name ILIKE '%%t20 world cup%%' OR l.name ILIKE '%%championship%%')")
            where_cricsheet.append("1=0")
            where_icc.append("(tournament ILIKE '%%world cup%%' OR tournament ILIKE '%%world twenty20%%' OR tournament ILIKE '%%t20 world cup%%' OR tournament ILIKE '%%championship%%')")
        elif league_filter == 'Asia Cup':
            {prefix}.append("l.name ILIKE '%%asia cup%%'")
            where_cricsheet.append("1=0")
            where_icc.append("tournament ILIKE '%%asia cup%%'")
        elif league_filter == 'Champions Trophy':
            {prefix}.append("l.name ILIKE '%%champions trophy%%'")
            where_cricsheet.append("1=0")
            where_icc.append("tournament ILIKE '%%champions trophy%%'")
        elif league_filter == 'Indian Premier League':
            {prefix}.append("(l.name ILIKE '%%premier league%%' OR l.name ILIKE '%%ipl%%')")
            where_cricsheet.append("1=0")
            where_icc.append("(tournament ILIKE '%%premier league%%' OR tournament ILIKE '%%ipl%%')")
        else:
            {prefix}.append("1=0") # We don't use direct matches anymore because we exhaust all buckets
            where_cricsheet.append("1=0")
            where_icc.append("1=0")"""

# But wait, there are 3 instances (stats_batter, stats_bowler, stats_faceoff). The prefixes are `where_d`, `where_b`, `where_f`.
# Let's just do a manual string replace to be very safe.

def replace_block(content, var, param_var):
    old_block = f"""        if league_filter == 'Series':
            {var}.append("(l.name ILIKE '%%tour%%' OR l.name ILIKE '%%series%%')")
            where_cricsheet.append("1=0")
        elif league_filter == 'Asia Cup':
            {var}.append("l.name ILIKE '%%asia cup%%'")
            where_cricsheet.append("1=0")
        elif league_filter == 'Champions Trophy':
            {var}.append("l.name ILIKE '%%champions trophy%%'")
            where_cricsheet.append("1=0")
        elif league_filter == 'World Cup':
            {var}.append("l.name ILIKE '%%world cup%%'")
            where_cricsheet.append("1=0")
        else:
            {var}.append("l.name = %s")
            {param_var}.append(league_filter)
            where_cricsheet.append("1=0")"""
            
    new_block = f"""        if league_filter == 'Series':
            {var}.append("(l.name NOT ILIKE '%%world cup%%' AND l.name NOT ILIKE '%%world twenty20%%' AND l.name NOT ILIKE '%%t20 world cup%%' AND l.name NOT ILIKE '%%championship%%' AND l.name NOT ILIKE '%%asia cup%%' AND l.name NOT ILIKE '%%champions trophy%%' AND l.name NOT ILIKE '%%premier league%%' AND l.name NOT ILIKE '%%ipl%%')")
            where_cricsheet.append("(1=1)") # everything else goes to series
            where_icc.append("(tournament NOT ILIKE '%%world cup%%' AND tournament NOT ILIKE '%%world twenty20%%' AND tournament NOT ILIKE '%%t20 world cup%%' AND tournament NOT ILIKE '%%championship%%' AND tournament NOT ILIKE '%%asia cup%%' AND tournament NOT ILIKE '%%champions trophy%%' AND tournament NOT ILIKE '%%premier league%%' AND tournament NOT ILIKE '%%ipl%%' OR tournament IS NULL)")
        elif league_filter == 'World Cup':
            {var}.append("(l.name ILIKE '%%world cup%%' OR l.name ILIKE '%%world twenty20%%' OR l.name ILIKE '%%t20 world cup%%' OR l.name ILIKE '%%championship%%')")
            where_cricsheet.append("1=0")
            where_icc.append("(tournament ILIKE '%%world cup%%' OR tournament ILIKE '%%world twenty20%%' OR tournament ILIKE '%%t20 world cup%%' OR tournament ILIKE '%%championship%%')")
        elif league_filter == 'Asia Cup':
            {var}.append("l.name ILIKE '%%asia cup%%'")
            where_cricsheet.append("1=0")
            where_icc.append("tournament ILIKE '%%asia cup%%'")
        elif league_filter == 'Champions Trophy':
            {var}.append("l.name ILIKE '%%champions trophy%%'")
            where_cricsheet.append("1=0")
            where_icc.append("tournament ILIKE '%%champions trophy%%'")
        elif league_filter == 'Indian Premier League':
            {var}.append("(l.name ILIKE '%%premier league%%' OR l.name ILIKE '%%ipl%%')")
            where_cricsheet.append("1=0")
            where_icc.append("(tournament ILIKE '%%premier league%%' OR tournament ILIKE '%%ipl%%')")
        else:
            {var}.append("1=0")
            where_cricsheet.append("1=0")
            where_icc.append("1=0")"""
            
    return content.replace(old_block, new_block)

content = replace_block(content, 'where_d', 'params_d')
content = replace_block(content, 'where_b', 'params_b')
content = replace_block(content, 'where_f', 'params_f')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated cumulative grouping logic successfully!")
