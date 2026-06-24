import re
with open('app.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if "if league_filter != 'All':" in line and "if league_filter ==" in line:
        # We have a messed up line. Let's skip it and insert the correct logic.
        new_lines.append("    if league_filter != 'All':\n")
        
        # If it's the start of the block, it's followed by some logic.
        if "where_d.append" in line or "where_b.append" in line or "where_f.append" in line:
            var = "where_d" if "where_d" in line else ("where_b" if "where_b" in line else "where_f")
            param_var = "params_d" if "params_d" in line else ("params_b" if "params_b" in line else "params_f")
            
            new_lines.append(f"""        if league_filter == 'Series':
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
            where_cricsheet.append("1=0")\n""")
            # Skip the next few lines that belonged to the old block until we hit `if venue_filter` or `if year_filter`
            skip = True
    elif "if league_filter != 'All':" in line and not skip:
        # Normal line
        new_lines.append(line)
        # But wait, did I mess up other places?
        # The syntax error was `if league_filter != 'All':` with NOTHING after it.
        # Let's just do a clean rewrite!
    elif line.strip() == "if league_filter == 'Series':" and lines[i-1].strip() == "if league_filter != 'All':":
        # The previous line was an empty if block!
        pass # It's part of the block
    else:
        if skip:
            if "if venue_filter" in line or "if year_filter" in line or "if opponent_filter" in line:
                skip = False
                new_lines.append(line)
        else:
            new_lines.append(line)

with open('app.py', 'w') as f:
    f.writelines(new_lines)
print("done")
