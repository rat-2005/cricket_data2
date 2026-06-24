import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('"years": [str(y) for y in range(2008, 2026)\n            })', '"years": [str(y) for y in range(2008, 2026)]\n            })')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed syntax errors globally!")
