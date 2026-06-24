import re

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
for i, line in enumerate(lines):
    # If the current line starts with some spaces and then `where_d`, `where_cricsheet`, `where_icc`, `where_b`, `where_f`, `elif`, `else:`
    # and the PREVIOUS line was `if league_filter == 'Series':`, we can see the indentation of `if league_filter == 'Series':` and fix everything below it up to the end of the block.
    # Actually, it's easier to just find the `if league_filter == 'Series':` lines and adjust the next lines.
    pass

# A simpler way:
# We know the block starts with:
#                 if league_filter == 'Series':
#             where_d.append(...)

for i in range(len(lines)):
    if "if league_filter == 'Series':" in lines[i]:
        # get the indent of the `if`
        indent = len(lines[i]) - len(lines[i].lstrip())
        
        # fix the next lines until we hit an empty line or something that shouldn't be in the block
        j = i + 1
        while j < len(lines):
            stripped = lines[j].lstrip()
            if not stripped:
                j += 1
                continue
                
            if stripped.startswith("elif ") or stripped.startswith("else:"):
                # these should match the indent of the `if`
                lines[j] = " " * indent + stripped + "\n"
            elif stripped.startswith("where_") or stripped.startswith("params_"):
                # these should be indented by 4 spaces MORE than the `if`
                lines[j] = " " * (indent + 4) + stripped + "\n"
            else:
                # end of block
                break
            j += 1

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed indentation!")
