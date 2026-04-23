from datetime import datetime, time
from decimal import Decimal

# Simulate the teacher blocks from March 18
blocks = [
    {"docente_name": "CARLOS", "date": "2026-03-18", "block_start_t": time(8, 0), "block_end_t": time(8, 50), "receso": Decimal('0.00')},
    {"docente_name": "CARLOS", "date": "2026-03-18", "block_start_t": time(9, 40), "block_end_t": time(10, 30), "receso": Decimal('0.00')},
]

final_consolidated_blocks = blocks

blocks_by_teacher_day = {}
for block in final_consolidated_blocks:
    k = (block["docente_name"], block["date"])
    if k not in blocks_by_teacher_day:
        blocks_by_teacher_day[k] = []
    blocks_by_teacher_day[k].append(block)

breaks = [{"start_time": "08:50:00", "end_time": "09:10:00"}]

for (docente, date), blocks in blocks_by_teacher_day.items():
    min_start = min([b["block_start_t"] for b in blocks])
    max_end = max([b["block_end_t"] for b in blocks])
    
    for b_config in breaks:
        b_start_t = datetime.strptime(b_config["start_time"], "%H:%M:%S").time()
        b_end_t = datetime.strptime(b_config["end_time"], "%H:%M:%S").time()
        
        print(f"min_start: {min_start}, max_end: {max_end}")
        print(f"b_start_t: {b_start_t}, b_end_t: {b_end_t}")
        print(f"Condition: {min_start <= b_start_t and max_end >= b_end_t}")
        
        if min_start <= b_start_t and max_end >= b_end_t:
            target_block = None
            eligible_blocks = [blk for blk in blocks if blk["block_start_t"] <= b_start_t]
            if eligible_blocks:
                target_block = sorted(eligible_blocks, key=lambda x: x["block_start_t"], reverse=True)[0]
            else:
                target_block = blocks[0]
            print(f"Assigned to {target_block['block_start_t']}")
            target_block["receso"] = Decimal('0.33')

for b in final_consolidated_blocks:
    print(b)
