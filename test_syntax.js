
            let currentBatterId = "{{ batter_id or '' }}";
            let currentBowlerId = "{{ bowler_id or '' }}";
            
            async function init() {
                try {
                    const filterRes = await fetch(`/api/filters`);
                    if(filterRes.ok) {
                        const filters = await filterRes.json();
                        
                        const formatSelect = document.getElementById('filterFormat');
                        filters.formats.forEach(f => formatSelect.innerHTML += `<option value="${f}">${f}</option>`);
                        
                        const leagueSelect = document.getElementById('filterLeague');
                        filters.leagues.forEach(l => leagueSelect.innerHTML += `<option value="${l}">${l}</option>`);
                        
                        const venSelect = document.getElementById('filterVenue');
                        filters.venues.forEach(v => venSelect.innerHTML += `<option value="${v}">${v}</option>`);
                    }
                    
                    if (currentBatterId && currentBowlerId) {
                        // Pre-fetch names if IDs are in URL
                        const bRes = await fetch(`/api/athlete/${currentBatterId}`);
                        if (bRes.ok) document.getElementById('batterName').textContent = (await bRes.json()).full_name;
                        
                        const boRes = await fetch(`/api/athlete/${currentBowlerId}`);
                        if (boRes.ok) document.getElementById('bowlerName').textContent = (await boRes.json()).full_name;
                        
                        fetchStats();
                    }
                } catch(e) {
                    console.error("Init failed", e);
                }
            }
            
            function setupSearch(inputId, resultsId, isBatter) {
                const input = document.getElementById(inputId);
                const results = document.getElementById(resultsId);
                let timeout;
                
                input.addEventListener('input', (e) => {
                    const q = e.target.value.trim();
                    clearTimeout(timeout);
                    if(q.length < 1) { results.classList.remove('active'); return; }
                    
                    results.innerHTML = '<div style="padding: 1rem; color: var(--text-secondary); text-align: center;"><i class="fas fa-spinner fa-spin"></i> Searching...</div>';
                    results.classList.add('active');
                    
                    timeout = setTimeout(async () => {
                        try {
                            const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
                            const data = await res.json();
                            if(data.length > 0) {
                                results.innerHTML = data.map(p => {
                                    const safeName = (p.full_name || '').replace(/'/g, "\\'");
                                    return `
                                    <div class="search-item" onclick="selectPlayer('${p.id}', '${safeName}', ${isBatter})">
                                        <div style="font-weight: 600;">${p.full_name}</div>
                                    </div>
                                    `;
                                }).join('');
                            } else {
                                results.innerHTML = '<div style="padding: 1rem; color: var(--text-secondary); text-align: center;">No players found</div>';
                            }
                        } catch (err) {
                            results.innerHTML = '<div style="padding: 1rem; color: #ef4444; text-align: center;">Error loading results</div>';
                        }
                    }, 300);
                });
                
                document.addEventListener('click', (e) => {
                    if (!input.contains(e.target) && !results.contains(e.target)) {
                        results.classList.remove('active');
                    }
                });
            }
            
            function selectPlayer(id, name, isBatter) {
                if (isBatter) {
                    currentBatterId = id;
                    document.getElementById('batterName').textContent = name;
                    document.getElementById('batterSearch').value = name;
                    document.getElementById('batterResults').classList.remove('active');
                } else {
                    currentBowlerId = id;
                    document.getElementById('bowlerName').textContent = name;
                    document.getElementById('bowlerSearch').value = name;
                    document.getElementById('bowlerResults').classList.remove('active');
                }
            }
            
            async function fetchStats() {
                if (!currentBatterId || !currentBowlerId) {
                    alert("Please select both a batter and a bowler.");
                    return;
                }
                
                document.getElementById('statsGrid').innerHTML = '<div class="stat-card" style="grid-column: 1/-1;"><i class="fas fa-spinner fa-spin"></i><p>Calculating Head-to-Head...</p></div>';
                
                const params = new URLSearchParams({
                    batter_id: currentBatterId,
                    bowler_id: currentBowlerId,
                    format: document.getElementById('filterFormat').value,
                    league: document.getElementById('filterLeague').value,
                    phase: document.getElementById('filterPhase').value,
                    venue: document.getElementById('filterVenue').value
                });
                
                try {
                    const res = await fetch(`/api/stats/faceoff?${params.toString()}`);
                    const data = await res.json();
                    
                    document.getElementById('statsGrid').innerHTML = `
                        <div class="stat-card">
                            <i class="fas fa-baseball-bat-ball"></i>
                            <h3>Runs Scored</h3>
                            <p>${data.runs}</p>
                        </div>
                        <div class="stat-card">
                            <i class="fas fa-hashtag"></i>
                            <h3>Balls Faced</h3>
                            <p>${data.balls}</p>
                        </div>
                        <div class="stat-card">
                            <i class="fas fa-bullseye"></i>
                            <h3>Dismissals</h3>
                            <p>${data.dismissals}</p>
                        </div>
                        <div class="stat-card">
                            <i class="fas fa-bolt"></i>
                            <h3>Strike Rate</h3>
                            <p>${data.sr}</p>
                        </div>
                        <div class="stat-card">
                            <i class="fas fa-chart-line"></i>
                            <h3>Batting Avg</h3>
                            <p>${data.avg}</p>
                        </div>
                        <div class="stat-card">
                            <i class="fas fa-fire"></i>
                            <h3>Boundaries (4s/6s)</h3>
                            <p>${data.boundaries} / ${data.sixes}</p>
                        </div>
                    `;
                } catch(e) {
                    console.error("Fetch failed", e);
                    document.getElementById('statsGrid').innerHTML = '<p style="grid-column: 1/-1; text-align:center;">No match data found for this head-to-head with the given filters.</p>';
                }
            }
            
            setupSearch('batterSearch', 'batterResults', true);
            setupSearch('bowlerSearch', 'bowlerResults', false);
            init();
        