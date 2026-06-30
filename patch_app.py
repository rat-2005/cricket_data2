import re

with open("app.py", "r") as f:
    content = f.read()

log_code = """
import datetime
@app.before_request
def log_request_info():
    with open("requests.log", "a") as f:
        f.write(f"[{datetime.datetime.now()}] URL: {request.url}\\n")
        f.write(f"[{datetime.datetime.now()}] ARGS: {dict(request.args)}\\n")
"""

content = content.replace("app = Flask(__name__)", "app = Flask(__name__)\n" + log_code)

with open("app.py", "w") as f:
    f.write(content)
