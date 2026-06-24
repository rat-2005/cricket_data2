import os

# 1. Add "Player Profile" to nav links in all templates
templates_dir = "d:/cricket/fresh_data/templates"
templates = ["index.html", "batter.html", "bowler.html", "faceoff.html", "player.html"]

for t in templates:
    filepath = os.path.join(templates_dir, t)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "Player Profile" not in content:
        if t == "index.html":
            target = '<a href="/faceoff" class="tab active" style="background: var(--surface-hover); text-decoration: none;"><i class="fas fa-people-arrows"></i> Face-off</a>'
            replacement = target + '\n                <a href="/player" class="tab active" style="text-decoration: none;"><i class="fas fa-user"></i> Player Profile</a>'
            content = content.replace(target, replacement)
        elif t == "player.html":
            # Add nav links to player.html header
            target = '<div class="search-container">'
            replacement = """<div class="nav-links" style="display: flex; gap: 1rem;">
                <a href="/batter"><i class="fas fa-baseball-bat-ball"></i> Batter Analytics</a>
                <a href="/bowler"><i class="fas fa-bolt"></i> Bowler Analytics</a>
                <a href="/faceoff"><i class="fas fa-people-arrows"></i> Face-off</a>
                <a href="/player" class="active"><i class="fas fa-user"></i> Player Profile</a>
            </div>
            
            <div class="search-container">"""
            # add some style for nav-links to player.html
            style_target = ".logo a {\n            text-decoration: none;\n        }"
            style_replacement = """.logo a {
            text-decoration: none;
        }

        .nav-links a {
            padding: 0.75rem 1.5rem;
            border-radius: 100px;
            text-decoration: none;
            color: var(--text-secondary);
            font-weight: 600;
            font-family: 'Outfit', sans-serif;
            transition: all 0.3s ease;
        }

        .nav-links a:hover, .nav-links a.active {
            color: var(--text-primary);
            background: var(--surface-hover);
        }
        
        .nav-links a.active {
            background: var(--accent-gradient);
        }"""
            content = content.replace(target, replacement)
            if ".nav-links a" not in content:
                content = content.replace(style_target, style_replacement)
        else:
            target = '<a href="/faceoff"><i class="fas fa-people-arrows"></i> Face-off</a>'
            active_class = ' class="active"' if t == "player.html" else ""
            replacement = target + f'\n                <a href="/player"{active_class}><i class="fas fa-user"></i> Player Profile</a>'
            content = content.replace(target, replacement)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Added Player Profile link to {t}")

# 2. Fix player.html to support empty athlete (Search State)
player_path = os.path.join(templates_dir, "player.html")
with open(player_path, 'r', encoding='utf-8') as f:
    player_content = f.read()

if "{% if athlete %}" not in player_content:
    # 1. Fix title
    player_content = player_content.replace("<title>{{ athlete.full_name }} - Profile | Cricket Analytics</title>", "<title>{% if athlete %}{{ athlete.full_name }} - Profile{% else %}Player Profile{% endif %} | Cricket Analytics</title>")
    
    # 2. Wrap profile in if
    profile_start = '<div class="profile-header">'
    search_state = """
        {% if not athlete %}
        <div style="max-width: 600px; margin: 4rem auto; text-align: center;">
            <h2 style="font-size: 2.5rem; margin-bottom: 2rem;">Find a Player</h2>
            <div style="position: relative;">
                <i class="fas fa-search" style="position: absolute; left: 1.5rem; top: 50%; transform: translateY(-50%); color: var(--text-secondary); font-size: 1.2rem;"></i>
                <input type="text" id="mainPlayerSearch" placeholder="Type a player name..." autocomplete="off" style="width: 100%; padding: 1.5rem 1.5rem 1.5rem 4rem; background: rgba(0, 0, 0, 0.4); border: 1px solid var(--glass-border); border-radius: 100px; color: var(--text-primary); font-family: 'Outfit', sans-serif; font-size: 1.2rem; outline: none; transition: all 0.3s ease;">
                <div id="mainSearchResults" class="search-results"></div>
            </div>
        </div>
        
        <script>
            const mainSearchInput = document.getElementById('mainPlayerSearch');
            const mainSearchResults = document.getElementById('mainSearchResults');
            let mainSearchTimeout;

            mainSearchInput.addEventListener('input', (e) => {
                const query = e.target.value.trim();
                clearTimeout(mainSearchTimeout);
                if (query.length < 2) {
                    mainSearchResults.classList.remove('active');
                    return;
                }
                mainSearchTimeout = setTimeout(async () => {
                    try {
                        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                        const data = await response.json();
                        if (data.length > 0) {
                            mainSearchResults.innerHTML = data.map(player => `
                                <a href="/player/${player.id}" class="search-item" style="padding: 1rem 1.5rem; text-align: left;">
                                    <div>
                                        <div style="font-weight: 600; font-family: 'Outfit', sans-serif;">${player.full_name}</div>
                                        <div style="font-size: 0.8rem; color: var(--text-secondary);">${player.country_code || 'Unknown'}</div>
                                    </div>
                                </a>
                            `).join('');
                            mainSearchResults.classList.add('active');
                        } else {
                            mainSearchResults.innerHTML = '<div style="padding: 1rem; color: var(--text-secondary); text-align: center;">No players found</div>';
                            mainSearchResults.classList.add('active');
                        }
                    } catch (err) {
                        console.error('Search failed:', err);
                    }
                }, 300);
            });
            document.addEventListener('click', (e) => {
                if (!mainSearchInput.contains(e.target) && !mainSearchResults.contains(e.target)) {
                    mainSearchResults.classList.remove('active');
                }
            });
        </script>
        {% else %}
        <div class="profile-header">"""
    
    player_content = player_content.replace(profile_start, search_state)
    
    # 3. Close if at the end of the container
    container_end = """        {% endif %}
    </div>"""
    
    # Replace the last </div> before <script>
    player_content = player_content.replace('    </div>\n\n    <script>', container_end + '\n\n    <script>')
    
    with open(player_path, 'w', encoding='utf-8') as f:
        f.write(player_content)
    print("Wrapped player.html in if athlete check")
