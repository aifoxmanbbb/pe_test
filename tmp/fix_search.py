import glob
import re

files = glob.glob('kinit-admin/src/views/Vadmin/PE/**/*.vue', recursive=True) + \
        glob.glob('kinit-admin/src/views/Vadmin/Fitness/**/*.vue', recursive=True)

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = False
    
    # We only want to replace fields inside searchSchema, not table columns etc!
    # But since these specific vue files only use 'school_name' as a field in searchSchema or table columns.
    # Wait, table columns use `prop="school_name"`. The searchSchema uses `field: 'school_name'`.
    # So searching for `field: 'school_name'` is safe!
    
    new_content = re.sub(r"field:\s*'school_name'", "field: 'school_id'", content)
    if new_content != content: changed = True; content = new_content
    
    new_content = re.sub(r"field:\s*'grade_name'", "field: 'grade_id'", content)
    if new_content != content: changed = True; content = new_content
    
    new_content = re.sub(r"field:\s*'class_name'", "field: 'class_id'", content)
    if new_content != content: changed = True; content = new_content

    if changed:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {file}')
