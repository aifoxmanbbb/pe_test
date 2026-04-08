import glob
import os

# Fix Entry pages: change school_id field to school_name to match string values
files = glob.glob('../kinit-admin/src/views/Vadmin/PE/Entry/Entry.vue') + \
        glob.glob('../kinit-admin/src/views/Vadmin/Fitness/Entry/Entry.vue')

for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Change schema field name
    content = content.replace("field: 'school_id'", "field: 'school_name'")
    # 2. Change loadStudents param key
    content = content.replace("school_id: searchParams.value.school_id", "school_name: searchParams.value.school_name")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Patched {file_path}')
