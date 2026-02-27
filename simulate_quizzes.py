import requests
import json
import time

URL = "http://localhost:8002/api/v1/recommendations"

SCENARIOS = [
    {"name": "1. Advanced Balanced (R$ 800)", "payload": {"skill_level": "advanced", "play_style": "balanced", "budget_max_brl": 800}},
    {"name": "2. Beginner Control (R$ 600)", "payload": {"skill_level": "beginner", "play_style": "control", "budget_max_brl": 600}},
    {"name": "3. Advanced Power (Unlimited)", "payload": {"skill_level": "advanced", "play_style": "power", "budget_max_brl": 5000}},
    {"name": "4. Intermediate Balanced (R$ 1200)", "payload": {"skill_level": "intermediate", "play_style": "balanced", "budget_max_brl": 1200}},
    {"name": "5. Advanced Control (Elbow Risk)", "payload": {"skill_level": "advanced", "play_style": "control", "budget_max_brl": 2000, "has_tennis_elbow": True}},
    {"name": "6. Beginner Power (R$ 700)", "payload": {"skill_level": "beginner", "play_style": "power", "budget_max_brl": 700}},
    {"name": "7. Intermediate Power (R$ 2000)", "payload": {"skill_level": "intermediate", "play_style": "power", "budget_max_brl": 2000}},
    {"name": "8. Advanced Balanced (R$ 1500)", "payload": {"skill_level": "advanced", "play_style": "balanced", "budget_max_brl": 1500}},
    {"name": "9. Beginner Balanced (R$ 500)", "payload": {"skill_level": "beginner", "play_style": "balanced", "budget_max_brl": 500}},
    {"name": "10. Intermediate Control (R$ 1000)", "payload": {"skill_level": "intermediate", "play_style": "control", "budget_max_brl": 1000}},
]

def run_simulation():
    print(f"🚀 Starting Simulation of {len(SCENARIOS)} quizzes...\n")
    results = []
    
    for s in SCENARIOS:
        print(f"Running: {s['name']}...", end="", flush=True)
        try:
            start_time = time.time()
            resp = requests.post(URL, json=s['payload'], timeout=30)
            duration = time.time() - start_time
            
            if resp.status_code == 200:
                data = resp.json()
                recs = data.get("recommendations", [])
                top_3 = [f"{r.get('brand_name', 'Unknown')} {r.get('model_name', 'Unknown')}" for r in recs]
                results.append({
                    "scenario": s['name'],
                    "top_3": top_3,
                    "dossier_preview": data.get("grok_dossier", "")[:100] + "...",
                    "duration_s": round(duration, 2)
                })
                print(f" ✅ ({round(duration, 2)}s)")
            else:
                print(f" ❌ Error {resp.status_code}")
        except Exception as e:
            print(f" ❌ Failed: {str(e)}")
            
    # Output to a file for analysis
    with open("simulation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\n📊 Simulation Complete. Results saved to simulation_results.json")
    
    # Print a quick summary table
    print("\n" + "="*80)
    print(f"{'Scenario':<40} | {'Top Recommendation':<40}")
    print("-" * 81)
    for r in results:
        top_1 = r['top_3'][0] if r['top_3'] else "NONE"
        print(f"{r['scenario']:<40} | {top_1:<40}")
    print("="*80)

if __name__ == "__main__":
    run_simulation()
