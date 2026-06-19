with open('d:/cricket/fresh_data/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_route = """
@app.route("/player")
def player_search():
    return render_template("player.html", athlete=None, batting=None, bowling=None)
"""

if "@app.route(\"/player\")" not in content:
    content = content.replace('@app.route("/player/<athlete_id>")', new_route + '\n@app.route("/player/<athlete_id>")')
    with open('d:/cricket/fresh_data/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added /player route")
else:
    print("/player route already exists")
