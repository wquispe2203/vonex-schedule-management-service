import xml.etree.ElementTree as ET
import os

path = r"d:\Desktop\MOD HOR\schedule-management-service\storage\xml_uploads\asctt2012.xml"
tree = ET.parse(path)
root = tree.getroot()

periods_map = {}
for p in root.find("periods").findall("period"):
    periods_map[int(p.get("period"))] = (p.get("starttime"), p.get("endtime"))

lessons_teacher = {}
for l in root.find("lessons").findall("lesson"):
    l_id = l.get("id")
    t_ids = l.get("teacherids")
    if t_ids:
        lessons_teacher[l_id] = t_ids.split(',')[0]

cards = root.find("cards").findall("card")

teacher_day_periods = {}
for c in cards:
    l_id = c.get("lessonid")
    t_id = lessons_teacher.get(l_id)
    if not t_id: continue
    day = c.get("days")
    period_node = c.get("period")
    if period_node:
        period = int(period_node)
        key = (t_id, day)
        if key not in teacher_day_periods:
            teacher_day_periods[key] = []
        teacher_day_periods[key].append(period)

# Analyze first 20 teachers with gaps
count = 0
for key, ps in teacher_day_periods.items():
    ps = sorted(list(set(ps)))
    for i in range(len(ps) - 1):
        if ps[i+1] > ps[i] + 1:
            t1_end = periods_map.get(ps[i], ("?", "?"))[1]
            t2_start = periods_map.get(ps[i+1], ("?", "?"))[0]
            print(f"Docente {key[0]} Día {key[1]}: Gap entre Periodo {ps[i]} ({t1_end}) y {ps[i+1]} ({t2_start})")
            count += 1
            if count > 20: break
    if count > 20: break
