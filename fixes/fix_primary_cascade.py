import re

def fix_cascading(filepath, prefix):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add the formatSelect and leagueSelect updates back to fetchFilters, but only if sourceId === null
    insertion = f"""
                        if (sourceId === null && formatSelect && filters.formats) {{
                            formatSelect.innerHTML = '<option value="All">All Formats</option>' + filters.formats.map(f => `<option value="${{f}}">${{f}}</option>`).join('');
                            if (filters.formats.includes(currentFormat)) formatSelect.value = currentFormat;
                        }}
                        if (sourceId === null && leagueSelect && filters.leagues) {{
                            leagueSelect.innerHTML = '<option value="All">All Leagues</option>' + filters.leagues.map(l => `<option value="${{l}}">${{l}}</option>`).join('');
                            if (filters.leagues.includes(currentLeague)) leagueSelect.value = currentLeague;
                        }}
"""
    # Find where to insert it: right before the venSelect update
    content = re.sub(r"(if \(sourceId !== 'filterVenue')", insertion + r"                        \1", content)

    # 2. In init(), make sure fetchFilters() is called if currentAthleteId is set
    # The existing code is:
    # if (currentAthleteId) {
    #     const bRes = await fetch(`/api/athlete/${currentAthleteId}`);
    #     if (bRes.ok) document.getElementById('athleteName').textContent = (await bRes.json()).full_name;
    #     fetchStats();
    # }
    
    # We want to change fetchStats(); to fetchFilters(); fetchStats();
    # Or rather, `await fetchBatterFilters(); fetchStats();`
    
    # Actually, we can just replace `fetchStats();` with `await fetch{prefix}Filters(); fetchStats();`
    if f"await fetch{prefix}Filters();" not in content:
        content = content.replace("fetchStats();", f"await fetch{prefix}Filters();\n                        fetchStats();")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

fix_cascading('templates/batter.html', 'Batter')
fix_cascading('templates/bowler.html', 'Bowler')
fix_cascading('templates/faceoff.html', 'Faceoff')

print("Fixed cascading for Format and League dropdowns!")
