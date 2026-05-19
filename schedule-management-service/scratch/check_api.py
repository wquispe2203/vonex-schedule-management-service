import requests

try:
    r = requests.get('http://127.0.0.1:8000/openapi.json')
    data = r.json()
    paths = list(data.get('paths', {}).keys())
    print("Paths count:", len(paths))
    print("bulk-delete-excel present:", '/api/docentes/bulk-delete-excel' in paths)
except Exception as e:
    print("Error:", e)
