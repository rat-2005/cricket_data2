            let currentBatterId = "{{ batter_id or '' }}";
            let currentBowlerId = "{{ bowler_id or '' }}";
            let lengthChartInstance = null;
            let wagonChartInstance = null;
            
            // Chart.js Default Config for Dark Theme
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
                        
                        if (filters.batting_types) {
                            const btSelect = document.getElementById('filterBattingType');
                            if (btSelect) btSelect.innerHTML += filters.batting_types.map(t => `<option value="${t}">${t}</option>`).join('');
                        }
                        if (filters.bowling_types) {
                            const bwtSelect = document.getElementById('filterBowlingType');
                            if (bwtSelect) bwtSelect.innerHTML += filters.bowling_types.map(t => `<option value="${t}">${t}</option>`).join('');
                        }
                        
                        convertToCustomMultiSelect('filterFormat');
                        convertToCustomMultiSelect('filterLeague');
                        convertToCustomMultiSelect('filterVenue');
                        if (document.getElementById('filterBattingType')) convertToCustomMultiSelect('filterBattingType');
                        if (document.getElementById('filterBowlingType')) convertToCustomMultiSelect('filterBowlingType');
                    }
                    
                    if (currentBatterId && currentBowlerId) {
                        const bRes = await fetch(`/api/athlete/${currentBatterId}`);
                        if (bRes.ok) document.getElementById('batterName').textContent = (await bRes.json()).full_name;
                        
                        const boRes = await fetch(`/api/athlete/${currentBowlerId}`);
                        if (boRes.ok) document.getElementById('bowlerName').textContent = (await boRes.json()).full_name;
                        
                        await fetchFaceoffFilters();
                        fetchStats();
                    }
                } catch(e) { console.error("Init failed", e); }
            }
            
            function getFilterVal(id) {
                const el = document.getElementById(id);
                if (!el) return 'All';
                
                if (el.parentElement && el.parentElement.classList.contains('custom-multi-wrapper')) {
                    const checkboxes = el.parentElement.querySelectorAll('.custom-multi-option input[type="checkbox"]:checked');
                    if (checkboxes.length > 0) {
                        return Array.from(checkboxes).map(cb => cb.value).join(',');
                    } else {
                        return 'All';
                    }
                }
                
                if (el.multiple) {
                    const vals = Array.from(el.selectedOptions).map(o => o.value);
                    return vals.length ? vals.join(',') : 'All';
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
                if (typeof val === "string" && val.includes(",")) val = val.split(",");
                if (Array.isArray(val)) {
                    Array.from(el.options).forEach(opt => {
                        opt.selected = val.includes(opt.value);
                    });
                } else {
                    if (el.multiple) {
                        Array.from(el.options).forEach(opt => {
                            opt.selected = (opt.value === val);
                        });
                    } else {
                        el.value = val;
                    }
                }
            }

            async function fetchFaceoffFilters(sourceId = null) {
                const bt = document.getElementById("filterBattingType"); const bwt = document.getElementById("filterBowlingType");
                if (!(currentBatterId || (bt && bt.value !== "All")) || !(currentBowlerId || (bwt && bwt.value !== "All"))) return;
                
                const formatSelect = document.getElementById('filterFormat');
                const leagueSelect = document.getElementById('filterLeague');
                const venSelect = document.getElementById('filterVenue');
                const yearSelect = document.getElementById('filterYear');
                const phaseSelect = document.getElementById('filterPhase');
                const inningsSelect = document.getElementById('filterInnings');
                const resultSelect = document.getElementById('filterResult');
                const recentSelect = document.getElementById('filterRecent');
                const wicketSelect = document.getElementById('filterWicketType');
                const plSelect = document.getElementById('filterPitchLength');
                const pitchLineSelect = document.getElementById('filterPitchLine');
                const shotSelect = document.getElementById('filterShotType');
                const deliveryOutputSelect = document.getElementById('filterDeliveryOutput');

                const currentFormat = formatSelect ? formatSelect.value || 'All' : 'All';
                const currentLeague = leagueSelect ? leagueSelect.value || 'All' : 'All';
                const currentVenue = venSelect ? venSelect.value || 'All' : 'All';
                const currentYear = yearSelect ? yearSelect.value || 'All' : 'All';
                const currentPhase = phaseSelect ? phaseSelect.value || 'All' : 'All';
                const currentInnings = inningsSelect ? inningsSelect.value || 'All' : 'All';
                const currentResult = resultSelect ? resultSelect.value || 'All' : 'All';
                const currentRecent = recentSelect ? recentSelect.value || 'All' : 'All';
                const currentWicket = wicketSelect ? wicketSelect.value || 'All' : 'All';
                const currentPitchLength = plSelect ? plSelect.value || 'All' : 'All';
                const currentPitchLine = pitchLineSelect ? pitchLineSelect.value || 'All' : 'All';
                const currentShotType = shotSelect ? shotSelect.value || 'All' : 'All';
                const currentDeliveryOutput = deliveryOutputSelect ? deliveryOutputSelect.value || 'All' : 'All';
                
                try {
                    const btV = document.getElementById("filterBattingType") ? document.getElementById("filterBattingType").value : "All";
                    const bwtV = document.getElementById("filterBowlingType") ? document.getElementById("filterBowlingType").value : "All";
                    const params = new URLSearchParams({
                        batter_id: currentBatterId || "", bowler_id: currentBowlerId || "", batting_type: btV, bowling_type: bwtV, format: currentFormat, league: currentLeague, venue: currentVenue,
                        year: currentYear, phase: currentPhase, recent: currentRecent, innings: currentInnings, result: currentResult,
                        wicket_type: currentWicket, pitch_length: currentPitchLength, pitch_line: currentPitchLine, shot_type: currentShotType, delivery_output: currentDeliveryOutput
                    });
                    
                    const filterRes = await fetch(`/api/faceoff_filters?${params.toString()}`);
                    
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
                        if (sourceId !== 'filterYear' && yearSelect && filters.years) {
                            yearSelect.innerHTML = '<option value="All">All Years</option>' + filters.years.map(y => `<option value="${y}">${y}</option>`).join('');
                            setFilterVal('filterYear', currentYear);
                        }
                        if (sourceId !== 'filterPhase' && phaseSelect && filters.phases) {
                            phaseSelect.innerHTML = '<option value="All">All Phases</option>' + filters.phases.map(p => `<option value="${p}">${p}</option>`).join('');
                            setFilterVal('filterPhase', currentPhase);
                        }
                        if (sourceId !== 'filterInnings' && inningsSelect && filters.innings) {
                            inningsSelect.innerHTML = '<option value="All">All Innings</option>' + filters.innings.map(i => `<option value="${i}">Innings ${i}</option>`).join('');
                            if (filters.innings.includes(currentInnings) || filters.innings.includes(parseInt(currentInnings))) inningsSelect.value = currentInnings;
                        }
                        if (sourceId !== 'filterResult' && resultSelect && filters.results) {
                            resultSelect.innerHTML = '<option value="All">All Results</option>' + filters.results.map(r => `<option value="${r}">${r}</option>`).join('');
                            setFilterVal('filterResult', currentResult);
                        }
                        if (sourceId !== 'filterWicketType' && wicketSelect && filters.wicket_types) {
                            wicketSelect.innerHTML = '<option value="All">All Types</option>' + filters.wicket_types.map(w => `<option value="${w}">${w}</option>`).join('');
                            if (filters.wicket_types.includes(currentWicket)) wicketSelect.value = currentWicket;
                        }
                        if (sourceId !== 'filterPitchLength' && plSelect && filters.pitch_lengths) {
                            plSelect.innerHTML = '<option value="All">All Lengths</option>' + filters.pitch_lengths.map(p => `<option value="${p}">${p}</option>`).join('');
                            setFilterVal('filterPitchLength', currentPitchLength);
                        }
                        if (sourceId !== 'filterPitchLine' && pitchLineSelect && filters.pitch_lines) {
                            pitchLineSelect.innerHTML = '<option value="All">All Lines</option>' + filters.pitch_lines.map(p => `<option value="${p}">${p}</option>`).join('');
                            setFilterVal('filterPitchLine', currentPitchLine);
                        }
                                                if (sourceId !== 'filterShotType' && shotSelect && filters.shot_types) {
                            shotSelect.innerHTML = '<option value="All">All Shots</option>' + filters.shot_types.map(s => `<option value="${s}">${s}</option>`).join('');
                            if (filters.shot_types.includes(currentShotType)) shotSelect.value = currentShotType;
                        }
                        const btSelect = document.getElementById('filterBattingType');
                        const bwtSelect = document.getElementById('filterBowlingType');
                        if (sourceId !== 'filterBattingType' && btSelect && filters.batting_types) {
                            const curr = btSelect.value;
                            btSelect.innerHTML = '<option value="All">All Types</option>' + filters.batting_types.map(s => `<option value="${s}">${s}</option>`).join('');
                            if (filters.batting_types.includes(curr)) btSelect.value = curr;
                        }
                        if (sourceId !== 'filterBowlingType' && bwtSelect && filters.bowling_types) {
                            const curr = bwtSelect.value;
                            bwtSelect.innerHTML = '<option value="All">All Types</option>' + filters.bowling_types.map(s => `<option value="${s}">${s}</option>`).join('');
                            if (filters.bowling_types.includes(curr)) bwtSelect.value = curr;
                        }
                        const selectIds = ['filterFormat', 'filterLeague', 'filterVenue', 'filterYear', 'filterInnings', 'filterResult', 'filterWicketType', 'filterPitchLength', 'filterPitchLine', 'filterShotType', 'filterPhase', 'filterDeliveryOutput', 'filterBattingType', 'filterBowlingType'];
                        selectIds.forEach(id => {
                            if (sourceId !== id && document.getElementById(id)) {
                                convertToCustomMultiSelect(id);
                            }
                        });
                    }
                } catch(e) { 
                    console.error("Filter update failed", e); 
                }
            }

            if(document.getElementById('filterFormat')) document.getElementById('filterFormat').addEventListener('change', async () => { await fetchFaceoffFilters('filterFormat'); fetchStats(); });
            if(document.getElementById('filterLeague')) document.getElementById('filterLeague').addEventListener('change', async () => { await fetchFaceoffFilters('filterLeague'); fetchStats(); });
            if(document.getElementById('filterVenue')) document.getElementById('filterVenue').addEventListener('change', async () => { await fetchFaceoffFilters('filterVenue'); fetchStats(); });
            if(document.getElementById('filterYear')) document.getElementById('filterYear').addEventListener('change', async () => { await fetchFaceoffFilters('filterYear'); fetchStats(); });
            if(document.getElementById('filterPhase')) document.getElementById('filterPhase').addEventListener('change', async () => { await fetchFaceoffFilters('filterPhase'); fetchStats(); });
            if(document.getElementById('filterInnings')) document.getElementById('filterInnings').addEventListener('change', async () => { await fetchFaceoffFilters('filterInnings'); fetchStats(); });
            if(document.getElementById('filterResult')) document.getElementById('filterResult').addEventListener('change', async () => { await fetchFaceoffFilters('filterResult'); fetchStats(); });
            if(document.getElementById('filterRecent')) document.getElementById('filterRecent').addEventListener('change', async () => { await fetchFaceoffFilters('filterRecent'); fetchStats(); });
            if(document.getElementById('filterWicketType')) document.getElementById('filterWicketType').addEventListener('change', async () => { await fetchFaceoffFilters('filterWicketType'); fetchStats(); });
            if(document.getElementById('filterPitchLength')) document.getElementById('filterPitchLength').addEventListener('change', async () => { await fetchFaceoffFilters('filterPitchLength'); fetchStats(); });
            if(document.getElementById('filterPitchLine')) document.getElementById('filterPitchLine').addEventListener('change', async () => { await fetchFaceoffFilters('filterPitchLine'); fetchStats(); });
            if(document.getElementById('filterShotType')) document.getElementById('filterShotType').addEventListener('change', async () => { await fetchFaceoffFilters('filterShotType'); fetchStats(); });
            if(document.getElementById('filterDeliveryOutput')) document.getElementById('filterDeliveryOutput').addEventListener('change', async () => { await fetchFaceoffFilters('filterDeliveryOutput'); fetchStats(); });

            if(document.getElementById('filterBattingType')) document.getElementById('filterBattingType').addEventListener('change', async () => {
                currentBatterId = null;
                document.getElementById('batterSearch').value = '';
                document.getElementById('batterName').textContent = 'Unknown Batter';
                await fetchFaceoffFilters('filterBattingType');
                fetchStats();
            });
            if(document.getElementById('filterBowlingType')) document.getElementById('filterBowlingType').addEventListener('change', async () => {
                currentBowlerId = null;
                document.getElementById('bowlerSearch').value = '';
                document.getElementById('bowlerName').textContent = 'Unknown Bowler';
                await fetchFaceoffFilters('filterBowlingType');
                fetchStats();
            });

            function setupSearch(inputId, resultsId, isBatter) {
                const input = document.getElementById(inputId);
                const results = document.getElementById(resultsId);
                let timeout;
                
                input.addEventListener('input', (e) => {
                    const query = e.target.value.trim();
                    clearTimeout(timeout);
                    if (query.length < 1) { results.classList.remove('active'); return; }
                    
                    results.innerHTML = '<div style="padding: 1rem; color: var(--text-secondary); text-align: center;"><i class="fas fa-spinner fa-spin"></i></div>';
                    results.classList.add('active');

                    timeout = setTimeout(async () => {
                        try {
                            let url = `/api/search?q=${encodeURIComponent(query)}`;
                            if (isBatter && currentBowlerId) url += `&against_bowler=${currentBowlerId}`;
                            else if (!isBatter && currentBatterId) url += `&against_batter=${currentBatterId}`;
                            
                            const response = await fetch(url);
                            const data = await response.json();
                            
                            if(data.length > 0) {
                                results.innerHTML = data.map(p => {
                                    const safeName = (p.full_name || '').replace(/'/g, "\\'");
                                    return `
                                    <div class="search-result-item" onclick="selectPlayer('${p.id}', '${safeName}', ${isBatter})">
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
            
            async function selectPlayer(id, name, isBatter) {
                try {
                    const infoRes = await fetch(`/api/athlete/${id}`);
                    if (infoRes.ok) {
                        const info = await infoRes.json();
                        if (isBatter && info.battingStyle) {
                            const sel = document.getElementById('filterBattingType');
                            if (sel) {
                                if(!Array.from(sel.options).some(o => o.value === info.battingStyle)) sel.innerHTML += `<option value="${info.battingStyle}">${info.battingStyle}</option>`;
                                sel.value = info.battingStyle;
                            }
                        }
                        if (!isBatter && info.bowlingStyle) {
                            const sel = document.getElementById('filterBowlingType');
                            if (sel) {
                                if(!Array.from(sel.options).some(o => o.value === info.bowlingStyle)) sel.innerHTML += `<option value="${info.bowlingStyle}">${info.bowlingStyle}</option>`;
                                sel.value = info.bowlingStyle;
                            }
                        }
                    }
                } catch(e) {}

                if (isBatter) {
                    currentBatterId = id;
                    document.getElementById('batterName').textContent = name;
                    document.getElementById('batterProfileLink').href = `/player/${id}`;
                    document.getElementById('batterSearch').value = name;
                    document.getElementById('batterResults').classList.remove('active');
                } else {
                    currentBowlerId = id;
                    document.getElementById('bowlerName').textContent = name;
                    document.getElementById('bowlerProfileLink').href = `/player/${id}`;
                    document.getElementById('bowlerSearch').value = name;
                    document.getElementById('bowlerResults').classList.remove('active');
                }
                
                const bt = document.getElementById('filterBattingType'); const bwt = document.getElementById('filterBowlingType');
                if ((currentBatterId || (bt && bt.value !== 'All')) && (currentBowlerId || (bwt && bwt.value !== 'All'))) {
                    await fetchFaceoffFilters();
                    fetchStats();
                } else {
                    const url = new URL(window.location);
                    if (isBatter) url.searchParams.set('batter_id', id);
                    else url.searchParams.set('bowler_id', id);
                    window.history.pushState({}, '', url);
                }
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
                            cell.style.backgroundColor = `rgba(255, 255, 255, 0.02)`;
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

            function initWagonChart(data) {
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
                    
                    const centerX = width / 2;
                    const centerY = height / 2;
                    const radius = Math.min(centerX, centerY) - 10;
                    
                    // Draw Boundary
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
                    const batOriginY = centerY - radius * 0.134; // Calibrated bat position
                    
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
            }

            async function fetchStats() {
                const bt = document.getElementById('filterBattingType'); const bwt = document.getElementById('filterBowlingType');
                if (!(currentBatterId || (bt && bt.value !== 'All')) || !(currentBowlerId || (bwt && bwt.value !== 'All'))) {
                    alert("Please select players or player types before comparing.");
                    return;
                }
                
                document.getElementById('emptyState').style.display = 'none';
                document.getElementById('loadingState').style.display = 'flex';
                
                const btV = document.getElementById('filterBattingType') ? document.getElementById('filterBattingType').value : 'All';
                const bwtV = document.getElementById('filterBowlingType') ? document.getElementById('filterBowlingType').value : 'All';
                const baseParams = new URLSearchParams({
                    batter_id: currentBatterId || '', bowler_id: currentBowlerId || '', batting_type: btV, bowling_type: bwtV,
                    league: getFilterVal('filterLeague'), league_not: getFilterNot('filterLeague'),
                    phase: getFilterVal('filterPhase'), phase_not: getFilterNot('filterPhase'),
                    venue: getFilterVal('filterVenue'), venue_not: getFilterNot('filterVenue'),
                    year: getFilterVal('filterYear'), year_not: getFilterNot('filterYear'),
                    innings: getFilterVal('filterInnings'), innings_not: getFilterNot('filterInnings'),
                    result: getFilterVal('filterResult'), result_not: getFilterNot('filterResult'),
                    recent: getFilterVal('filterRecent'), recent_not: getFilterNot('filterRecent'),
                    wicket_type: getFilterVal('filterWicketType'), wicket_type_not: getFilterNot('filterWicketType'),
                    pitch_length: getFilterVal('filterPitchLength'), pitch_length_not: getFilterNot('filterPitchLength'),
                    pitch_line: getFilterVal('filterPitchLine'), pitch_line_not: getFilterNot('filterPitchLine'),
                    shot_type: getFilterVal('filterShotType'), shot_type_not: getFilterNot('filterShotType'),
                    delivery_output: getFilterVal('filterDeliveryOutput'), delivery_output_not: getFilterNot('filterDeliveryOutput')
                });
                
                try {
                    document.getElementById('mainContent').style.display = 'block';
                    
                    if (false) {
                        document.getElementById('chartsRow').style.display = 'none';
                        document.getElementById('statsGrid').className = '';
                        
                        const formats = ['Test', 'ODI', 'T20I', 'T20'];
                        let html = '';
                        
                        for (let fmt of formats) {
                            baseParams.set('format', fmt);
                            const res = await fetch(`/api/stats/faceoff?${baseParams.toString()}`);
                            const data = await res.json();
                            
                            if (data.balls > 0) {
                                html += `
                                <h3 style="margin-top: 2rem; margin-bottom: 1rem; color: var(--accent-blue); display:flex; align-items:center; gap:0.5rem;"><i class="fas fa-trophy"></i> ${fmt} Breakdown</h3>
                                <div class="bento-grid">
                                    <div class="glass-panel stat-box">
                                        <div class="stat-label">Runs Scored</div>
                                        <div class="stat-value">${data.runs}</div>
                                        <div class="stat-subtext">Avg: ${data.avg}</div>
                                    </div>
                                    <div class="glass-panel stat-box">
                                        <div class="stat-label">Strike Rate</div>
                                        <div class="stat-value" style="color: var(--accent-green); background: none; -webkit-text-fill-color: var(--accent-green);">${data.sr}</div>
                                        <div class="stat-subtext">Off ${data.balls} balls</div>
                                    </div>
                                    <div class="glass-panel stat-box">
                                        <div class="stat-label">Dismissals</div>
                                        <div class="stat-value" style="color: var(--accent-red); background: none; -webkit-text-fill-color: var(--accent-red);">${data.dismissals}</div>
                                        <div class="stat-subtext">${data.dot_pct}% Dot Balls</div>
                                    </div>
                                    <div class="glass-panel stat-box">
                                        <div class="stat-label">Boundaries</div>
                                        <div class="stat-value">${data.boundaries}<span style="font-size:1.5rem; color:var(--text-secondary);">/</span>${data.sixes}</div>
                                        <div class="stat-subtext">Fours / Sixes</div>
                                    </div>
                                </div>
                                `;
                            }
                        }
                        
                        if (html === '') {
                            html = '<div style="text-align:center; padding: 3rem; color: var(--text-secondary); background: rgba(0,0,0,0.2); border-radius: 12px;"><i class="fas fa-ghost" style="font-size: 2rem; margin-bottom: 1rem; display:block;"></i>No historical matchups found for the selected filters.</div>';
                        }
                        
                        document.getElementById('statsGrid').innerHTML = html;
                        document.getElementById('loadingState').style.display = 'none';
                        
                    } else {
                        document.getElementById('chartsRow').style.display = 'grid';
                        document.getElementById('statsGrid').className = 'bento-grid';
                        
                        
                        const res = await fetch(`/api/stats/faceoff?${baseParams.toString()}`);
                        const data = await res.json();
                        
                        document.getElementById('statsGrid').innerHTML = `
                            <div class="glass-panel stat-box">
                                <div class="stat-label">Runs Scored</div>
                                <div class="stat-value">${data.runs}</div>
                                <div class="stat-subtext">Avg: ${data.avg}</div>
                            </div>
                            <div class="glass-panel stat-box">
                                <div class="stat-label">Strike Rate</div>
                                <div class="stat-value" style="color: var(--accent-green); background: none; -webkit-text-fill-color: var(--accent-green);">${data.sr}</div>
                                <div class="stat-subtext">Off ${data.balls} balls</div>
                            </div>
                            <div class="glass-panel stat-box">
                                <div class="stat-label">Dismissals</div>
                                <div class="stat-value" style="color: var(--accent-red); background: none; -webkit-text-fill-color: var(--accent-red);">${data.dismissals}</div>
                                <div class="stat-subtext">${data.dot_pct}% Dot Balls</div>
                            </div>
                            <div class="glass-panel stat-box">
                                <div class="stat-label">Boundaries</div>
                                <div class="stat-value">${data.boundaries}<span style="font-size:1.5rem; color:var(--text-secondary);">/</span>${data.sixes}</div>
                                <div class="stat-subtext">Fours / Sixes</div>
                            </div>
                            <div class="glass-panel stat-box span-2">
                                <div class="stat-label">Favorite Shot</div>
                                <div class="stat-value small">${data.favorite_shot}</div>
                            </div>
                            <div class="glass-panel stat-box span-2">
                                <div class="stat-label">Dangerous Shot</div>
                                <div class="stat-value small">${data.dangerous_shot}</div>
                            </div>
                        `;
                        
                        // Render Chart
                        if (data.pitch_heatmap) {
                            renderPitchHeatmap(data.pitch_heatmap);
                        }
                        if (data.wagon_wheel) {
                            initWagonChart(data);
                        }
                        
                        // Recent Matches
                        const recentList = document.getElementById('recentMatchesList');
                        if (data.recent_matches && data.recent_matches.length > 0) {
                            recentList.innerHTML = data.recent_matches.map(rm => `
                                <tr>
                                    <td>
                                        <div style="font-weight: 600; color: white;">${rm.date}</div>
                                        <span class="badge ${rm.source.toLowerCase()}">${rm.source}</span>
                                    </td>
                                    <td>
                                        <div style="font-family: 'Outfit'; font-size: 1.1rem; font-weight: 600;">${rm.runs} <span style="font-size:0.8rem; color:var(--text-secondary);">runs</span></div>
                                        <div style="font-size: 0.8rem; color: var(--text-secondary);">${rm.balls} balls</div>
                                    </td>
                                    <td>
                                        ${rm.dismissals > 0 
                                            ? `<span style="color: var(--accent-red); font-weight: 600;"><i class="fas fa-skull" style="margin-right:0.25rem;"></i> Out</span>` 
                                            : `<span style="color: var(--accent-green); font-weight: 600;"><i class="fas fa-shield-alt" style="margin-right:0.25rem;"></i> Not Out</span>`}
                                    </td>
                                </tr>
                            `).join('');
                        } else {
                            recentList.innerHTML = '<tr><td colspan="3" style="text-align:center; padding: 2rem;">No recent match data available</td></tr>';
                        }
                        
                        document.getElementById('loadingState').style.display = 'none';
                    }
                    
                } catch(e) {
                    console.error(e);
                    document.getElementById('loadingState').style.display = 'none';
                    document.getElementById('emptyState').style.display = 'block';
                    document.getElementById('emptyState').innerHTML = '<p style="color:var(--accent-red);">Failed to load faceoff data.</p>';
                }
            }
            
            setupSearch('batterSearch', 'batterResults', true);
            setupSearch('bowlerSearch', 'bowlerResults', false);
            init();
            initializeAllCustomSelects();
