import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Revert my previous mistake where I changed innings to inning_no for where_icc!
content = re.sub(r'where_icc\.append\("inning_no = %s"\)', r'where_icc.append("innings = %s")', content)
content = re.sub(r'where_icc\.append\("u\.inning_no = %s"\)', r'where_icc.append("u.innings = %s")', content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Reverted where_icc to innings!")
