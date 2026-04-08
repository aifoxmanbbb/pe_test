import glob
import re
import os

files = glob.glob('kinit-admin/src/views/Vadmin/PE/**/*.vue', recursive=True) + \
        glob.glob('kinit-admin/src/views/Vadmin/Fitness/**/*.vue', recursive=True)

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    changed = False

    # 1. Add computed to imports if not present
    if 'computed' not in content and 'searchSchema' in content:
        content = re.sub(r"import \{([^}]*)\} from 'vue'", 
                         lambda m: f"import {{{m.group(1)}, computed}} from 'vue'" if 'computed' not in m.group(1) else m.group(0), 
                         content)
        changed = True

    # 2. Change reactive<FormSchema[]>([ to computed<FormSchema[]>(() => [
    if 'const searchSchema = reactive<FormSchema[]>([' in content:
        content = content.replace('const searchSchema = reactive<FormSchema[]>([', 'const searchSchema = computed<FormSchema[]>(() => [')
        
        # We need to find where the array ends to close the computed function.
        # For simplicity, since the searchSchema usually ends with `])` at the line start,
        # we can replace `\n])` with `\n])` -> wait, it's `])` for reactive, we change to `])` for computed.
        # Actually: reactive<FormSchema[]>([ ... ])
        # computed<FormSchema[]>(() => [ ... ])
        # The closing is still `])`. So the closing syntax is EXACTLY THE SAME! `])` is correct!
        changed = True

    # 3. Change options: xxxOptions to options: xxxOptions.value
    # Find all `options: \w+Options` and append `.value` if not already there
    def options_replacer(match):
        opt_name = match.group(1)
        if not opt_name.endswith('.value'):
            return f"options: {opt_name}.value"
        return match.group(0)

    new_content = re.sub(r"options:\s*(\w+Options(?:\.value)?)", options_replacer, content)
    if new_content != content:
        content = new_content
        changed = True

    # Also handle studentOptions if any
    new_content = re.sub(r"options:\s*(\w+Options(?:\.value)?)", options_replacer, content)
    if new_content != content:
        content = new_content
        changed = True

    if changed:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {file}")
