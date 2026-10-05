import requests

key = 'AIzaSyBOrBf2PmguBKHaAtqigJHuHYZkW5H4pf4'   # <-- paste new key here

# First list all available models for this key
print("=== Listing available models for your key ===")
url = f'https://generativelanguage.googleapis.com/v1beta/models?key={key}'
r = requests.get(url, timeout=30)
if r.status_code == 200:
    models_list = r.json().get('models', [])
    for m in models_list:
        if 'generateContent' in m.get('supportedGenerationMethods', []):
            print(f"✅ Available: {m['name']}")
else:
    print(f"Error listing models: {r.json()}")