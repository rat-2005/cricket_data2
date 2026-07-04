import re

files = ['templates/batter.html', 'templates/bowler.html', 'templates/faceoff.html']

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 1. Fix setFilterVal
    old_set = 'if (Array.isArray(val)) {'
    new_set = 'if (typeof val === "string" && val.includes(",")) val = val.split(",");\n                if (Array.isArray(val)) {'
    content = content.replace(old_set, new_set)
    
    # 2. Add re-initialization of custom selects at the end of filterRes.ok block
    rebuild_logic = '''
                        const selectIds = ['filterFormat', 'filterLeague', 'filterVenue', 'filterOpponent', 'filterBowlingType', 'filterYear', 'filterInnings', 'filterResult', 'filterWicketType', 'filterPitchLength', 'filterPitchLine', 'filterShotType', 'filterPhase'];
                        selectIds.forEach(id => {
                            if (sourceId !== id && document.getElementById(id)) {
                                convertToCustomMultiSelect(id);
                            }
                        });
'''
    content = re.sub(r'(setFilterVal\(\'filterPhase\', currentPhase\);\s*})', r'\1' + rebuild_logic, content)
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
print('Done!')
