import os

def fix_html_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace `sourceId === null && formatSelect`
    content = content.replace(
        "if (sourceId === null && formatSelect",
        "if (sourceId !== 'filterFormat' && formatSelect"
    )

    # Replace `sourceId === null && leagueSelect`
    content = content.replace(
        "if (sourceId === null && leagueSelect",
        "if (sourceId !== 'filterLeague' && leagueSelect"
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

fix_html_file('templates/batter.html')
fix_html_file('templates/bowler.html')
fix_html_file('templates/faceoff.html')

print("Applied proper cascading without lock-in!")
