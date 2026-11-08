import glob
import os

process_dir = "/home/me/repos/random-stuff/qidi-studio/process"
files = glob.glob(os.path.join(process_dir, "*.json"))
target = "{input_filename_base}_{filament_type[0]}_{print_time}.gcode"
replacement = "{input_filename_base}_{filament_type[0]}_{print_time}"

count = 0
for filepath in files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if target in content:
        content = content.replace(target, replacement)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed: {os.path.basename(filepath)}")
        count += 1

print(f"Completed: updated {count} files.")
