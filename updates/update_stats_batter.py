import re

with open('app.py', 'r') as f:
    content = f.read()

stats_args_target = """    fmt = request.args.get('format', 'All')
    league = request.args.get('league', 'All')
    opponent = request.args.get('opponent', 'All')
    phase = request.args.get('phase', 'All')
    venue = request.args.get('venue', 'All')"""

stats_args_replacement = """    fmt = request.args.get('format', 'All')
    league = request.args.get('league', 'All')
    opponent = request.args.get('opponent', 'All')
    phase = request.args.get('phase', 'All')
    venue = request.args.get('venue', 'All')
    bowling_type = request.args.get('bowling_type', 'All')
    innings = request.args.get('innings', 'All')
    result = request.args.get('result', 'All')
    year = request.args.get('year', 'All')
    recent = request.args.get('recent', 'All')"""

content = content.replace(stats_args_target, stats_args_replacement)


stats_logic_target = """    # NOTE: Opponent team is tricky as we need to join innings/match_teams
    # For now we'll skip opponent team strict filtering in this optimized query
    # unless we join match_teams which slows it down.
        
    where_clause_d = " AND ".join(where_d)"""

stats_logic_replacement = """    if opponent != 'All':
        where_d.append("d.bowling_team_id IN (SELECT id FROM cricket.teams WHERE name = %s)")
        params_d.append(opponent)
        where_cricsheet.append("1=0")
        where_icc.append("1=0")

    if bowling_type != 'All':
        where_d.append("d.bowler_id IN (SELECT id FROM cricket.athletes WHERE bowling_style = %s)")
        params_d.append(bowling_type)
        where_cricsheet.append("1=0")
        where_icc.append("1=0")

    if innings != 'All':
        where_d.append("d.innings = %s")
        params_d.append(innings)
        where_cricsheet.append("d.innings = %s")
        params_cricsheet.append(innings)
        where_icc.append("u.innings = %s")
        params_icc_extra.append(innings)

    if result != 'All':
        if result == 'Won':
            where_d.append("d.competition_id IN (SELECT competition_id FROM cricket.competitors WHERE team_id = d.batting_team_id AND winner = True)")
        elif result == 'Lost':
            where_d.append("d.competition_id IN (SELECT competition_id FROM cricket.competitors WHERE team_id = d.batting_team_id AND winner = False)")
        where_cricsheet.append("1=0")
        where_icc.append("1=0")

    if year != 'All':
        where_d.append("EXTRACT(YEAR FROM c.date) = %s")
        params_d.append(year)
        where_cricsheet.append("EXTRACT(YEAR FROM m.match_date) = %s")
        params_cricsheet.append(year)
        where_icc.append("EXTRACT(YEAR FROM u.match_date) = %s")
        params_icc_extra.append(year)

    if recent != 'All' and recent.isdigit():
        limit = int(recent)
        where_d.append(f"d.competition_id IN (SELECT competition_id FROM cricket.deliveries WHERE batsman_id = %s GROUP BY competition_id ORDER BY MAX(created_at) DESC LIMIT {limit})")
        params_d.append(athlete_id)
        where_cricsheet.append(f"d.match_id IN (SELECT match_id FROM cricket.cricsheet_deliveries WHERE batsman_id = %s GROUP BY match_id ORDER BY MAX(created_at) DESC LIMIT {limit})")
        params_cricsheet.append(athlete_id)
        where_icc.append("1=0")
        
    where_clause_d = " AND ".join(where_d)"""

content = content.replace(stats_logic_target, stats_logic_replacement)

with open('app.py', 'w') as f:
    f.write(content)
print("Updated stats_batter successfully!")
