import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix d.innings = %s -> d.period = %s
content = re.sub(r'where_d\.append\("d\.innings = %s"\)', r'where_d.append("d.period = %s")', content)
content = re.sub(r'where_b\.append\("d\.innings = %s"\)', r'where_b.append("d.period = %s")', content)
content = re.sub(r'where_f\.append\("d\.innings = %s"\)', r'where_f.append("d.period = %s")', content)
content = re.sub(r'where_clause\.append\("d\.innings = %s"\)', r'where_clause.append("d.period = %s")', content)

# 2. League Cumulation Logic in filters()
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

# 3. League Cumulation Logic in batter_filters, bowler_filters, faceoff_filters
# Notice the old one was added in an earlier commit but might differ slightly.
# Let's just find `array_agg(DISTINCT CASE ... END)`
new_agg_case = """CASE 
                WHEN league ILIKE '%%world cup%%' OR league ILIKE '%%world twenty20%%' OR league ILIKE '%%t20 world cup%%' OR league ILIKE '%%championship%%' THEN 'World Cup'
                WHEN league ILIKE '%%asia cup%%' THEN 'Asia Cup'
                WHEN league ILIKE '%%champions trophy%%' THEN 'Champions Trophy'
                WHEN league ILIKE '%%premier league%%' OR league ILIKE '%%ipl%%' THEN 'Indian Premier League'
                ELSE 'Series' END"""

# The exact old string from earlier was `CASE WHEN league ILIKE '%%tour%%' OR league ILIKE '%%series%%' THEN 'Series' WHEN league ILIKE '%%asia cup%%' THEN 'Asia Cup' WHEN league ILIKE '%%champions trophy%%' THEN 'Champions Trophy' WHEN league ILIKE '%%world cup%%' THEN 'World Cup' ELSE league END`
content = re.sub(
    r"CASE\s*WHEN league ILIKE '%%tour%%'[^)]+ELSE league END",
    new_agg_case,
    content
)

# 4. League Cumulation Logic in stats_batter, stats_bowler, stats_faceoff
# We will use exactly literal replaces without Regex DOTALL to avoid destroying the file!

def replace_block(text, var, param_var):
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
            where_cricsheet.append("(1=1)")
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
            
    return text.replace(old_block, new_block)

content = replace_block(content, 'where_d', 'params_d')
content = replace_block(content, 'where_b', 'params_b')
content = replace_block(content, 'where_f', 'params_f')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied carefully!")
