"""Extract __NEXT_DATA__ from the SSR page and use the auth token it contains."""
from curl_cffi import requests
import re
import json

_NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>')

session = requests.Session(impersonate="chrome")

# Load page and extract everything from __NEXT_DATA__
url = "https://www.espncricinfo.com/series/india-in-south-africa-2023-24-1387592/south-africa-vs-india-3rd-t20i-1387599/ball-by-ball-commentary"
r = session.get(url)
m = _NEXT_DATA_RE.search(r.text)
full_data = json.loads(m.group(1))

# Look for auth tokens, API keys, or any configuration
print("=== Top-level keys ===")
print(list(full_data.keys()))

# Check props for auth info
props = full_data.get("props", {})
print("\n=== props keys ===")
print(list(props.keys()))

# Check for any auth/token in the full JSON
json_str = json.dumps(full_data)
# Search for token-related patterns
import re as re2
tokens = re2.findall(r'"(?:token|auth|apiKey|hsci)[^"]*"\s*:\s*"([^"]+)"', json_str, re.IGNORECASE)
print(f"\n=== Auth/token values found: {len(tokens)} ===")
for t in tokens[:5]:
    print(f"  {t[:80]}...")

# Check page props
app_page_props = props.get("appPageProps", {})
print(f"\n=== appPageProps keys ===")
print(list(app_page_props.keys()))

# Look for editionDetails or config
edition = app_page_props.get("editionDetails", {})
print(f"\n=== editionDetails ===")
print(json.dumps(edition, indent=2)[:500])

# Look for any API configuration
for key in app_page_props:
    val = app_page_props[key]
    if isinstance(val, str) and ("api" in val.lower() or "token" in val.lower() or "auth" in val.lower()):
        print(f"\nFound API-related string in appPageProps.{key}: {val[:200]}")
    elif isinstance(val, dict):
        val_str = json.dumps(val)
        if "api" in val_str.lower() or "token" in val_str.lower() or "auth" in val_str.lower():
            print(f"\nFound API-related dict in appPageProps.{key}: {val_str[:300]}")

# Check all script tags for auth tokens
print("\n=== Searching HTML for auth tokens ===")
auth_patterns = re2.findall(r'X-Hsci-Auth-Token["\s:]+([^"<]+)', r.text)
print(f"X-Hsci-Auth-Token: {auth_patterns}")

token_patterns = re2.findall(r'(?:hsciAuth|authToken|x-hsci)[^=]*=\s*["\']([^"\']+)', r.text, re.IGNORECASE)
print(f"Other token patterns: {token_patterns}")

# Look for script src that might contain API config
scripts = re2.findall(r'<script[^>]+src="([^"]*_app[^"]*)"', r.text)
print(f"\n_app script: {scripts}")
