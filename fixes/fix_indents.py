import re
with open('app.py', 'r') as f:
    content = f.read()

# Fix the 3 instances of if league_filter != 'All':\n        if league_filter == 'Series':
# One has 4 spaces, one has 12 spaces, etc.

# Let's just find "if league_filter != 'All':\n" followed by "        if league_filter == 'Series':"
# and we replace it with exactly what it was in my last multi_replace_file_content! Wait!
# In my `fix.py`, I replaced:
# "if league_filter != 'All':        if league_filter == 'Series':"
# with
# "if league_filter != 'All':\n        if league_filter == 'Series':"

# The issue is the spaces before `if league_filter == 'Series':` need to match the indentation of `if league_filter != 'All':` plus 4 spaces!

lines = content.split('\n')
for i, line in enumerate(lines):
    if line.strip() == "if league_filter == 'Series':":
        prev_line = lines[i-1]
        if "if league_filter != 'All':" in prev_line:
            # Get the leading spaces of the previous line
            spaces = len(prev_line) - len(prev_line.lstrip())
            lines[i] = (" " * (spaces + 4)) + "if league_filter == 'Series':"

with open('app.py', 'w') as f:
    f.write('\n'.join(lines))
