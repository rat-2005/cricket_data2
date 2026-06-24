import re

def insert_listeners(filepath, prefix):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We will search for all listeners between the end of fetchFilters and function setupSearch() (or similar)
    # Actually, it's easier to just insert our new listeners right after `} catch(e) { console.error(e); } }`
    
    listeners = f"""
            document.getElementById('filterFormat').addEventListener('change', () => fetch{prefix}Filters('filterFormat'));
            document.getElementById('filterLeague').addEventListener('change', () => fetch{prefix}Filters('filterLeague'));
            document.getElementById('filterVenue').addEventListener('change', () => fetch{prefix}Filters('filterVenue'));
            if(document.getElementById('filterOpponent')) document.getElementById('filterOpponent').addEventListener('change', () => fetch{prefix}Filters('filterOpponent'));
            if(document.getElementById('filterBowlingType')) document.getElementById('filterBowlingType').addEventListener('change', () => fetch{prefix}Filters('filterBowlingType'));
            if(document.getElementById('filterYear')) document.getElementById('filterYear').addEventListener('change', () => fetch{prefix}Filters('filterYear'));
            if(document.getElementById('filterInnings')) document.getElementById('filterInnings').addEventListener('change', () => fetch{prefix}Filters('filterInnings'));
            if(document.getElementById('filterResult')) document.getElementById('filterResult').addEventListener('change', () => fetch{prefix}Filters('filterResult'));
            if(document.getElementById('filterPhase')) document.getElementById('filterPhase').addEventListener('change', () => fetch{prefix}Filters('filterPhase'));
            if(document.getElementById('filterRecent')) document.getElementById('filterRecent').addEventListener('change', () => fetch{prefix}Filters('filterRecent'));
            """
    
    # Let's remove existing listeners first to avoid duplication
    content = re.sub(rf"document\.getElementById\('filterFormat'\)\.addEventListener.*?;\n?", "", content)
    content = re.sub(rf"document\.getElementById\('filterLeague'\)\.addEventListener.*?;\n?", "", content)
    content = re.sub(rf"document\.getElementById\('filterVenue'\)\.addEventListener.*?;\n?", "", content)
    
    content = re.sub(r"(} catch\(e\) { \n\s*console\.error\(e\); \n\s*}\n\s*})", r"\1\n" + listeners, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

insert_listeners('templates/batter.html', 'Batter')
insert_listeners('templates/bowler.html', 'Bowler')
insert_listeners('templates/faceoff.html', 'Faceoff')

print("Listeners successfully injected!")
