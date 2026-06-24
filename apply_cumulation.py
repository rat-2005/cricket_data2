import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update `/api/filters`
# Currently it has: `SELECT DISTINCT l.name as league` and `SELECT DISTINCT tournament as league`
filters_l_case = """SELECT DISTINCT CASE 
                        WHEN l.name ILIKE '%world cup%' OR l.name ILIKE '%world twenty20%' OR l.name ILIKE '%t20 world cup%' OR l.name ILIKE '%championship%' THEN 'World Cup'
                        WHEN l.name ILIKE '%asia cup%' THEN 'Asia Cup'
                        WHEN l.name ILIKE '%champions trophy%' THEN 'Champions Trophy'
                        WHEN l.name ILIKE '%premier league%' OR l.name ILIKE '%ipl%' THEN 'Indian Premier League'
                        ELSE 'Series' END as league"""

filters_t_case = """SELECT DISTINCT CASE 
                        WHEN tournament ILIKE '%world cup%' OR tournament ILIKE '%world twenty20%' OR tournament ILIKE '%t20 world cup%' OR tournament ILIKE '%championship%' THEN 'World Cup'
                        WHEN tournament ILIKE '%asia cup%' THEN 'Asia Cup'
                        WHEN tournament ILIKE '%champions trophy%' THEN 'Champions Trophy'
                        WHEN tournament ILIKE '%premier league%' OR tournament ILIKE '%ipl%' THEN 'Indian Premier League'
                        ELSE 'Series' END as league"""

content = content.replace("SELECT DISTINCT l.name as league", filters_l_case)
content = content.replace("SELECT DISTINCT tournament as league", filters_t_case)

# 2. Update `batter_filters`, `bowler_filters`, `faceoff_filters`
# Currently they have: `array_remove(array_agg(DISTINCT league), NULL) as leagues`
new_agg_case = """array_remove(array_agg(DISTINCT CASE 
                WHEN league ILIKE '%%world cup%%' OR league ILIKE '%%world twenty20%%' OR league ILIKE '%%t20 world cup%%' OR league ILIKE '%%championship%%' THEN 'World Cup'
                WHEN league ILIKE '%%asia cup%%' THEN 'Asia Cup'
                WHEN league ILIKE '%%champions trophy%%' THEN 'Champions Trophy'
                WHEN league ILIKE '%%premier league%%' OR league ILIKE '%%ipl%%' THEN 'Indian Premier League'
                ELSE 'Series' END), NULL) as leagues"""

content = content.replace("array_remove(array_agg(DISTINCT league), NULL) as leagues", new_agg_case)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied cumulation logic to ALL endpoints!")
