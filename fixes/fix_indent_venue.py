import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("\nif venue_filter != 'All':", "\n    if venue_filter != 'All':")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed indentation!")
