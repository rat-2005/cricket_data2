import os

def update_html(filename, api_name):
    with open(f"d:/cricket/fresh_data/templates/{filename}", "r", encoding="utf-8") as f:
        content = f.read()
        
    js_addition = f"""
            async function fetchDynamicFilters(sourceId = null) {{
                const formatSelect = document.getElementById('filterFormat');
                const leagueSelect = document.getElementById('filterLeague');
                const venSelect = document.getElementById('filterVenue');
                const phaseSelect = document.getElementById('filterPhase');
                
                const currentFormat = formatSelect.value || 'All';
                const currentLeague = leagueSelect.value || 'All';
                const currentVenue = venSelect.value || 'All';
                const currentPhase = phaseSelect.value || 'All';
                
                try {{
                    const params = new URLSearchParams({{
                        id: athleteId,
                        format: currentFormat,
                        league: currentLeague,
                        venue: currentVenue,
                        phase: currentPhase
                    }});
                    
                    const filterRes = await fetch(`/api/{api_name}?${{params.toString()}}`);
                    if(filterRes.ok) {{
                        const filters = await filterRes.json();
                        
                        if (sourceId !== 'filterFormat') {{
                            formatSelect.innerHTML = '<option value="All">All Formats</option>' + filters.formats.map(f => `<option value="${{f}}">${{f}}</option>`).join('');
                            if (filters.formats.includes(currentFormat)) formatSelect.value = currentFormat;
                        }}
                        
                        if (sourceId !== 'filterLeague') {{
                            leagueSelect.innerHTML = '<option value="All">All Leagues</option>' + filters.leagues.map(l => `<option value="${{l}}">${{l}}</option>`).join('');
                            if (filters.leagues.includes(currentLeague)) leagueSelect.value = currentLeague;
                        }}
                        
                        if (sourceId !== 'filterVenue') {{
                            venSelect.innerHTML = '<option value="All">All Venues</option>' + filters.venues.map(v => `<option value="${{v}}">${{v}}</option>`).join('');
                            if (filters.venues.includes(currentVenue)) venSelect.value = currentVenue;
                        }}
                    }}
                }} catch(e) {{
                    console.error("Failed to fetch dynamic filters", e);
                }}
            }}

            document.getElementById('filterFormat').addEventListener('change', () => fetchDynamicFilters('filterFormat'));
            document.getElementById('filterLeague').addEventListener('change', () => fetchDynamicFilters('filterLeague'));
            document.getElementById('filterVenue').addEventListener('change', () => fetchDynamicFilters('filterVenue'));
            document.getElementById('filterPhase').addEventListener('change', () => fetchDynamicFilters('filterPhase'));
"""

    if "fetchDynamicFilters" not in content:
        # replace the static filter logic in init()
        old_init_logic = """
                    // Fetch filters
                    const filterRes = await fetch(`/api/filters`);
                    if(filterRes.ok) {
                        const filters = await filterRes.json();
                        
                        const formatSelect = document.getElementById('filterFormat');
                        formatSelect.innerHTML += filters.formats.map(f => `<option value="${f}">${f}</option>`).join('');
                        
                        const leagueSelect = document.getElementById('filterLeague');
                        leagueSelect.innerHTML += filters.leagues.map(l => `<option value="${l}">${l}</option>`).join('');
                        
                        const oppSelect = document.getElementById('filterOpponent');
                        oppSelect.innerHTML += filters.opponents.map(o => `<option value="${o}">${o}</option>`).join('');
                        
                        const venSelect = document.getElementById('filterVenue');
                        venSelect.innerHTML += filters.venues.map(v => `<option value="${v}">${v}</option>`).join('');
                    }"""
        
        new_init_logic = """
                    // Initialize dynamic filters
                    await fetchDynamicFilters();
                    
                    // Also fetch opponents globally (since opponent isn't dynamic in backend yet)
                    const globalRes = await fetch('/api/filters');
                    if (globalRes.ok) {
                        const globalData = await globalRes.json();
                        const oppSelect = document.getElementById('filterOpponent');
                        oppSelect.innerHTML = '<option value="All">All Opponents</option>' + globalData.opponents.map(o => `<option value="${o}">${o}</option>`).join('');
                    }
        """
        
        content = content.replace(old_init_logic, new_init_logic)
        content = content.replace("async function fetchStats() {", js_addition + "\n            async function fetchStats() {")
        
        with open(f"d:/cricket/fresh_data/templates/{filename}", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {filename}")
    else:
        print(f"Already updated {filename}")

update_html("batter.html", "batter_filters")
update_html("bowler.html", "bowler_filters")
