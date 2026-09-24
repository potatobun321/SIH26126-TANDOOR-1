import urllib.request
import urllib.error
import json

data = json.dumps({"command": "nav_ab"}).encode('utf-8')
req = urllib.request.Request("http://127.0.0.1:8080/api/command", data=data, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req) as resp:
        print("SUCCESS:", resp.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code, e.read().decode())
