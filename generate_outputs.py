import requests
import json
import os

# create folder if not exists
os.makedirs("sample_outputs", exist_ok=True)

for i in range(1, 11):
    sid = f"STU_{i:03d}"

    analyze = requests.post(f"http://127.0.0.1:8001/analyze/{sid}").json()
    recommend = requests.post(f"http://127.0.0.1:8001/recommend/{sid}").json()

    with open(f"sample_outputs/{sid}.json", "w") as f:
        json.dump({
            "analyze": analyze,
            "recommend": recommend
        }, f, indent=4)

print("✅ Sample outputs generated successfully!")