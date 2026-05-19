from app.core.database import SessionLocal
from app.modules.reportes.service import get_planilla_data
from datetime import date

def run():
    db = SessionLocal()
    try:
        # Test dates matching the historical import range: 2026-03-02 to 2026-03-20
        start = date(2026, 3, 2)
        end = date(2026, 3, 20)
        
        print("Testing get_planilla_data with historical date range:")
        result = get_planilla_data(db, start, end)
        print(f"Success: {result['success']}")
        if result['success']:
            data = result['data']
            print(f"Total records in paginated result: {data['total']}")
            print(f"Total hours sum: {data['total_hours_sum']}")
            print(f"Total receso count: {data['total_receso_count']}")
            print(f"Number of returned data items: {len(data['data'])}")
            if len(data['data']) > 0:
                print("First item preview:")
                print(data['data'][0])
    finally:
        db.close()

if __name__ == "__main__":
    run()
