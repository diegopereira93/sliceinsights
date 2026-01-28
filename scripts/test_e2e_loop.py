
import time
import requests
import sys

def check_service(name, url, expected_status=200):
    try:
        start = time.time()
        response = requests.get(url, timeout=5)
        duration = (time.time() - start) * 1000
        if response.status_code == expected_status:
            print(f"✅ {name}: OK ({response.status_code}) - {duration:.2f}ms")
            return True, duration
        else:
            print(f"❌ {name}: Failed (Status: {response.status_code}) - {duration:.2f}ms")
            return False, duration
    except requests.exceptions.RequestException as e:
        print(f"❌ {name}: Connection Error - {e}")
        return False, 0

def run_tests(iterations=10):
    backend_url = "http://localhost:8002/"
    # Using the /api/v1/health endpoint if it exists, otherwise relying on root
    # Based on main.py, root returns a JSON with "health" key pointing to /api/v1/health
    # Let's try to hit the root first to get the health URL dynamically if possible? 
    # For now, let's just assume we hit the root and maybe the health endpoint.
    
    frontend_url = "http://localhost:3000/"
    
    print(f"🚀 Starting End-to-End Tests ({iterations} iterations)...")
    print(f"Backend URL: {backend_url}")
    print(f"Frontend URL: {frontend_url}\n")
    
    success_count = 0
    total_checks = 0
    
    for i in range(1, iterations + 1):
        print(f"--- Iteration {i}/{iterations} ---")
        
        # Check Backend Root
        b_success, _ = check_service("Backend Root", backend_url)
        
        # Check Backend Health (assuming /api/v1/health based on main.py)
        # We try this, but check_service handles if it's 404 or something else, but we want to know if it's UP.
        # If root worked, backend is UP. 
        # But let's try the specific health endpoint too.
        bh_success, _ = check_service("Backend Health", f"{backend_url}api/v1/health")
        
        # Check Frontend
        f_success, _ = check_service("Frontend", frontend_url)
        
        if b_success and f_success:
            print("Iteration passed.")
            success_count += 1
        else:
            print("Iteration failed.")
            
        total_checks += 1
        time.sleep(1) # Small delay between checks

    print("\n===============================")
    print(f"Summary: {success_count}/{iterations} Successful Iterations")
    print("===============================")
    
    if success_count == iterations:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
