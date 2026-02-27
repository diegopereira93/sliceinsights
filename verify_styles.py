import requests
import json

def test_style(style):
    url = "http://localhost:8002/api/v1/recommendations"
    payload = {
        "skill_level": "intermediate",
        "play_style": style,
        "budget_max_brl": 1500
    }
    resp = requests.post(url, json=payload)
    data = resp.json()
    print(f"\n--- STYLE: {style.upper()} ---")
    for rec in data.get("recommendations", []):
        print(f"Rank {rec['rank']}: {rec['brand_name']} {rec['model_name']} (Value: {rec.get('value_score')})")

if __name__ == "__main__":
    test_style("control")
    test_style("power")
