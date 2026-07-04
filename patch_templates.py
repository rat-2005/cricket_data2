import re

def process_file(f):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Remove all Multi buttons
    content = re.sub(r'<button type="button" class="filter-btn" onclick="toggleMulti[^>]+>Multi</button>\s*', '', content)
    
    # Remove Split Formats label completely
    content = re.sub(r'<label style="display: flex; align-items: center; gap: 0\.5rem; color: var\(--text-primary\); cursor: pointer; font-size: 0\.85rem; font-weight: 600; text-transform: uppercase;">\s*<input type="checkbox" id="splitByFormat"[^>]+>\s*Split Formats\s*</label>\s*', '', content)
    
    # Add Reset Options button next to Analyze
    analyze_btn = r'(<button onclick="fetchStats\(\)" style="[^"]+">\s*Analyze\s*</button>)'
    reset_btn = '<button type="button" onclick="resetFilters()" style="padding: 0.8rem 2rem; border-radius: 12px; border: 1px solid var(--glass-border); background: rgba(0,0,0,0.4); color: white; font-family: \'Outfit\', sans-serif; font-weight: 600; font-size: 1.1rem; cursor: pointer; transition: background 0.2s;">Reset Options</button>'
    
    if "resetFilters()" not in content:
        content = re.sub(analyze_btn, reset_btn + r'\n                    \1', content)
    
    # Remove splitMode from javascript
    content = re.sub(r'const splitMode = document\.getElementById\(\'splitByFormat\'\)\.checked;\s*', '', content)
    
    # Remove the splitMode block from fetchStats (if (splitMode) { ... })
    # This is tricky with regex, we can just remove the if statement lines and let the backend handle format splitting if needed, but since we removed it, we'll just fix it manually if it breaks. Actually, the if(splitMode) block handles the fetching for multiple formats. We can just leave the code there, since splitMode will be undefined or false (Wait, if we delete the const splitMode, it throws a ReferenceError if splitMode is used).
    # Let's replace 'if (splitMode)' with 'if (false)'
    content = re.sub(r'if \(splitMode\)', 'if (false)', content)
    
    # Add initializeAllCustomSelects() at the end of the script before </script>
    if 'initializeAllCustomSelects()' not in content:
        content = content.replace('</script>', '    initializeAllCustomSelects();\n</script>')

    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

for f in ['templates/batter.html', 'templates/bowler.html', 'templates/faceoff.html']:
    process_file(f)
