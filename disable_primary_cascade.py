import re

def prevent_primary_cascade(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove formatSelect update block
    content = re.sub(
        r"if \(sourceId !== 'filterFormat'.*?\}\n", 
        "", 
        content, 
        flags=re.DOTALL
    )

    # Remove leagueSelect update block
    content = re.sub(
        r"if \(sourceId !== 'filterLeague'.*?\}\n", 
        "", 
        content, 
        flags=re.DOTALL
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

prevent_primary_cascade('templates/batter.html')
prevent_primary_cascade('templates/bowler.html')
prevent_primary_cascade('templates/faceoff.html')

print("Disabled cascading for Format and League dropdowns!")
