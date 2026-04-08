import glob
import os

files = glob.glob('kinit-admin/src/views/Vadmin/PE/**/*.vue', recursive=True) + \
        glob.glob('kinit-admin/src/views/Vadmin/Fitness/**/*.vue', recursive=True)

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = False
    
    rep1 = "schoolOptions.value = schRes.data.map(i => ({ label: i.label, value: i.school_name }))"
    if "schoolOptions.value = schRes.data\n" in content:
        content = content.replace("schoolOptions.value = schRes.data\n", rep1 + "\n")
        changed = True
        
    rep2 = "schoolOptions.value = sRes.data.map(i => ({ label: i.label, value: i.school_name }))"
    if "schoolOptions.value = sRes.data\n" in content:
        content = content.replace("schoolOptions.value = sRes.data\n", rep2 + "\n")
        changed = True

    rep3 = "gradeOptions.value = res.data.map(i => ({ label: i.label, value: i.grade_name }))"
    if "gradeOptions.value = res.data\n" in content:
        content = content.replace("gradeOptions.value = res.data\n", rep3 + "\n")
        changed = True

    rep4 = "classOptions.value = res.data.map(i => ({ label: i.label, value: i.class_name }))"
    if "classOptions.value = res.data\n" in content:
        content = content.replace("classOptions.value = res.data\n", rep4 + "\n")
        changed = True

    if changed:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated options mapping in {file}")
