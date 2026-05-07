from datetime import time, datetime

def calculate_receso_gas(day_data):
    b_start_1 = time(9, 40)
    b_end_1 = time(10, 0)
    b_start_2 = time(10, 30)
    b_end_2 = time(10, 50)
    b_end_3 = time(11, 40)
    
    if not day_data: return 0.0
    
    d_start = min(datetime.strptime(str(d["start_time"]), "%H:%M").time() for d in day_data)
    d_end_orig = max(datetime.strptime(str(d["end_time"]), "%H:%M").time() for d in day_data)
    
    d_middle = d_end_orig
    d_end = d_end_orig
    
    for d in day_data:
        t_e = datetime.strptime(str(d["end_time"]), "%H:%M").time()
        if t_e >= b_end_1 and t_e <= b_end_3:
            d_end = t_e
        if t_e >= b_end_1 and t_e <= b_end_2:
            d_middle = t_e
            
    total_break_min = 0
    if d_start < b_start_1 and d_middle >= b_end_1 and d_middle <= b_end_2:
        total_break_min += 20
    if d_middle >= b_end_1 and d_middle <= b_end_2 and d_end >= b_end_2 and d_end <= b_end_3:
        total_break_min += 20
        
    return total_break_min

# Test Case 1: 17:00 Teacher
test1 = [{"start_time": "17:00", "end_time": "17:50"}]
print(f"Test 17:00: {calculate_receso_gas(test1)} min")

# Test Case 2: Morning Teacher (8:00 - 10:50)
test2 = [{"start_time": "08:00", "end_time": "08:50"}, {"start_time": "08:50", "end_time": "09:40"}, {"start_time": "10:00", "end_time": "10:50"}]
print(f"Test 08:00-10:50: {calculate_receso_gas(test2)} min")

# Test Case 3: 8:00 - 9:40
test3 = [{"start_time": "08:00", "end_time": "08:50"}, {"start_time": "08:50", "end_time": "09:40"}]
print(f"Test 08:00-09:40: {calculate_receso_gas(test3)} min")
