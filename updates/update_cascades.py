import re

def update_html_filters(filepath, prefix):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. We replace the fetchFilters function
    new_func = f"""async function fetch{prefix}Filters(sourceId = null) {{
                let currentId = '';
                if ('{prefix}' === 'Faceoff') {{
                    if (!currentBatterId || !currentBowlerId) return;
                }} else {{
                    if (!currentAthleteId) return;
                    currentId = currentAthleteId;
                }}
                
                const formatSelect = document.getElementById('filterFormat');
                const leagueSelect = document.getElementById('filterLeague');
                const venSelect = document.getElementById('filterVenue');
                const oppSelect = document.getElementById('filterOpponent');
                const bowlSelect = document.getElementById('filterBowlingType');
                const yearSelect = document.getElementById('filterYear');
                // phase, innings, result, recent are static or independent, but we send them
                
                const currentFormat = formatSelect ? formatSelect.value || 'All' : 'All';
                const currentLeague = leagueSelect ? leagueSelect.value || 'All' : 'All';
                const currentVenue = venSelect ? venSelect.value || 'All' : 'All';
                const currentOpp = oppSelect ? oppSelect.value || 'All' : 'All';
                const currentBowl = bowlSelect ? bowlSelect.value || 'All' : 'All';
                const currentYear = yearSelect ? yearSelect.value || 'All' : 'All';
                const currentInnings = document.getElementById('filterInnings') ? document.getElementById('filterInnings').value || 'All' : 'All';
                const currentResult = document.getElementById('filterResult') ? document.getElementById('filterResult').value || 'All' : 'All';
                const currentPhase = document.getElementById('filterPhase') ? document.getElementById('filterPhase').value || 'All' : 'All';
                const currentRecent = document.getElementById('filterRecent') ? document.getElementById('filterRecent').value || 'All' : 'All';
                
                try {{
                    let params;
                    if ('{prefix}' === 'Faceoff') {{
                        params = new URLSearchParams({{
                            batter_id: currentBatterId, bowler_id: currentBowlerId, format: currentFormat, league: currentLeague, venue: currentVenue,
                            opponent: currentOpp, bowling_type: currentBowl, innings: currentInnings, result: currentResult, year: currentYear, phase: currentPhase, recent: currentRecent
                        }});
                    }} else {{
                        params = new URLSearchParams({{
                            id: currentId, format: currentFormat, league: currentLeague, venue: currentVenue,
                            opponent: currentOpp, bowling_type: currentBowl, innings: currentInnings, result: currentResult, year: currentYear, phase: currentPhase, recent: currentRecent
                        }});
                    }}
                    
                    const endpoint = '{prefix}' === 'Batter' ? '/api/batter_filters' : ('{prefix}' === 'Bowler' ? '/api/bowler_filters' : '/api/faceoff_filters');
                    const filterRes = await fetch(`${{endpoint}}?${{params.toString()}}`);
                    
                    if(filterRes.ok) {{
                        const filters = await filterRes.json();
                        
                        if (sourceId !== 'filterFormat' && formatSelect && filters.formats) {{
                            formatSelect.innerHTML = '<option value="All">All Formats</option>' + filters.formats.map(f => `<option value="${{f}}">${{f}}</option>`).join('');
                            if (filters.formats.includes(currentFormat)) formatSelect.value = currentFormat;
                        }}
                        if (sourceId !== 'filterLeague' && leagueSelect && filters.leagues) {{
                            leagueSelect.innerHTML = '<option value="All">All Leagues</option>' + filters.leagues.map(l => `<option value="${{l}}">${{l}}</option>`).join('');
                            if (filters.leagues.includes(currentLeague)) leagueSelect.value = currentLeague;
                        }}
                        if (sourceId !== 'filterVenue' && venSelect && filters.venues) {{
                            venSelect.innerHTML = '<option value="All">All Venues</option>' + filters.venues.map(v => `<option value="${{v}}">${{v}}</option>`).join('');
                            if (filters.venues.includes(currentVenue)) venSelect.value = currentVenue;
                        }}
                        if (sourceId !== 'filterOpponent' && oppSelect && filters.opponents) {{
                            oppSelect.innerHTML = '<option value="All">All Opponents</option>' + filters.opponents.map(o => `<option value="${{o}}">${{o}}</option>`).join('');
                            if (filters.opponents.includes(currentOpp)) oppSelect.value = currentOpp;
                        }}
                        if (sourceId !== 'filterBowlingType' && bowlSelect && filters.bowling_types) {{
                            bowlSelect.innerHTML = '<option value="All">All Types</option>' + filters.bowling_types.map(b => `<option value="${{b}}">${{b}}</option>`).join('');
                            if (filters.bowling_types.includes(currentBowl)) bowlSelect.value = currentBowl;
                        }}
                        if (sourceId !== 'filterYear' && yearSelect && filters.years) {{
                            yearSelect.innerHTML = '<option value="All">All Years</option>' + filters.years.map(y => `<option value="${{y}}">${{y}}</option>`).join('');
                            if (filters.years.includes(parseInt(currentYear)) || filters.years.includes(currentYear)) yearSelect.value = currentYear;
                        }}
                    }}
                }} catch(e) {{ 
                    console.error(e); 
                }}
            }}"""

    # We need to replace the old fetchFilters function
    regex = rf"async function fetch{prefix}Filters\(sourceId = null\) {{.*?}} catch\(e\) {{ \n? *console\.error\(e\);(?:.*?)?\n? *}}\n? *}}"
    content = re.sub(regex, new_func, content, flags=re.DOTALL)
    
    # 2. Add event listeners for the new fields if they don't exist
    listeners = f"""            document.getElementById('filterFormat').addEventListener('change', () => fetch{prefix}Filters('filterFormat'));
            document.getElementById('filterLeague').addEventListener('change', () => fetch{prefix}Filters('filterLeague'));
            document.getElementById('filterVenue').addEventListener('change', () => fetch{prefix}Filters('filterVenue'));
            if(document.getElementById('filterOpponent')) document.getElementById('filterOpponent').addEventListener('change', () => fetch{prefix}Filters('filterOpponent'));
            if(document.getElementById('filterBowlingType')) document.getElementById('filterBowlingType').addEventListener('change', () => fetch{prefix}Filters('filterBowlingType'));
            if(document.getElementById('filterYear')) document.getElementById('filterYear').addEventListener('change', () => fetch{prefix}Filters('filterYear'));
            if(document.getElementById('filterInnings')) document.getElementById('filterInnings').addEventListener('change', () => fetch{prefix}Filters('filterInnings'));
            if(document.getElementById('filterResult')) document.getElementById('filterResult').addEventListener('change', () => fetch{prefix}Filters('filterResult'));
            if(document.getElementById('filterPhase')) document.getElementById('filterPhase').addEventListener('change', () => fetch{prefix}Filters('filterPhase'));
            if(document.getElementById('filterRecent')) document.getElementById('filterRecent').addEventListener('change', () => fetch{prefix}Filters('filterRecent'));"""
            
    # Replace existing listeners
    old_listeners_regex = rf"document\.getElementById\('filterFormat'\)\.addEventListener\('change', \(\) => fetch{prefix}Filters\('filterFormat'\)\);\s*document\.getElementById\('filterLeague'\)\.addEventListener\('change', \(\) => fetch{prefix}Filters\('filterLeague'\)\);\s*document\.getElementById\('filterVenue'\)\.addEventListener\('change', \(\) => fetch{prefix}Filters\('filterVenue'\)\);"
    content = re.sub(old_listeners_regex, listeners, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

update_html_filters('templates/batter.html', 'Batter')
update_html_filters('templates/bowler.html', 'Bowler')
update_html_filters('templates/faceoff.html', 'Faceoff')

print("Updated HTML files for full cascading")
