import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the jsonify return block in batter_filters, bowler_filters, faceoff_filters
# We need to add the static lists so the frontend can populate the dropdowns.
static_lists = """
            return jsonify({
                "formats": sorted(res['formats']) if res and res['formats'] else [],
                "leagues": sorted(res['leagues']) if res and res['leagues'] else [],
                "venues": sorted(res['venues']) if res and res['venues'] else [],
                "phases": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"],
                "opponents": ["India", "Australia", "England", "South Africa", "New Zealand", "Pakistan", "Sri Lanka", "West Indies", "Bangladesh", "Afghanistan", "Chennai Super Kings", "Mumbai Indians", "Royal Challengers Bangalore", "Kolkata Knight Riders", "Delhi Capitals", "Rajasthan Royals", "Punjab Kings", "Sunrisers Hyderabad"],
                "bowling_types": ["Right-arm fast", "Right-arm medium", "Right-arm offbreak", "Legbreak", "Left-arm fast", "Left-arm medium", "Left-arm orthodox", "Left-arm chinaman"],
                "years": [str(y) for y in range(2008, 2026)]
"""

content = re.sub(
    r'return jsonify\(\{\s*"formats": sorted\(res\[\'formats\'\]\).*?phases": \["Powerplay.*?\]',
    static_lists.strip()[:-1],
    content,
    flags=re.DOTALL
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied static lists to filters!")
