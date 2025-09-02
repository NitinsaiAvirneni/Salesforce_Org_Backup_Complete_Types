import xml.etree.ElementTree as ET
import os
import copy

# === CONFIG ===
INPUT_PACKAGE = "manifest/package.xml"
OUTPUT_FOLDER = "split_manifests"
TYPES_PER_FILE = 50
IS_WINDOWS = True

# === PREPARE FOLDER ===
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === PARSE package.xml ===
tree = ET.parse(INPUT_PACKAGE)
root = tree.getroot()
namespace = {'sf': 'http://soap.sforce.com/2006/04/metadata'}

types = root.findall('sf:types', namespace)
version = root.find('sf:version', namespace).text

# === SPLIT TYPES ===
chunks = [types[i:i + TYPES_PER_FILE] for i in range(0, len(types), TYPES_PER_FILE)]
xml_files = []

for i, chunk in enumerate(chunks, start=1):
    # Create <Package> with only one xmlns
    package = ET.Element('Package', xmlns="http://soap.sforce.com/2006/04/metadata")
    
    # Append types (deepcopy to avoid removing from original tree)
    for t in chunk:
        # Remove namespace from tag names in the copy
        t_copy = copy.deepcopy(t)
        t_copy.tag = 'types'
        for child in t_copy:
            child.tag = child.tag.split('}')[-1]
        package.append(t_copy)

    # Add <version>
    ver_el = ET.SubElement(package, "version")
    ver_el.text = version

    # Save split file
    file_name = f"split_package_{i}.xml"
    file_path = os.path.join(OUTPUT_FOLDER, file_name)
    ET.ElementTree(package).write(file_path, encoding='utf-8', xml_declaration=True)
    xml_files.append(file_path)

# === GENERATE SCRIPT ===
script_file = "run_retrieves.bat" if IS_WINDOWS else "run_retrieves.sh"
with open(script_file, "w", encoding="utf-8") as f:
    if not IS_WINDOWS:
        f.write("#!/bin/bash\n\n")
    for xml_file in xml_files:
        rel_path = xml_file.replace("\\", "/")
        cmd = f"sf project retrieve start --manifest {rel_path} --target-org WESQA"
        f.write(cmd + ("\r\n" if IS_WINDOWS else "\n"))

print(f"✅ Done. Generated {len(xml_files)} package files and '{script_file}' script.")
