import re

with open('templates/batter.html', 'r') as f:
    content = f.read()

# 1. Update the HTML layout to include the 6 new filters
new_filters_html = """
                <div style="flex: 1; min-width: 150px;">
                    <label id="labelOpponent" style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 0.5rem; display: block; font-weight: 600; text-transform: uppercase;">Opponent</label>
                    <select id="filterOpponent" style="width: 100%; padding: 0.8rem 1rem; background: rgba(0, 0, 0, 0.4); border: 1px solid var(--glass-border); border-radius: 12px; color: var(--text-primary); font-family: 'Inter', sans-serif; font-size: 0.95rem;"><option value="All">All Opponents</option></select>
                </div>

                <div style="flex: 1; min-width: 150px;">
                    <label id="labelBowlingType" style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 0.5rem; display: block; font-weight: 600; text-transform: uppercase;">Bowling Type</label>
                    <select id="filterBowlingType" style="width: 100%; padding: 0.8rem 1rem; background: rgba(0, 0, 0, 0.4); border: 1px solid var(--glass-border); border-radius: 12px; color: var(--text-primary); font-family: 'Inter', sans-serif; font-size: 0.95rem;"><option value="All">All Types</option></select>
                </div>

                <div style="flex: 1; min-width: 150px;">
                    <label id="labelInnings" style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 0.5rem; display: block; font-weight: 600; text-transform: uppercase;">Innings</label>
                    <select id="filterInnings" style="width: 100%; padding: 0.8rem 1rem; background: rgba(0, 0, 0, 0.4); border: 1px solid var(--glass-border); border-radius: 12px; color: var(--text-primary); font-family: 'Inter', sans-serif; font-size: 0.95rem;">
                        <option value="All">All Innings</option>
                        <option value="1">1st Innings</option>
                        <option value="2">2nd Innings</option>
                        <option value="3">3rd Innings</option>
                        <option value="4">4th Innings</option>
                    </select>
                </div>

                <div style="flex: 1; min-width: 150px;">
                    <label id="labelResult" style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 0.5rem; display: block; font-weight: 600; text-transform: uppercase;">Match Result</label>
                    <select id="filterResult" style="width: 100%; padding: 0.8rem 1rem; background: rgba(0, 0, 0, 0.4); border: 1px solid var(--glass-border); border-radius: 12px; color: var(--text-primary); font-family: 'Inter', sans-serif; font-size: 0.95rem;">
                        <option value="All">All Results</option>
                        <option value="Won">Won</option>
                        <option value="Lost">Lost</option>
                    </select>
                </div>

                <div style="flex: 1; min-width: 150px;">
                    <label id="labelYear" style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 0.5rem; display: block; font-weight: 600; text-transform: uppercase;">Year</label>
                    <select id="filterYear" style="width: 100%; padding: 0.8rem 1rem; background: rgba(0, 0, 0, 0.4); border: 1px solid var(--glass-border); border-radius: 12px; color: var(--text-primary); font-family: 'Inter', sans-serif; font-size: 0.95rem;"><option value="All">All Years</option></select>
                </div>

                <div style="flex: 1; min-width: 150px;">
                    <label id="labelRecent" style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 0.5rem; display: block; font-weight: 600; text-transform: uppercase;">Recent Matches</label>
                    <select id="filterRecent" style="width: 100%; padding: 0.8rem 1rem; background: rgba(0, 0, 0, 0.4); border: 1px solid var(--glass-border); border-radius: 12px; color: var(--text-primary); font-family: 'Inter', sans-serif; font-size: 0.95rem;">
                        <option value="All">All Matches</option>
                        <option value="5">Last 5 Matches</option>
                        <option value="10">Last 10 Matches</option>
                        <option value="20">Last 20 Matches</option>
                    </select>
                </div>
"""

# Insert right before the analyze button div
target_ui = """                <div style="flex: 0 0 auto; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; gap: 0.5rem;">"""
content = content.replace(target_ui, new_filters_html + '\n' + target_ui)


# 2. Update fetchBatterFilters
js_fetch_filters_old = """            async function fetchBatterFilters(sourceId = null) {
                if (!currentAthleteId) return;

                const formatSelect = document.getElementById('filterFormat');
                const leagueSelect = document.getElementById('filterLeague');
                const venSelect = document.getElementById('filterVenue');

                const currentFormat = formatSelect.value || 'All';
                const currentLeague = leagueSelect.value || 'All';
                const currentVenue = venSelect.value || 'All';

                // Show local loaders on labels
                const formatLabel = document.getElementById('labelFormat');
                const leagueLabel = document.getElementById('labelLeague');
                const venueLabel = document.getElementById('labelVenue');

                if (formatLabel) formatLabel.innerHTML = 'Format <i class="fas fa-spinner fa-spin" style="margin-left: 5px; color: var(--accent-blue);"></i>';
                if (leagueLabel) leagueLabel.innerHTML = 'League <i class="fas fa-spinner fa-spin" style="margin-left: 5px; color: var(--accent-blue);"></i>';
                if (venueLabel) venueLabel.innerHTML = 'Venue <i class="fas fa-spinner fa-spin" style="margin-left: 5px; color: var(--accent-blue);"></i>';

                try {
                    const params = new URLSearchParams({
                        id: currentAthleteId, format: currentFormat, league: currentLeague, venue: currentVenue
                    });

                    const filterRes = await fetch(`/api/batter_filters?${params.toString()}`);
                    if(filterRes.ok) {
                        const filters = await filterRes.json();
                        if (sourceId !== 'filterFormat') {
                            formatSelect.innerHTML = '<option value="All">All Formats</option>' + filters.formats.map(f => `<option value="${f}">${f}</option>`).join('');
                            if (filters.formats.includes(currentFormat)) formatSelect.value = currentFormat;
                        }
                        if (sourceId !== 'filterLeague') {
                            leagueSelect.innerHTML = '<option value="All">All Leagues</option>' + filters.leagues.map(l => `<option value="${l}">${l}</option>`).join('');
                            if (filters.leagues.includes(currentLeague)) leagueSelect.value = currentLeague;
                        }
                        if (sourceId !== 'filterVenue') {
                            venSelect.innerHTML = '<option value="All">All Venues</option>' + filters.venues.map(v => `<option value="${v}">${v}</option>`).join('');
                            if (filters.venues.includes(currentVenue)) venSelect.value = currentVenue;
                        }
                    }
                    if (formatLabel) formatLabel.innerHTML = 'Format';
                    if (leagueLabel) leagueLabel.innerHTML = 'League';
                    if (venueLabel) venueLabel.innerHTML = 'Venue';
                } catch(e) {
                    console.error(e);
                    if (formatLabel) formatLabel.innerHTML = 'Format';
                    if (leagueLabel) leagueLabel.innerHTML = 'League';
                    if (venueLabel) venueLabel.innerHTML = 'Venue';
                }
            }

            document.getElementById('filterFormat').addEventListener('change', () => fetchBatterFilters('filterFormat'));
            document.getElementById('filterLeague').addEventListener('change', () => fetchBatterFilters('filterLeague'));
            document.getElementById('filterVenue').addEventListener('change', () => fetchBatterFilters('filterVenue'));"""

js_fetch_filters_new = """            async function fetchBatterFilters(sourceId = null) {
                if (!currentAthleteId) return;

                const formatSelect = document.getElementById('filterFormat');
                const leagueSelect = document.getElementById('filterLeague');
                const venSelect = document.getElementById('filterVenue');
                const oppSelect = document.getElementById('filterOpponent');
                const bowlSelect = document.getElementById('filterBowlingType');
                const yearSelect = document.getElementById('filterYear');

                const currentFormat = formatSelect.value || 'All';
                const currentLeague = leagueSelect.value || 'All';
                const currentVenue = venSelect.value || 'All';
                const currentOpp = oppSelect.value || 'All';
                const currentBowl = bowlSelect.value || 'All';
                const currentYear = yearSelect.value || 'All';

                // Show local loaders on labels
                const formatLabel = document.getElementById('labelFormat');
                const leagueLabel = document.getElementById('labelLeague');
                const venueLabel = document.getElementById('labelVenue');
                const oppLabel = document.getElementById('labelOpponent');
                const bowlLabel = document.getElementById('labelBowlingType');
                const yearLabel = document.getElementById('labelYear');

                if (formatLabel) formatLabel.innerHTML = 'Format <i class="fas fa-spinner fa-spin" style="margin-left: 5px; color: var(--accent-blue);"></i>';
                if (leagueLabel) leagueLabel.innerHTML = 'League <i class="fas fa-spinner fa-spin" style="margin-left: 5px; color: var(--accent-blue);"></i>';
                if (venueLabel) venueLabel.innerHTML = 'Venue <i class="fas fa-spinner fa-spin" style="margin-left: 5px; color: var(--accent-blue);"></i>';
                if (oppLabel) oppLabel.innerHTML = 'Opponent <i class="fas fa-spinner fa-spin" style="margin-left: 5px; color: var(--accent-blue);"></i>';
                if (bowlLabel) bowlLabel.innerHTML = 'Bowling Type <i class="fas fa-spinner fa-spin" style="margin-left: 5px; color: var(--accent-blue);"></i>';
                if (yearLabel) yearLabel.innerHTML = 'Year <i class="fas fa-spinner fa-spin" style="margin-left: 5px; color: var(--accent-blue);"></i>';

                try {
                    const params = new URLSearchParams({
                        id: currentAthleteId, format: currentFormat, league: currentLeague, venue: currentVenue,
                        opponent: currentOpp, bowling_type: currentBowl, innings: document.getElementById('filterInnings').value || 'All',
                        result: document.getElementById('filterResult').value || 'All', year: currentYear,
                        recent: document.getElementById('filterRecent').value || 'All', phase: document.getElementById('filterPhase').value || 'All'
                    });

                    const filterRes = await fetch(`/api/batter_filters?${params.toString()}`);
                    if(filterRes.ok) {
                        const filters = await filterRes.json();
                        if (sourceId !== 'filterFormat') {
                            formatSelect.innerHTML = '<option value="All">All Formats</option>' + filters.formats.map(f => `<option value="${f}">${f}</option>`).join('');
                            if (filters.formats.includes(currentFormat)) formatSelect.value = currentFormat;
                        }
                        if (sourceId !== 'filterLeague') {
                            leagueSelect.innerHTML = '<option value="All">All Leagues</option>' + filters.leagues.map(l => `<option value="${l}">${l}</option>`).join('');
                            if (filters.leagues.includes(currentLeague)) leagueSelect.value = currentLeague;
                        }
                        if (sourceId !== 'filterVenue') {
                            venSelect.innerHTML = '<option value="All">All Venues</option>' + filters.venues.map(v => `<option value="${v}">${v}</option>`).join('');
                            if (filters.venues.includes(currentVenue)) venSelect.value = currentVenue;
                        }
                        if (sourceId !== 'filterOpponent' && filters.opponents) {
                            oppSelect.innerHTML = '<option value="All">All Opponents</option>' + filters.opponents.map(o => `<option value="${o}">${o}</option>`).join('');
                            if (filters.opponents.includes(currentOpp)) oppSelect.value = currentOpp;
                        }
                        if (sourceId !== 'filterBowlingType' && filters.bowling_types) {
                            bowlSelect.innerHTML = '<option value="All">All Types</option>' + filters.bowling_types.map(b => `<option value="${b}">${b}</option>`).join('');
                            if (filters.bowling_types.includes(currentBowl)) bowlSelect.value = currentBowl;
                        }
                        if (sourceId !== 'filterYear' && filters.years) {
                            yearSelect.innerHTML = '<option value="All">All Years</option>' + filters.years.map(y => `<option value="${y}">${y}</option>`).join('');
                            if (filters.years.includes(parseInt(currentYear))) yearSelect.value = currentYear;
                        }
                    }
                } catch(e) {
                    console.error(e);
                } finally {
                    if (formatLabel) formatLabel.innerHTML = 'Format';
                    if (leagueLabel) leagueLabel.innerHTML = 'League';
                    if (venueLabel) venueLabel.innerHTML = 'Venue';
                    if (oppLabel) oppLabel.innerHTML = 'Opponent';
                    if (bowlLabel) bowlLabel.innerHTML = 'Bowling Type';
                    if (yearLabel) yearLabel.innerHTML = 'Year';
                }
            }

            document.getElementById('filterFormat').addEventListener('change', () => fetchBatterFilters('filterFormat'));
            document.getElementById('filterLeague').addEventListener('change', () => fetchBatterFilters('filterLeague'));
            document.getElementById('filterVenue').addEventListener('change', () => fetchBatterFilters('filterVenue'));
            document.getElementById('filterOpponent').addEventListener('change', () => fetchBatterFilters('filterOpponent'));
            document.getElementById('filterBowlingType').addEventListener('change', () => fetchBatterFilters('filterBowlingType'));
            document.getElementById('filterYear').addEventListener('change', () => fetchBatterFilters('filterYear'));
            document.getElementById('filterInnings').addEventListener('change', () => fetchBatterFilters('filterInnings'));
            document.getElementById('filterResult').addEventListener('change', () => fetchBatterFilters('filterResult'));
            document.getElementById('filterRecent').addEventListener('change', () => fetchBatterFilters('filterRecent'));
            document.getElementById('filterPhase').addEventListener('change', () => fetchBatterFilters('filterPhase'));
"""

content = content.replace(js_fetch_filters_old, js_fetch_filters_new)

# 3. Update fetchStats
js_fetch_stats_old = """                const baseParams = new URLSearchParams({
                    id: currentAthleteId,
                    league: document.getElementById('filterLeague').value,
                    phase: document.getElementById('filterPhase').value,
                    venue: document.getElementById('filterVenue').value
                });"""

js_fetch_stats_new = """                const baseParams = new URLSearchParams({
                    id: currentAthleteId,
                    league: document.getElementById('filterLeague').value,
                    phase: document.getElementById('filterPhase').value,
                    venue: document.getElementById('filterVenue').value,
                    opponent: document.getElementById('filterOpponent').value,
                    bowling_type: document.getElementById('filterBowlingType').value,
                    innings: document.getElementById('filterInnings').value,
                    result: document.getElementById('filterResult').value,
                    year: document.getElementById('filterYear').value,
                    recent: document.getElementById('filterRecent').value
                });"""

content = content.replace(js_fetch_stats_old, js_fetch_stats_new)

with open('templates/batter.html', 'w') as f:
    f.write(content)
print("Updated batter.html successfully!")
