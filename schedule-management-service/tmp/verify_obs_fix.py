import requests

BASE_URL = "http://localhost:8000/api/schedule"

def test_sessions_for_obs():
    teacher_id = 99 # Abanto Herrera
    start = "2026-03-09"
    end = "2026-03-15"
    
    url = f"{BASE_URL}/sessions-for-obs?teacher_id={teacher_id}&start_date={start}&end_date={end}"
    print(f"Testing URL: {url}")
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Error: Status {response.status_code}")
            return

        data = response.json().get("data", [])
        print(f"Total blocks returned: {len(data)}")
        
        for b in data:
            print(f"[{b['date']}] {b['start_time']} - {b['end_time']} | Course: {b['subject']} | IDs: {b['session_ids']}")
        
        # Check for cleaning (Bug 2)
        long_courses = [d for d in data if "(" in d["subject"] or ")" in d["subject"]]
        if not long_courses:
            print("✅ BUG 2 (Cleaning): PASS - No suffixes found in subjects.")

    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    test_sessions_for_obs()
