import requests
import json
import time
import concurrent.futures
from itertools import product

URL = "http://localhost:8002/api/v1/recommendations"

SKILLS = ["beginner", "intermediate", "advanced"]
STYLES = ["power", "control", "balanced"]
BUDGETS = [600, 1200, 2500]
ELBOWS = [True, False]

def run_quiz(params):
    skill, style, budget, elbow = params
    payload = {
        "skill_level": skill,
        "play_style": style,
        "budget_max_brl": budget,
        "has_tennis_elbow": elbow
    }
    name = f"{skill} | {style} | R$ {budget} | Elbow: {elbow}"
    
    try:
        start = time.time()
        resp = requests.post(URL, json=payload, timeout=60)
        duration = time.time() - start
        if resp.status_code == 200:
            data = resp.json()
            recs = data.get("recommendations", [])
            top_1 = f"{recs[0]['brand_name']} {recs[0]['model_name']}" if recs else "NONE"
            return {
                "name": name,
                "payload": payload,
                "top_1": top_1,
                "duration": round(duration, 2),
                "success": True
            }
        return {"name": name, "success": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"name": name, "success": False, "error": str(e)}

def mass_simulation():
    combinations = list(product(SKILLS, STYLES, BUDGETS, ELBOWS))
    print(f"📦 Starting EXHAUSTIVE MATRIX: {len(combinations)} combinations...")
    
    results = []
    # Using ThreadPoolExecutor to speed up (Careful with Groq rate limits)
    # We'll use a small workers count to avoid 429
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_quiz, combo) for combo in combinations]
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            res = future.result()
            results.append(res)
            status = "✅" if res["success"] else "❌"
            print(f"[{i+1}/{len(combinations)}] {status} {res['name']}")

    with open("matrix_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n🏁 Matrix Audit Complete. Data saved to matrix_results.json")

if __name__ == "__main__":
    mass_simulation()
