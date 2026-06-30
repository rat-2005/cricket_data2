
            let currentAthleteId = "{{ athlete_id or '' }}";
            let heatmapChartInstance = null;
            let wicketChartInstance = null;
            let paceChartInstance = null;
            
            Chart.defaults.color = '#94a3b8';
            Chart.defaults.font.family = "'Inter', sans-serif";
            
            async function init() {
                try {
                    const filterRes = await fetch(`/api/filters`);
                    if(filterRes.ok) {
                        const filters = await filterRes.json();
                        const formatSelect = document.getElementById('filterFormat');
                        formatSelect.innerHTML += filters.formats.map(f => `<option value="${f}">${f}</option>`).join('');
                        const leagueSelect = document.getElementById('filterLeague');
                        leagueSelect.innerHTML += filters.leagues.map(l => `<option value="${l}">${l}</option>`).join('');
                        const venSelect = document.getElementById('filterVenue');
                        venSelect.innerHTML += filters.venues.map(v => `<option value="${v}">${v}</option>`).join('');
                    }
                    
                    if (currentAthleteId) {
                        const bRes = await fetch(`/api/athlete/${currentAthleteId}`);
                        if (bRes.ok) document.getElementById('athleteName').textContent = (await bRes.json()).full_name;
                        await fetchBowlerFilters();
                        fetchStats();
                    }
                } catch(e) { console.error("Init failed", e); }
            }
            
            async function fetchBowlerFilters(sourceId = null) {
                let currentId = '';
                if ('Bowler' === 'Faceoff') {
                    if (!currentBatterId || !currentBowlerId) return;
                } else {
                    if (!currentAthleteId) return;
                    currentId = currentAthleteId;
                }
                
                const formatSelect = document.getElementById('filterFormat');
                const leagueSelect = document.getElementById('filterLeague');
                const venSelect = document.getElementById('filterVenue');
                const oppSelect = document.getElementById('filterOpponent');
                const batSelect = document.getElementById('filterBattingType');
                const yearSelect = document.getElementById('filterYear');
                
                const currentFormat = getFilterVal('filterFormat'); const format_not = getFilterNot('filterFormat');
                const currentLeague = getFilterVal('filterLeague'); const league_not = getFilterNot('filterLeague');
                const currentVenue = getFilterVal('filterVenue'); const venue_not = getFilterNot('filterVenue');
                const currentOpp = getFilterVal('filterOpponent'); const opponent_not = getFilterNot('filterOpponent');
                const currentBowl = getFilterVal('filterBowlingType'); const bowling_type_not = getFilterNot('filterBowlingType');
                const currentYear = getFilterVal('filterYear'); const year_not = getFilterNot('filterYear');
                const currentInnings = getFilterVal('filterInnings'); const innings_not = getFilterNot('filterInnings');
                const currentResult = getFilterVal('filterResult'); const result_not = getFilterNot('filterResult');
                const currentPhase = getFilterVal('filterPhase'); const phase_not = getFilterNot('filterPhase');
                const currentRecent = getFilterVal('filterRecent'); const recent_not = getFilterNot('filterRecent');
                const currentWicket = getFilterVal('filterWicketType'); const wicket_type_not = getFilterNot('filterWicketType');
                const currentPitchLength = getFilterVal('filterPitchLength'); const pitch_length_not = getFilterNot('filterPitchLength');
                const currentPitchLine = getFilterVal('filterPitchLine'); const pitch_line_not = getFilterNot('filterPitchLine');
                const currentShotType = getFilterVal('filterShotType'); const shot_type_not = getFilterNot('filterShotType');
                
                try {
                    document.getElementById('loadingState').style.display = 'flex';
                    let params;
                    if ('Bowler' === 'Faceoff') {
                        params = new URLSearchParams({
                            batter_id: currentBatterId, bowler_id: currentBowlerId, format: currentFormat, league: currentLeague, venue: currentVenue,
                            opponent: currentOpp, batting_type: currentBat, innings: currentInnings, result: currentResult, year: currentYear, phase: currentPhase, recent: currentRecent,
                            wicket_type: currentWicket, pitch_length: currentPitchLength, pitch_line: currentPitchLine, shot_type: currentShotType
                        });
                    } else {
                        params = new URLSearchParams({
                            id: currentId, format: currentFormat, league: currentLeague, venue: currentVenue,
                            opponent: currentOpp, batting_type: currentBat, innings: currentInnings, result: currentResult, year: currentYear, phase: currentPhase, recent: currentRecent,
                            wicket_type: currentWicket, pitch_length: currentPitchLength, pitch_line: currentPitchLine, shot_type: currentShotType
                        });
                    }
                    
                    const endpoint = 'Bowler' === 'Batter' ? '/api/batter_filters' : ('Bowler' === 'Bowler' ? '/api/bowler_filters' : '/api/faceoff_filters');
                    const filterRes = await fetch(`${endpoint}?${params.toString()}`);
                    
                    if(filterRes.ok) {
                        const filters = await filterRes.json();
                        
                                                                        
                        if (sourceId !== 'filterFormat' && formatSelect && filters.formats) {
                            formatSelect.innerHTML = '<option value="All">All Formats</option>' + filters.formats.map(f => `<option value="${f}">${f}</option>`).join('');
                            setFilterVal('filterFormat', currentFormat);
                        }
                        if (sourceId !== 'filterLeague' && leagueSelect && filters.leagues) {
                            leagueSelect.innerHTML = '<option value="All">All Leagues</option>' + filters.leagues.map(l => `<option value="${l}">${l}</option>`).join('');
                            setFilterVal('filterLeague', currentLeague);
                        }
                        if (sourceId !== 'filterVenue' && venSelect && filters.venues) {
                            venSelect.innerHTML = '<option value="All">All Venues</option>' + filters.venues.map(v => `<option value="${v}">${v}</option>`).join('');
                            setFilterVal('filterVenue', currentVenue);
                        }
                        if (sourceId !== 'filterOpponent' && oppSelect && filters.opponents) {
                            oppSelect.innerHTML = '<option value="All">All Opponents</option>' + filters.opponents.map(o => `<option value="${o}">${o}</option>`).join('');
                            setFilterVal('filterOpponent', currentOpp);
                        }
                        if (sourceId !== 'filterBattingType' && batSelect && filters.batting_types) {
                            batSelect.innerHTML = '<option value="All">All Types</option>' + filters.batting_types.map(b => `<option value="${b}">${b}</option>`).join('');
                            if (filters.batting_types.includes(currentBat)) batSelect.value = currentBat;
                        }
                        if (sourceId !== 'filterYear' && yearSelect && filters.years) {
                            yearSelect.innerHTML = '<option value="All">All Years</option>' + filters.years.map(y => `<option value="${y}">${y}</option>`).join('');
                            setFilterVal('filterYear', currentYear);
                        }
                        
                        const inningsSelect = document.getElementById('filterInnings');
                        if (sourceId !== 'filterInnings' && inningsSelect && filters.innings) {
                            inningsSelect.innerHTML = '<option value="All">All Innings</option>' + filters.innings.map(i => `<option value="${i}">Innings ${i}</option>`).join('');
                            setFilterVal('filterInnings', currentInnings);
                        }

                        const resultSelect = document.getElementById('filterResult');
                        if (sourceId !== 'filterResult' && resultSelect && filters.results) {
                            resultSelect.innerHTML = '<option value="All">All Results</option>' + filters.results.map(r => `<option value="${r}">${r}</option>`).join('');
                            setFilterVal('filterResult', currentResult);
                        }

                        const wtSelect = document.getElementById('filterWicketType');
                        if (sourceId !== 'filterWicketType' && wtSelect && filters.wicket_types) {
                            wtSelect.innerHTML = '<option value="All">All Types</option>' + filters.wicket_types.map(w => `<option value="${w}">${w}</option>`).join('');
                            setFilterVal('filterWicketType', currentWicket);
                        }

                        const plSelect = document.getElementById('filterPitchLength');
                        if (sourceId !== 'filterPitchLength' && plSelect && filters.pitch_lengths) {
                            plSelect.innerHTML = '<option value="All">All Lengths</option>' + filters.pitch_lengths.map(p => `<option value="${p}">${p}</option>`).join('');
                            setFilterVal('filterPitchLength', currentPitchLength);
                        }

                        const plnSelect = document.getElementById('filterPitchLine');
                        if (sourceId !== 'filterPitchLine' && plnSelect && filters.pitch_lines) {
                            plnSelect.innerHTML = '<option value="All">All Lines</option>' + filters.pitch_lines.map(p => `<option value="${p}">${p}</option>`).join('');
                            setFilterVal('filterPitchLine', currentPitchLine);
                        }

                        const stSelect = document.getElementById('filterShotType');
                        if (sourceId !== 'filterShotType' && stSelect && filters.shot_types) {
                            stSelect.innerHTML = '<option value="All">All Shots</option>' + filters.shot_types.map(s => `<option value="${s}">${s}</option>`).join('');
                            setFilterVal('filterShotType', currentShotType);
                        }

                        const phaseSelect = document.getElementById('filterPhase');
                        if (sourceId !== 'filterPhase' && phaseSelect && filters.phases) {
                            phaseSelect.innerHTML = '<option value="All">All Phases</option>' + filters.phases.map(p => `<option value="${p}">${p}</option>`).join('');
                            setFilterVal('filterPhase', currentPhase);
                        }
                    }
                } catch(e) { 
                    console.error("Filter fetch failed", e); 
                } finally {
                    document.getElementById('loadingState').style.display = 'none';
                }
            }

            document.getElementById('filterFormat').addEventListener('change', () => fetchBowlerFilters('filterFormat'));
            document.getElementById('filterLeague').addEventListener('change', () => fetchBowlerFilters('filterLeague'));
            document.getElementById('filterVenue').addEventListener('change', () => fetchBowlerFilters('filterVenue'));
            if(document.getElementById('filterOpponent')) document.getElementById('filterOpponent').addEventListener('change', () => fetchBowlerFilters('filterOpponent'));
            if(document.getElementById('filterBattingType')) document.getElementById('filterBattingType').addEventListener('change', () => fetchBowlerFilters('filterBattingType'));
            if(document.getElementById('filterYear')) document.getElementById('filterYear').addEventListener('change', () => fetchBowlerFilters('filterYear'));
            if(document.getElementById('filterInnings')) document.getElementById('filterInnings').addEventListener('change', () => fetchBowlerFilters('filterInnings'));
            if(document.getElementById('filterResult')) document.getElementById('filterResult').addEventListener('change', () => fetchBowlerFilters('filterResult'));
            if(document.getElementById('filterPhase')) document.getElementById('filterPhase').addEventListener('change', () => fetchBowlerFilters('filterPhase'));
            if(document.getElementById('filterRecent')) document.getElementById('filterRecent').addEventListener('change', () => fetchBowlerFilters('filterRecent'));
            if(document.getElementById('filterWicketType')) document.getElementById('filterWicketType').addEventListener('change', () => fetchBowlerFilters('filterWicketType'));
            if(document.getElementById('filterPitchLength')) document.getElementById('filterPitchLength').addEventListener('change', () => fetchBowlerFilters('filterPitchLength'));
            if(document.getElementById('filterPitchLine')) document.getElementById('filterPitchLine').addEventListener('change', () => fetchBowlerFilters('filterPitchLine'));
            if(document.getElementById('filterShotType')) document.getElementById('filterShotType').addEventListener('change', () => fetchBowlerFilters('filterShotType'));


            function getFilterVal(id) {
                const el = document.getElementById(id);
                if (!el) return 'All';
                if (el.hasAttribute('multiple')) {
                    const vals = Array.from(el.selectedOptions).map(o => o.value);
                    return vals.length ? vals : 'All';
                }
                return el.value || 'All';
            }
            function getFilterNot(id) {
                const el = document.getElementById(id);
                return el ? (el.dataset.not === 'true') : false;
            }
            function setFilterVal(id, val) {
                const el = document.getElementById(id);
                if (!el) return;
                if (Array.isArray(val)) {
                    Array.from(el.options).forEach(opt => {
                        opt.selected = val.includes(opt.value);
                    });
                } else {
                    el.value = val;
                }
            }
            function toggleMulti(selectId, btn) {
                const sel = document.getElementById(selectId);
                if (!sel) return;
                if (sel.hasAttribute('multiple')) {
                    sel.removeAttribute('multiple');
                    btn.classList.remove('active-multi');
                } else {
                    sel.setAttribute('multiple', 'multiple');
                    btn.classList.add('active-multi');
                }
            }
            function toggleNot(selectId, btn) {
                const sel = document.getElementById(selectId);
                if (!sel) return;
                if (sel.dataset.not === "true") {
                    sel.dataset.not = "false";
                    btn.classList.remove('active-not');
                } else {
                    sel.dataset.not = "true";
                    btn.classList.add('active-not');
                }
            }
            function setupSearch() {
                const input = document.getElementById('athleteSearch');
                const results = document.getElementById('searchResults');
                let timeout;
                
                input.addEventListener('input', (e) => {
                    const query = e.target.value.trim();
                    clearTimeout(timeout);
                    if (query.length < 1) { results.classList.remove('active'); return; }
                    
                    results.innerHTML = '<div style="padding: 1rem; color: var(--text-secondary); text-align: center;"><i class="fas fa-spinner fa-spin"></i></div>';
                    results.classList.add('active');

                    timeout = setTimeout(async () => {
                        try {
                            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                            const data = await response.json();
                            
                            if(data.length > 0) {
                                results.innerHTML = data.map(p => {
                                    const safeName = (p.full_name || '').replace(/'/g, "\\'");
                                    return `
                                    <div class="search-result-item" onclick="selectPlayer('${p.id}', '${safeName}')">
                                        <div style="font-weight: 600; font-family: 'Outfit'; color: white;">${p.full_name}</div>
                                        <div style="font-size: 0.8rem;">${p.country_code || 'Unknown'}</div>
                                    </div>`;
                                }).join('');
                            } else {
                                results.innerHTML = '<div style="padding: 1rem; text-align: center;">No players found</div>';
                            }
                        } catch (err) { results.innerHTML = '<div style="padding: 1rem; color: #ef4444; text-align: center;">Error</div>'; }
                    }, 300);
                });
                document.addEventListener('click', (e) => {
                    if (!input.contains(e.target) && !results.contains(e.target)) results.classList.remove('active');
                });
            }
            
            function selectPlayer(id, name) {
                currentAthleteId = id;
                document.getElementById('athleteName').textContent = name;
                document.getElementById('athleteProfileLink').href = `/player/${id}`;
                document.getElementById('athleteSearch').value = name;
                document.getElementById('searchResults').classList.remove('active');
                
                fetchBowlerFilters();
                
                const url = new URL(window.location);
                url.searchParams.set('id', id);
                window.history.pushState({}, '', url);
            }
            
            function initCharts(data) {
                // Pitch Heatmap
                renderPitchHeatmap(data.pitch_heatmap);


                // Wicket Types
                const wicketCtx = document.getElementById('wicketChart').getContext('2d');
                if (wicketChartInstance) wicketChartInstance.destroy();
                
                wicketChartInstance = new Chart(wicketCtx, {
                    type: 'bar',
                    data: {
                        labels: Object.keys(data.wicket_data || {}),
                        datasets: [{
                            label: 'Dismissals',
                            data: Object.values(data.wicket_data || {}),
                            backgroundColor: 'rgba(59, 130, 246, 0.8)',
                            borderRadius: 4
                        }]
                    },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { display: false } } } }
                });

                // Pace Profile Curve
                const paceCtx = document.getElementById('paceChart').getContext('2d');
                if (paceChartInstance) paceChartInstance.destroy();
                
                paceChartInstance = new Chart(paceCtx, {
                    type: 'line',
                    data: {
                        labels: Object.keys(data.pace_data || {}),
                        datasets: [{
                            label: 'Deliveries',
                            data: Object.values(data.pace_data || {}),
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.2)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { color: 'rgba(255,255,255,0.05)' } } }, elements: { point: { radius: 0, hitRadius: 10, hoverRadius: 6 } } }
                });
            }

            async function fetchStats() {
                if (!currentAthleteId) return;
                
                document.getElementById('emptyState').style.display = 'none';
document.getElementById('loadingState').style.display = 'flex';
                
                const splitMode = document.getElementById('splitByFormat').checked;
                
                const baseParams = new URLSearchParams({
                    id: currentAthleteId,
                    format: document.getElementById('filterFormat').value,
                    league: document.getElementById('filterLeague').value,
                    phase: document.getElementById('filterPhase').value,
                    venue: document.getElementById('filterVenue').value,
                    opponent: document.getElementById('filterOpponent').value,
                    batting_type: document.getElementById('filterBattingType').value,
                    year: document.getElementById('filterYear').value,
                    innings: document.getElementById('filterInnings').value,
                    result: document.getElementById('filterResult').value,
                    recent: document.getElementById('filterRecent').value,
                    wicket_type: document.getElementById('filterWicketType').value,
                    pitch_length: document.getElementById('filterPitchLength').value,
                    pitch_line: document.getElementById('filterPitchLine').value,
                    shot_type: document.getElementById('filterShotType').value
                });
                
                try {
                    document.getElementById('mainContent').style.display = 'block';
                    
                    if (splitMode) {
                        document.getElementById('chartsRow').style.display = 'none';
                        document.getElementById('statsGrid').className = '';
                        
                        const formats = ['Test', 'ODI', 'T20I', 'T20'];
                        let html = '';
                        
                        for (let fmt of formats) {
                            baseParams.set('format', fmt);
                            const res = await fetch(`/api/stats/bowler?${baseParams.toString()}`);
                            const data = await res.json();
                            
                            if (data.wickets > 0 || data.balls_bowled > 0) {
                                html += `
                                <h3 style="margin-top: 2rem; margin-bottom: 1rem; color: var(--accent-blue); display:flex; align-items:center; gap:0.5rem;"><i class="fas fa-trophy"></i> ${fmt} Breakdown</h3>
                                <div class="bento-grid">
                                    <div class="glass-panel stat-box">
                                        <div class="stat-label">Wickets</div>
                                        <div class="stat-value" style="color: var(--accent-blue); background: none; -webkit-text-fill-color: var(--accent-blue);">${data.wickets}</div>
                                    </div>
                                    <div class="glass-panel stat-box">
                                        <div class="stat-label">Economy</div>
                                        <div class="stat-value small">${data.eco}</div>
                                        <div class="stat-subtext">Runs/Over</div>
                                    </div>
                                    <div class="glass-panel stat-box">
                                        <div class="stat-label">Average</div>
                                        <div class="stat-value small">${data.avg}</div>
                                        <div class="stat-subtext">Runs/Wicket</div>
                                    </div>
                                    <div class="glass-panel stat-box">
                                        <div class="stat-label">Best Bowling</div>
                                        <div class="stat-value" style="font-size: 2rem;">${data.best}</div>
                                    </div>
                                </div>
                                `;
                            }
                        }
                        
                        if (html === '') {
                            html = '<div style="text-align:center; padding: 3rem; color: var(--text-secondary); background: rgba(0,0,0,0.2); border-radius: 12px;"><i class="fas fa-ghost" style="font-size: 2rem; margin-bottom: 1rem; display:block;"></i>No historical data found for the selected filters.</div>';
                        }
                        
                        document.getElementById('statsGrid').innerHTML = html;
                        document.getElementById('loadingState').style.display = 'none';
                        
                    } else {
                        document.getElementById('chartsRow').style.display = 'grid';
                        document.getElementById('statsGrid').className = 'bento-grid';
                        baseParams.set('format', document.getElementById('filterFormat').value);
                        
                        const res = await fetch(`/api/stats/bowler?${baseParams.toString()}`);
                        const data = await res.json();
                        
                        document.getElementById('statsGrid').innerHTML = `
                            <div class="glass-panel stat-box">
                                <div class="stat-label">Wickets</div>
                                <div class="stat-value" style="color: var(--accent-blue); background: none; -webkit-text-fill-color: var(--accent-blue);">${data.wickets}</div>
                            </div>
                            <div class="glass-panel stat-box">
                                <div class="stat-label">Economy</div>
                                <div class="stat-value small">${data.eco}</div>
                                <div class="stat-subtext">Runs/Over</div>
                            </div>
                            <div class="glass-panel stat-box">
                                <div class="stat-label">Average</div>
                                <div class="stat-value small">${data.avg}</div>
                                <div class="stat-subtext">Runs/Wicket</div>
                            </div>
                            <div class="glass-panel stat-box">
                                <div class="stat-label">Best Bowling</div>
                                <div class="stat-value" style="font-size: 2rem;">${data.best}</div>
                            </div>
                        `;
                        
                        initCharts(data);
                        document.getElementById('loadingState').style.display = 'none';
                    }
                    
                } catch(e) {
                    console.error(e);
                    document.getElementById('loadingState').style.display = 'none';
                    document.getElementById('emptyState').style.display = 'block';
                    document.getElementById('emptyState').innerHTML = '<p style="color:var(--accent-red);">Failed to load bowler data.</p>';
                }
            }
            
            function renderPitchHeatmap(heatmapData) {
                const grid = document.getElementById('pitchHeatmapGrid');
                if (!grid) return;
                
                while (grid.children.length > 4) {
                    grid.removeChild(grid.lastChild);
                }
                
                const lengths = ['FULL_TOSS', 'YORKER', 'FULL', 'GOOD_LENGTH', 'SHORT_OF_A_GOOD_LENGTH', 'SHORT'];
                const lengthLabels = ['Full Toss', 'Yorker', 'Full Length', 'Good Length', 'Short of good length', 'Short Length'];
                const lines = ['WIDE_OUTSIDE_OFFSTUMP', 'OUTSIDE_OFFSTUMP', 'ON_THE_STUMPS', 'DOWN_LEG', 'WIDE_DOWN_LEG'];
                
                let maxWickets = 0;
                let maxRuns = 0;
                const map = {};
                if (heatmapData && heatmapData.length) {
                    heatmapData.forEach(d => {
                        if (!map[d.length]) map[d.length] = {};
                        map[d.length][d.line] = d;
                        if (d.wickets > maxWickets) maxWickets = d.wickets;
                        if (d.runs > maxRuns) maxRuns = d.runs;
                    });
                }
                
                const maxWGradient = maxWickets > 0 ? maxWickets : 1;
                const maxRGradient = maxRuns > 0 ? maxRuns : 1;

                for (let r = 0; r < lengths.length; r++) {
                    const labelCell = document.createElement('div');
                    labelCell.className = 'pitch-label';
                    labelCell.textContent = lengthLabels[r];
                    grid.appendChild(labelCell);
                    
                    for (let c = 0; c < lines.length; c++) {
                        const cell = document.createElement('div');
                        cell.className = 'pitch-cell';
                        
                        const cellData = map[lengths[r]] && map[lengths[r]][lines[c]];
                        if (cellData) {
                            if (cellData.wickets > 0) {
                                const intensity = 0.4 + (0.6 * (cellData.wickets / maxWGradient));
                                cell.style.background = `rgba(249, 115, 22, ${intensity})`;
                                cell.style.borderColor = `rgba(249, 115, 22, 0.4)`;
                                cell.textContent = cellData.wickets + 'W';
                            } else if (cellData.runs > 0) {
                                const intensity = 0.1 + (0.3 * (cellData.runs / maxRGradient));
                                cell.style.background = `rgba(59, 130, 246, ${intensity})`;
                                cell.style.borderColor = `rgba(59, 130, 246, 0.2)`;
                            }
                            let tooltipText = `Runs: ${cellData.runs} | Balls: ${cellData.balls} | Wickets: ${cellData.wickets}\n`;
                            if (cellData.runs > 0 && cellData.shots && Object.keys(cellData.shots).length > 0) {
                                tooltipText += `\n-- Runs by Shot --\n`;
                                const sortedShots = Object.entries(cellData.shots).sort((a,b) => b[1] - a[1]);
                                for (const [shot, r] of sortedShots) {
                                    tooltipText += `${shot.charAt(0).toUpperCase() + shot.slice(1)}: ${r}\n`;
                                }
                            }
                            if (cellData.wickets > 0 && cellData.wicket_events && cellData.wicket_events.length > 0) {
                                tooltipText += `\n-- Wickets --\n`;
                                cellData.wicket_events.forEach(w => {
                                    tooltipText += `• ${w.shot} \u2192 ${w.type}\n`;
                                });
                            }
                            // Setup custom tooltip
                            cell.addEventListener('mouseenter', (e) => {
                                cell.style.transform = 'scale(1.15)';
                                cell.style.zIndex = '10';
                                cell.style.boxShadow = '0 10px 15px -3px rgba(0,0,0,0.5)';
                                let tooltip = document.getElementById('heatmap-tooltip');
                                if (!tooltip) {
                                    tooltip = document.createElement('div');
                                    tooltip.id = 'heatmap-tooltip';
                                    tooltip.style.position = 'fixed';
                                    tooltip.style.background = 'rgba(15, 23, 42, 0.95)';
                                    tooltip.style.color = '#f8fafc';
                                    tooltip.style.padding = '12px 16px';
                                    tooltip.style.borderRadius = '8px';
                                    tooltip.style.boxShadow = '0 10px 25px -5px rgba(0, 0, 0, 0.5)';
                                    tooltip.style.border = '1px solid rgba(255, 255, 255, 0.1)';
                                    tooltip.style.pointerEvents = 'none';
                                    tooltip.style.zIndex = '9999';
                                    tooltip.style.fontSize = '12px';
                                    tooltip.style.fontFamily = 'Inter, sans-serif';
                                    tooltip.style.whiteSpace = 'pre-wrap';
                                    tooltip.style.lineHeight = '1.5';
                                    document.body.appendChild(tooltip);
                                }
                                tooltip.style.display = 'block';
                                tooltip.textContent = tooltipText.trim();
                            });
                            cell.addEventListener('mousemove', (e) => {
                                const tooltip = document.getElementById('heatmap-tooltip');
                                if (tooltip) {
                                    tooltip.style.left = (e.clientX + 15) + 'px';
                                    tooltip.style.top = (e.clientY + 15) + 'px';
                                }
                            });
                            cell.addEventListener('mouseleave', (e) => {
                                cell.style.transform = 'scale(1)';
                                cell.style.zIndex = '1';
                                cell.style.boxShadow = 'none';
                                const tooltip = document.getElementById('heatmap-tooltip');
                                if (tooltip) tooltip.style.display = 'none';
                            });
                        } else {
                            cell.addEventListener('mouseenter', (e) => {
                                cell.style.transform = 'scale(1.15)';
                                cell.style.zIndex = '10';
                                cell.style.boxShadow = '0 10px 15px -3px rgba(0,0,0,0.5)';
                                let tooltip = document.getElementById('heatmap-tooltip');
                                if (!tooltip) {
                                    tooltip = document.createElement('div');
                                    tooltip.id = 'heatmap-tooltip';
                                    tooltip.style.position = 'fixed';
                                    tooltip.style.background = 'rgba(15, 23, 42, 0.95)';
                                    tooltip.style.color = '#f8fafc';
                                    tooltip.style.padding = '12px 16px';
                                    tooltip.style.borderRadius = '8px';
                                    tooltip.style.boxShadow = '0 10px 25px -5px rgba(0, 0, 0, 0.5)';
                                    tooltip.style.border = '1px solid rgba(255, 255, 255, 0.1)';
                                    tooltip.style.pointerEvents = 'none';
                                    tooltip.style.zIndex = '9999';
                                    tooltip.style.fontSize = '12px';
                                    tooltip.style.fontFamily = 'Inter, sans-serif';
                                    tooltip.style.whiteSpace = 'pre-wrap';
                                    tooltip.style.lineHeight = '1.5';
                                    document.body.appendChild(tooltip);
                                }
                                tooltip.style.display = 'block';
                                tooltip.textContent = "No data";
                            });
                            cell.addEventListener('mousemove', (e) => {
                                const tooltip = document.getElementById('heatmap-tooltip');
                                if (tooltip) {
                                    tooltip.style.left = (e.clientX + 15) + 'px';
                                    tooltip.style.top = (e.clientY + 15) + 'px';
                                }
                            });
                            cell.addEventListener('mouseleave', (e) => {
                                cell.style.transform = 'scale(1)';
                                cell.style.zIndex = '1';
                                cell.style.boxShadow = 'none';
                                const tooltip = document.getElementById('heatmap-tooltip');
                                if (tooltip) tooltip.style.display = 'none';
                            });
                        }
                        grid.appendChild(cell);
                    }
                }
            }
            
            setupSearch();

            init();
        