import threading
import time
import requests
import os
import uuid
import hashlib

# Configuration
API_URL = "http://localhost:8000/api/schedule/upload-xml"
XML_FILE_PATH = "tests/data/sample_large.xml" # Ensure this exists
CONCURRENT_UPLOADS = 5
TOKEN = "YOUR_AUTH_TOKEN_HERE" # Need a valid token

def simulate_upload(thread_id):
    print(f"[THREAD {thread_id}] Starting upload...")
    start_time = time.time()
    
    files = {'file': open(XML_FILE_PATH, 'rb')}
    data = {
        'start_date': '2026-01-01',
        'end_date': '2026-12-31',
        'overwrite': 'false'
    }
    headers = {'Authorization': f'Bearer {TOKEN}'}
    
    try:
        response = requests.post(API_URL, files=files, data=data, headers=headers)
        duration = time.time() - start_time
        print(f"[THREAD {thread_id}] Finished in {duration:.2f}s. Status: {response.status_code}")
        print(f"[THREAD {thread_id}] Response: {response.json()}")
    except Exception as e:
        print(f"[THREAD {thread_id}] Error: {e}")

def run_stress_test():
    threads = []
    for i in range(CONCURRENT_UPLOADS):
        t = threading.Thread(target=simulate_upload, args=(i,))
        threads.append(t)
        
    print(f"🚀 Launching {CONCURRENT_UPLOADS} concurrent uploads...")
    for t in threads:
        t.start()
        
    for t in threads:
        t.join()
    print("✅ Stress test completed.")

if __name__ == "__main__":
    if not os.path.exists(XML_FILE_PATH):
        print(f"❌ Error: {XML_FILE_PATH} not found. Please create a sample XML.")
    else:
        run_stress_test()
