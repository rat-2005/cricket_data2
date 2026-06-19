with open('d:/cricket/fresh_data/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('d.over <= 5', 'd.over_number <= 5')
content = content.replace('d.over > 5', 'd.over_number > 5')
content = content.replace('d.over <= 14', 'd.over_number <= 14')
content = content.replace('d.over > 14', 'd.over_number > 14')

with open('d:/cricket/fresh_data/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
