import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

def fix_filters_logic(match):
    # This matches the league_filter if-else block
    return """        if league_filter == 'Series':
            where_d.append("(l.name ILIKE '%%tour%%' OR l.name ILIKE '%%series%%')")
            where_cricsheet.append("1=0")
        elif league_filter == 'Asia Cup':
            where_d.append("l.name ILIKE '%%asia cup%%'")
            where_cricsheet.append("1=0")
        elif league_filter == 'Champions Trophy':
            where_d.append("l.name ILIKE '%%champions trophy%%'")
            where_cricsheet.append("1=0")
        elif league_filter == 'World Cup':
            where_d.append("l.name ILIKE '%%world cup%%'")
            where_cricsheet.append("1=0")
        else:
            where_d.append("l.name = %s")
            params_d.append(league_filter)
            where_cricsheet.append("1=0")"""

regex_d = r"\s*if league_filter == 'Series':\n\s*where_d\.append\(\"\(l\.name ILIKE '%%tour%%' OR l\.name ILIKE '%%series%%'\)\"\)\n\s*where_cricsheet\.append\(\"1=0\"\)\n\s*else:\n\s*where_d\.append\(\"l\.name = %s\"\)\n\s*params_d\.append\(league_filter\)\n\s*where_cricsheet\.append\(\"1=0\"\)"

content = re.sub(regex_d, fix_filters_logic, content)

def fix_icc_logic(match):
    return """                if league_filter == 'Series':
                    where_icc.append("(tournament ILIKE '%%tour%%' OR tournament ILIKE '%%series%%')")
                elif league_filter == 'Asia Cup':
                    where_icc.append("tournament ILIKE '%%asia cup%%'")
                elif league_filter == 'Champions Trophy':
                    where_icc.append("tournament ILIKE '%%champions trophy%%'")
                elif league_filter == 'World Cup':
                    where_icc.append("tournament ILIKE '%%world cup%%'")
                else:
                    where_icc.append("tournament = %s")
                    params_icc_extra.append(league_filter)"""

regex_icc = r"\s*if league_filter == 'Series':\n\s*where_icc\.append\(\"\(tournament ILIKE '%%tour%%' OR tournament ILIKE '%%series%%'\)\"\)\n\s*else:\n\s*where_icc\.append\(\"tournament = %s\"\)\n\s*params_icc_extra\.append\(league_filter\)"

content = re.sub(regex_icc, fix_icc_logic, content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated filters logic in app.py!")
