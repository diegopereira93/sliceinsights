
import requests
from collections import Counter

def test_api_paddles():
    url = "http://localhost:8002/api/v1/paddles?limit=100"
    print(f"--- FETCHING FROM: {url} ---")
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        paddles = data.get("data", [])
        print(f"Fetched {len(paddles)} paddles.")
        
        ids = [p["id"] for p in paddles]
        id_counts = Counter(ids)
        
        duplicates = {id: count for id, count in id_counts.items() if count > 1}
        
        if not duplicates:
            print("No duplicate IDs found in API response.")
            
            # Check for duplicate names if IDs are unique
            names = [(p["brand_name"], p["model_name"]) for p in paddles]
            name_counts = Counter(names)
            name_duplicates = {name: count for name, count in name_counts.items() if count > 1}
            
            if name_duplicates:
                print(f"Found {len(name_duplicates)} duplicate (brand, model) pairs with unique IDs:")
                for name, count in name_duplicates.items():
                    print(f"- {name}: {count} occurrences")
            else:
                print("No duplicate (brand, model) pairs found.")
        else:
            print(f"Found {len(duplicates)} duplicate IDs in API response!")
            for id, count in duplicates.items():
                p = next(p for p in paddles if p["id"] == id)
                print(f"- ID {id} ({p['brand_name']} {p['model_name']}): {count} times")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api_paddles()
