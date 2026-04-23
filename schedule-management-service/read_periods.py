import xml.etree.ElementTree as ET
import os

xml_path = os.path.join("storage", "xml_uploads", "asctt2012.xml")
tree = ET.parse(xml_path)
root = tree.getroot()

periods_el = root.find("periods")
if periods_el is None:
    periods_el = root

for p in periods_el.findall("period")[:5]:
    print(p.attrib)
