
            let currentAthleteId = "{{ athlete_id or '' }}";
            let wagonChartInstance = null;
            let shotChartInstance = null;
            let vulnChartInstance = null;
            
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
                        await fetchBatterFilters();
                        fetchStats();
                    }
                } catch(e) { console.error("Init failed", e); }
            }
            
            async function fetchBatterFilters(sourceId = null) {
                let currentId = '';
                if ('Batter' === 'Faceoff') {
                    if (!currentBatterId || !currentBowlerId) return;
                } else {
                    if (!currentAthleteId) return;
                    currentId = currentAthleteId;
                }
                
                const formatSelect = document.getElementById('filterFormat');
                const leagueSelect = document.getElementById('filterLeague');
                const venSelect = document.getElementById('filterVenue');
                const oppSelect = document.getElementById('filterOpponent');
                const bowlSelect = document.getElementById('filterBowlingType');
                const yearSelect = document.getElementById('filterYear');
                // phase, innings, result, recent are static or independent, but we send them
                
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
                    if ('Batter' === 'Faceoff') {
                        params = new URLSearchParams({
                            batter_id: currentBatterId, bowler_id: currentBowlerId, format: currentFormat, format_not, league: currentLeague, league_not, venue: currentVenue, venue_not,
                            opponent: currentOpp, opponent_not, bowling_type: currentBowl, bowling_type_not, innings: currentInnings, innings_not, 
                            result: currentResult, result_not, year: currentYear, year_not, phase: currentPhase, phase_not, recent: currentRecent, recent_not,
                            wicket_type: currentWicket, wicket_type_not, pitch_length: currentPitchLength, pitch_length_not, pitch_line: currentPitchLine, pitch_line_not, shot_type: currentShotType, shot_type_not
                        });
                    } else {
                        params = new URLSearchParams({
                            id: currentId, format: currentFormat, format_not, league: currentLeague, league_not, venue: currentVenue, venue_not,
                            opponent: currentOpp, opponent_not, bowling_type: currentBowl, bowling_type_not, innings: currentInnings, innings_not, 
                            result: currentResult, result_not, year: currentYear, year_not, phase: currentPhase, phase_not, recent: currentRecent, recent_not,
                            wicket_type: currentWicket, wicket_type_not, pitch_length: currentPitchLength, pitch_length_not, pitch_line: currentPitchLine, pitch_line_not, shot_type: currentShotType, shot_type_not
                        });
                    }
                    
                    const endpoint = 'Batter' === 'Batter' ? '/api/batter_filters' : ('Batter' === 'Bowler' ? '/api/bowler_filters' : '/api/faceoff_filters');
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
                        if (sourceId !== 'filterBowlingType' && bowlSelect && filters.bowling_types) {
                            bowlSelect.innerHTML = '<option value="All">All Types</option>' + filters.bowling_types.map(b => `<option value="${b}">${b}</option>`).join('');
                            setFilterVal('filterBowlingType', currentBowl);
                        }
                        if (sourceId !== 'filterYear' && yearSelect && filters.years) {
                            let labelEl = document.getElementById('labelYear');
                            let isLeague = (currentLeague && currentLeague !== 'All');
                            if (labelEl) labelEl.innerText = isLeague ? 'Season' : 'Year';
                            let defaultTxt = isLeague ? 'All Seasons' : 'All Years';
                            yearSelect.innerHTML = `<option value="All">${defaultTxt}</option>` + filters.years.map(y => `<option value="${y}">${y}</option>`).join('');
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

            document.getElementById('filterFormat').addEventListener('change', () => fetchBatterFilters('filterFormat'));
            document.getElementById('filterLeague').addEventListener('change', () => fetchBatterFilters('filterLeague'));
            document.getElementById('filterVenue').addEventListener('change', () => fetchBatterFilters('filterVenue'));
            if(document.getElementById('filterOpponent')) document.getElementById('filterOpponent').addEventListener('change', () => fetchBatterFilters('filterOpponent'));
            if(document.getElementById('filterBowlingType')) document.getElementById('filterBowlingType').addEventListener('change', () => fetchBatterFilters('filterBowlingType'));
            if(document.getElementById('filterYear')) document.getElementById('filterYear').addEventListener('change', () => fetchBatterFilters('filterYear'));
            if(document.getElementById('filterInnings')) document.getElementById('filterInnings').addEventListener('change', () => fetchBatterFilters('filterInnings'));
            if(document.getElementById('filterResult')) document.getElementById('filterResult').addEventListener('change', () => fetchBatterFilters('filterResult'));
            if(document.getElementById('filterPhase')) document.getElementById('filterPhase').addEventListener('change', () => fetchBatterFilters('filterPhase'));
            if(document.getElementById('filterRecent')) document.getElementById('filterRecent').addEventListener('change', () => fetchBatterFilters('filterRecent'));
            if(document.getElementById('filterWicketType')) document.getElementById('filterWicketType').addEventListener('change', () => fetchBatterFilters('filterWicketType'));
            if(document.getElementById('filterPitchLength')) document.getElementById('filterPitchLength').addEventListener('change', () => fetchBatterFilters('filterPitchLength'));
            if(document.getElementById('filterPitchLine')) document.getElementById('filterPitchLine').addEventListener('change', () => fetchBatterFilters('filterPitchLine'));
            if(document.getElementById('filterShotType')) document.getElementById('filterShotType').addEventListener('change', () => fetchBatterFilters('filterShotType'));


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
                
                fetchBatterFilters();
                
                const url = new URL(window.location);
                url.searchParams.set('id', id);
                window.history.pushState({}, '', url);
            }
            
            function initCharts(data) {
                // Wagon Wheel Chart (Custom HTML5 Canvas)
                let canvas = document.getElementById('wagonChart');
                
                // Remove old listeners by cloning BEFORE drawing
                const newCanvas = canvas.cloneNode(true);
                canvas.parentNode.replaceChild(newCanvas, canvas);
                canvas = newCanvas;
                
                // Make the canvas larger by updating its max-width dynamically
                canvas.style.maxWidth = '500px';
                canvas.width = 600;
                canvas.height = 600;
                
                const emptyMsg = document.getElementById('wagonEmpty');
                if (emptyMsg) emptyMsg.remove();
                
                let scatterData = [];
                if (data.wagon_wheel) {
                    scatterData = data.wagon_wheel;
                }
                
                if (scatterData.length === 0) {
                    canvas.style.display = 'none';
                    document.getElementById('wagonLegend').style.display = 'none';
                    canvas.parentElement.insertAdjacentHTML('afterbegin', '<div id="wagonEmpty" style="text-align:center; padding:2rem; color:var(--text-secondary);">No wagon wheel data available</div>');
                } else {
                    canvas.style.display = 'block';
                    document.getElementById('wagonLegend').style.display = 'flex';
                    
                    const ctx = canvas.getContext('2d');
                    const width = canvas.width;
                    const height = canvas.height;
                    
                    // Draw Grass
                    ctx.fillStyle = '#22c55e';
                    ctx.fillRect(0, 0, width, height);
                    ctx.fillStyle = '#16a34a';
                    for(let i=0; i<height; i+=40) {
                        ctx.fillRect(0, i, width, 20);
                    }
                    
                    const centerX = canvas.width / 2;
                    const centerY = canvas.height / 2;
                    const radius = Math.min(centerX, centerY) - 20;
                    const batOriginY = centerY - radius * 0.134; // Calibrated bat position             // Draw Boundary
                    ctx.beginPath();
                    ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
                    ctx.strokeStyle = '#ffffff';
                    ctx.lineWidth = 2;
                    ctx.stroke();

                    // Draw 30 Yard Circle
                    ctx.beginPath();
                    ctx.arc(centerX, centerY, radius * 0.55, 0, 2 * Math.PI);
                    ctx.strokeStyle = '#ffffff';
                    ctx.lineWidth = 1.5;
                    ctx.stroke();
                    
                    // Draw Pitch
                    const pitchW = 24;
                    const pitchH = 70;
                    ctx.fillStyle = '#eab308';
                    ctx.fillRect(centerX - pitchW/2, centerY - pitchH/2, pitchW, pitchH);
                    
                    // Pitch Creases
                    ctx.strokeStyle = '#ffffff';
                    ctx.lineWidth = 1.5;
                    ctx.beginPath();
                    ctx.moveTo(centerX - pitchW/2, centerY - pitchH/2 + 12);
                    ctx.lineTo(centerX + pitchW/2, centerY - pitchH/2 + 12);
                    ctx.stroke();
                    ctx.beginPath();
                    ctx.moveTo(centerX - pitchW/2, centerY + pitchH/2 - 12);
                    ctx.lineTo(centerX + pitchW/2, centerY + pitchH/2 - 12);
                    ctx.stroke();
                    // Field Position Labels
                    ctx.font = '11px "Outfit", sans-serif';
                    ctx.fillStyle = 'rgba(255,255,255,0.7)';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    const labelR = radius + 1;
                    const labels = [
                        { name: 'Square Leg',      angle: 0   },
                        { name: 'Mid Wicket',      angle: 35  },
                        { name: 'Mid On',          angle: 70  },
                        { name: 'Straight',        angle: 90  },
                        { name: 'Mid Off',         angle: 110 },
                        { name: 'Cover',           angle: 145 },
                        { name: 'Point',           angle: 180 },
                        { name: 'Backward Point',  angle: 205 },
                        { name: 'Third Man',       angle: 235 },
                        { name: 'Fine Leg',        angle: 305 },
                    ];
                    labels.forEach(l => {
                        const a = l.angle * Math.PI / 180;
                        const lx = centerX - Math.cos(a) * labelR;
                        const ly = centerY + Math.sin(a) * labelR;
                        ctx.fillText(l.name, lx, ly);
                    });
                    
                    let drawnSpokes = [];
                    
                    // Draw Spokes
                    scatterData.forEach(w => {
                        ctx.beginPath();
                        ctx.moveTo(centerX, batOriginY);
                        
                        let nx, ny;
                        if (w.x > 0 || w.y > 0) {
                            nx = (w.x / 180) - 1.0;
                            ny = (w.y / 180) - 1.0;
                        } else if (w.zone > 0) {
                            const zoneAngles = {
                                1: {x: 0.6, y: -0.8},  2: {x: 1.0, y: 0.0},  3: {x: 0.7, y: 0.7},  4: {x: 0.0, y: 1.0},
                                5: {x: -0.7, y: 0.7},  6: {x: -1.0, y: 0.0}, 7: {x: -0.8, y: -0.6}, 8: {x: -0.6, y: -0.8}
                            };
                            if (zoneAngles[w.zone]) {
                                nx = zoneAngles[w.zone].x; ny = zoneAngles[w.zone].y;
                            } else { return; }
                        } else { return; }
                        
                        const mappedX = centerX + nx * radius;
                        const mappedY = centerY + ny * radius;
                        ctx.lineTo(mappedX, mappedY);
                        
                        let color = '#facc15'; // 1-3
                        if (w.runs === 4) color = '#3b82f6';
                        if (w.runs === 6) color = '#ef4444';
                        if (w.runs === 0) color = 'rgba(255,255,255,0.3)';
                        
                        ctx.strokeStyle = color;
                        ctx.lineWidth = w.runs >= 4 ? 2.5 : 1.5;
                        ctx.stroke();
                        
                        drawnSpokes.push({
                            endX: mappedX,
                            endY: mappedY,
                            data: w
                        });
                    });
                    
                    // Interactivity
                    let tooltip = document.getElementById('wagonTooltip');
                    if (!tooltip) {
                        tooltip = document.createElement('div');
                        tooltip.id = 'wagonTooltip';
                        tooltip.style.cssText = 'position:fixed; display:none; background:rgba(15,23,42,0.95); border:1px solid rgba(255,255,255,0.1); padding:1rem; border-radius:8px; pointer-events:none; z-index:1000; font-family:"Outfit", sans-serif; font-size:0.85rem; color:white; box-shadow: 0 8px 16px rgba(0,0,0,0.5); backdrop-filter: blur(4px); min-width: 150px;';
                        document.body.appendChild(tooltip);
                    }
                    
                    function pointToLineDistance(px, py, x1, y1, x2, y2) {
                        const A = px - x1; const B = py - y1; const C = x2 - x1; const D = y2 - y1;
                        const dot = A * C + B * D;
                        const len_sq = C * C + D * D;
                        let param = -1;
                        if (len_sq != 0) param = dot / len_sq;
                        let xx, yy;
                        if (param < 0) { xx = x1; yy = y1; }
                        else if (param > 1) { xx = x2; yy = y2; }
                        else { xx = x1 + param * C; yy = y1 + param * D; }
                        const dx = px - xx; const dy = py - yy;
                        return Math.sqrt(dx * dx + dy * dy);
                    }
                    
                    canvas.addEventListener('mousemove', (e) => {
                        const rect = canvas.getBoundingClientRect();
                        const scaleX = canvas.width / rect.width;
                        const scaleY = canvas.height / rect.height;
                        const mx = (e.clientX - rect.left) * scaleX;
                        const my = (e.clientY - rect.top) * scaleY;
                        
                        let closest = null;
                        let minDist = 12; // hit radius in canvas pixels
                        
                        drawnSpokes.forEach(spoke => {
                            const d = pointToLineDistance(mx, my, centerX, centerY, spoke.endX, spoke.endY);
                            if (d < minDist) {
                                minDist = d;
                                closest = spoke;
                            }
                        });
                        
                        if (closest) {
                            tooltip.style.display = 'block';
                            tooltip.style.left = (e.clientX + 15) + 'px';
                            tooltip.style.top = (e.clientY + 15) + 'px';
                            
                            let runColor = '#facc15';
                            if (closest.data.runs === 4) runColor = '#3b82f6';
                            if (closest.data.runs === 6) runColor = '#ef4444';
                            if (closest.data.runs === 0) runColor = '#94a3b8';
                            
                            tooltip.innerHTML = `
                                <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:8px;">
                                    <span style="display:inline-block; width:12px; height:12px; border-radius:50%; background:${runColor};"></span>
                                    <span style="font-weight:600; font-size:1rem;">${closest.data.runs} Runs</span>
                                </div>
                                <div style="margin-bottom:4px; color:var(--text-secondary);">Shot: <span style="color:white; font-weight:500;">${closest.data.shot_type && closest.data.shot_type !== 'Unknown' ? closest.data.shot_type : 'Not Specified'}</span></div>
                                <div style="margin-bottom:4px; color:var(--text-secondary);">Bowler: <span style="color:white; font-weight:500;">${closest.data.bowler_name || 'Unknown'}</span></div>
                                <div style="margin-bottom:4px; color:var(--text-secondary);">Length: <span style="color:white; font-weight:500;">${closest.data.length || 'Unknown'}</span></div>
                                <div style="margin-bottom:4px; color:var(--text-secondary);">Line: <span style="color:white; font-weight:500;">${closest.data.line || 'Unknown'}</span></div>
                                <div style="margin-bottom:4px; color:var(--text-secondary);">Over: <span style="color:white; font-weight:500;">${closest.data.over - 1}${closest.data.ball > 0 ? '.' + closest.data.ball : ''}</span></div>
                                <div style="margin-bottom:4px; color:var(--text-secondary);">Date: <span style="color:white; font-weight:500;">${closest.data.date ? new Date(closest.data.date).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata' }) : 'Unknown'}</span></div>
                                <div style="color:var(--text-secondary);">Time: <span style="color:white; font-weight:500;">${closest.data.date ? new Date(closest.data.date).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' }) : 'Unknown'} IST</span></div>
                            `;
                            canvas.style.cursor = 'pointer';
                        } else {
                            tooltip.style.display = 'none';
                            canvas.style.cursor = 'default';
                        }
                    });
                    
                    canvas.addEventListener('mouseleave', () => {
                        tooltip.style.display = 'none';
                    });
                }

                // Shot Mastery Chart (Bar)
                const shotCtx = document.getElementById('shotChart').getContext('2d');
                if (shotChartInstance) shotChartInstance.destroy();
                
                const sLabels = Object.keys(data.shot_data || {});
                const sValues = Object.values(data.shot_data || {});
                
                shotChartInstance = new Chart(shotCtx, {
                    type: 'bar',
                    data: {
                        labels: sLabels,
                        datasets: [{
                            label: 'Occurrences',
                            data: sValues,
                            backgroundColor: 'rgba(16, 185, 129, 0.8)',
                            borderRadius: 4
                        }]
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { display: false } } }
                    }
                });

                // Vulnerability Matrix (Bar/Doughnut)
                const vulnCtx = document.getElementById('vulnChart').getContext('2d');
                if (vulnChartInstance) vulnChartInstance.destroy();
                
                const vLabels = Object.keys(data.vuln_data || {});
                const vValues = Object.values(data.vuln_data || {});
                
                vulnChartInstance = new Chart(vulnCtx, {
                    type: 'bar',
                    data: {
                        labels: vLabels,
                        datasets: [{
                            label: 'Dismissals',
                            data: vValues,
                            backgroundColor: 'rgba(239, 68, 68, 0.8)',
                            borderRadius: 4
                        }]
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { display: false } } }
                    }
                });

                // Pitch Heatmap
                renderPitchHeatmap(data.pitch_heatmap);
            }

            function renderPitchHeatmap(heatmapData) {
                const grid = document.getElementById('pitchHeatmapGrid');
                if (!grid) return;
                
                // Keep the first 4 children (the headers)
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
                                // Sort shots by runs descending
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
                    bowling_type: document.getElementById('filterBowlingType').value,
                    innings: document.getElementById('filterInnings').value,
                    result: document.getElementById('filterResult').value,
                    year: document.getElementById('filterYear').value,
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
                            const res = await fetch(`/api/stats/batter?${baseParams.toString()}`);
                            const data = await res.json();
                            
                            if (data.runs > 0 || data.balls > 0) {
                                html += `
                                <h3 style="margin-top: 2rem; margin-bottom: 1rem; color: var(--accent-blue); display:flex; align-items:center; gap:0.5rem;"><i class="fas fa-trophy"></i> ${fmt} Breakdown</h3>
                                <div class="bento-grid">
                                    <div class="glass-panel stat-box">
                                        <div class="stat-label">Runs Scored</div>
                                        <div class="stat-value">${data.runs}</div>
                                    </div>
                                    <div class="glass-panel stat-box">
                                        <div class="stat-label">Highest Score</div>
                                        <div class="stat-value small">${data.hs}</div>
                                    </div>
                                    <div class="glass-panel stat-box">
                                        <div class="stat-label">Strike Rate</div>
                                        <div class="stat-value" style="color: var(--accent-green); background: none; -webkit-text-fill-color: var(--accent-green);">${data.sr}</div>
                                    </div>
                                    <div class="glass-panel stat-box">
                                        <div class="stat-label">Sixes Hit</div>
                                        <div class="stat-value">${data.sixes}</div>
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
                        
                        const res = await fetch(`/api/stats/batter?${baseParams.toString()}`);
                        const data = await res.json();
                        
                        document.getElementById('statsGrid').innerHTML = `
                            <div class="glass-panel stat-box">
                                <div class="stat-label">Runs Scored</div>
                                <div class="stat-value">${data.runs}</div>
                            </div>
                            <div class="glass-panel stat-box">
                                <div class="stat-label">Highest Score</div>
                                <div class="stat-value small">${data.hs}</div>
                            </div>
                            <div class="glass-panel stat-box">
                                <div class="stat-label">Strike Rate</div>
                                <div class="stat-value" style="color: var(--accent-green); background: none; -webkit-text-fill-color: var(--accent-green);">${data.sr}</div>
                            </div>
                            <div class="glass-panel stat-box">
                                <div class="stat-label">Sixes Hit</div>
                                <div class="stat-value">${data.sixes}</div>
                            </div>
                        `;
                        
                        initCharts(data);
                        document.getElementById('loadingState').style.display = 'none';
                    }
                    
                } catch(e) {
                    console.error(e);
                    document.getElementById('loadingState').style.display = 'none';
                    document.getElementById('emptyState').style.display = 'block';
                    document.getElementById('emptyState').innerHTML = '<p style="color:var(--accent-red);">Failed to load batter data.</p>';
                }
            }
            
            setupSearch();
            init();
        