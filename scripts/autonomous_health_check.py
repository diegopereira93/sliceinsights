import os
import requests
import time
import sys

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "https://sliceinsights.onrender.com/api/v1")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://frontend-five-iota-18.vercel.app")
SECRET = os.getenv("ADMIN_SEED_SECRET", "sliceinsights2026")

def check_backend():
    print(f"Checking backend: {BACKEND_URL}/health")
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=30)
        data = resp.json()
        if data.get("status") == "healthy" and data.get("database") == "connected":
            print("✅ Backend is healthy and connected to DB.")
            return True
        else:
            print(f"❌ Backend unhealthy: {data}")
            return False
    except Exception as e:
        print(f"❌ Backend check failed: {e}")
        return False

def check_data_availability():
    print(f"Checking data availability: {BACKEND_URL}/paddles")
    try:
        resp = requests.get(f"{BACKEND_URL}/paddles?limit=1&available_in_brazil=true", timeout=30)
        data = resp.json()
        count = data.get("total", 0)
        if count > 0:
            print(f"✅ Found {count} paddles available in Brazil.")
            return True
        else:
            print("❌ No paddles found in Brazil market!")
            return False
    except Exception as e:
        print(f"❌ Data check failed: {e}")
        return False

def trigger_reseed():
    print(f"Triggeting re-seed: {BACKEND_URL}/admin/seed")
    try:
        resp = requests.post(f"{BACKEND_URL}/admin/seed?secret={SECRET}", timeout=120)
        if resp.status_code == 200:
            print(f"✅ Seed triggered successfully: {resp.json()}")
            return True
        else:
            print(f"❌ Seed trigger failed: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Seed trigger request failed: {e}")
        return False

def check_frontend_ssr():
    print(f"Checking frontend SSR: {FRONTEND_URL}")
    try:
        # We look for the paddles data in the Next.js bootstrap data (__NEXT_DATA__)
        resp = requests.get(FRONTEND_URL, timeout=45)
        if "Nenhuma raquete encontrada" in resp.text and '"initialPaddles":[]' in resp.text:
            print("❌ Frontend is showing empty catalog!")
            return False
        else:
            print("✅ Frontend seems to have data or is healthy.")
            return True
    except Exception as e:
        print(f"❌ Frontend check failed: {e}")
        return False

def main():
    print("--- 🎾 Ralph-Loop Autonomous Health Check v1.1 (Redeploy Trigger) ---")
    
    # 1. Check Backend
    if not check_backend():
        print("Waiting for cold start...")
        time.sleep(30)
        if not check_backend():
            print("FATAL: Backend unreachable.")
            sys.exit(1)
            
    # 2. Check Data
    data_ok = check_data_availability()
    if not data_ok:
        print("Data is missing. Starting recovery...")
        trigger_reseed()
        time.sleep(10)
        if not check_data_availability():
            print("RECOVERY FAILED: Data still missing after seed.")
            sys.exit(1)
            
    # 3. Check Frontend
    if not check_frontend_ssr():
        print("Frontend cache might be stale or SSR is failing. Keeping backend alive...")
        # Add logic here if needed (e.g. trigger Vercel webhook)
        pass

    print("--- 🎾 Ralph-Loop Completed Successfully ---")

if __name__ == "__main__":
    main()
