import requests
import socket

# Test 1: DNS resolution
try:
    ip = socket.gethostbyname('catbox.moe')
    print(f"✅ DNS resolved: catbox.moe → {ip}")
except:
    print("❌ DNS failed: Can't resolve catbox.moe")

# Test 2: HTTP connection
try:
    response = requests.get('https://catbox.moe', timeout=10)
    print(f"✅ HTTP connection: Status {response.status_code}")
except Exception as e:
    print(f"❌ HTTP failed: {e}")

# Test 3: API endpoint
try:
    response = requests.get('https://catbox.moe/user/api.php', timeout=10)
    print(f"✅ API endpoint: Status {response.status_code}")
except Exception as e:
    print(f"❌ API failed: {e}")
