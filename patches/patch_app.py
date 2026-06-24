import re

with open('app.py', 'r') as f:
    content = f.read()

content = content.replace('where_d = ["d.batsman_id = %s"]', 'where_d = ["d.batsman_id = %s", "c.date::date < \'2025-01-01\'"]')
content = content.replace('where_cricsheet = ["d.batsman_id = %s"]', 'where_cricsheet = ["d.batsman_id = %s", "m.match_date::date < \'2025-01-01\'"]')
content = content.replace('where_icc = ["u.batsman_name IN %s", "u.source_database = \'ICC\'"]', 'where_icc = ["u.batsman_name IN %s", "u.source_database = \'ICC\'", "u.match_date::date < \'2025-01-01\'"]')

content = content.replace('where_d = ["d.bowler_id = %s"]', 'where_d = ["d.bowler_id = %s", "c.date::date < \'2025-01-01\'"]')
content = content.replace('where_cricsheet = ["d.bowler_id = %s"]', 'where_cricsheet = ["d.bowler_id = %s", "m.match_date::date < \'2025-01-01\'"]')
content = content.replace('where_icc = ["u.bowler_name IN %s", "u.source_database = \'ICC\'"]', 'where_icc = ["u.bowler_name IN %s", "u.source_database = \'ICC\'", "u.match_date::date < \'2025-01-01\'"]')

content = content.replace('where_d = ["d.batsman_id = %s", "d.bowler_id = %s"]', 'where_d = ["d.batsman_id = %s", "d.bowler_id = %s", "c.date::date < \'2025-01-01\'"]')
content = content.replace('where_cricsheet = ["d.batsman_id = %s", "d.bowler_id = %s"]', 'where_cricsheet = ["d.batsman_id = %s", "d.bowler_id = %s", "m.match_date::date < \'2025-01-01\'"]')

content = re.sub(r'where_icc = \["batsman_name IN %s", "bowler_name IN %s", "source_database = \'ICC\'", "zad IS NOT NULL", "zad != \'\'"\]', 
                 'where_icc = ["batsman_name IN %s", "bowler_name IN %s", "source_database = \'ICC\'", "zad IS NOT NULL", "zad != \'\'", "match_date::date < \'2025-01-01\'"]', content)

with open('app.py', 'w') as f:
    f.write(content)

print('Updated app.py')
