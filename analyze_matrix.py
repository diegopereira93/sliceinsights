import json
from collections import Counter

def analyze():
    try:
        with open("matrix_results.json", "r", encoding="utf-8") as f:
            results = json.load(f)
    except FileNotFoundError:
        print("❌ matrix_results.json not found. Run simulation first.")
        return

    total = len(results)
    successes = [r for r in results if r["success"]]
    fails = [r for r in results if not r["success"]]
    
    print(f"📊 Analyzing {total} results ({len(successes)} success, {len(fails)} fail)")
    
    # 1. Distribution Analysis
    all_picks = [r["top_1"] for r in successes]
    counts = Counter(all_picks)
    
    print("\n🏆 Top Recommended Paddles (Distribution):")
    for paddle, count in counts.most_common():
        pct = (count / len(successes)) * 100
        print(f" - {paddle}: {count} ({pct:.1f}%)")
        
    # 2. Skill Level Check
    regressions = []
    for r in successes:
        skill = r["payload"]["skill_level"]
        paddle = r["top_1"].lower()
        if skill == "advanced" and ("start" in paddle or "beginner" in paddle):
            regressions.append(f"🔴 ADVANCED got BEGINNER paddle: {r['name']} -> {r['top_1']}")
    
    if regressions:
        print("\n🚫 Skill Regressions Found:")
        for reg in regressions:
            print(reg)
    else:
        print("\n✅ Skill-to-Quality mapping looks solid.")

    # 3. Medical Check
    medical_fails = []
    for r in successes:
        if r["payload"]["has_tennis_elbow"] and "16mm" not in r["top_1"].lower() and "touch" not in r["top_1"].lower() and "soft" not in r["top_1"].lower():
             # Basic heuristic check for the report
             medical_fails.append(f"⚠️ ELBOW RISK: {r['name']} -> {r['top_1']}")
             
    if medical_fails:
        print("\n🩹 Medical Alignment Concerns (check these manually):")
        for m in medical_fails:
            print(m)

if __name__ == "__main__":
    analyze()
