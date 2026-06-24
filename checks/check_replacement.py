with open('app.py', 'r') as f:
    content = f.read()

count = content.count("l.name NOT ILIKE '%world cup%'")
print('Replacements found:', count)
if count == 0:
    print('Failed to replace! Re-running replacement script...')
