import glob
import os

files = glob.glob('kinit-admin/src/views/Vadmin/PE/**/*.vue', recursive=True) + \
        glob.glob('kinit-admin/src/views/Vadmin/Fitness/**/*.vue', recursive=True)

# Remove the BOM if present
def remove_bom(text):
    if text.startswith('\ufeff'):
        return text[1:]
    return text

for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = remove_bom(content)
    
    # Check if it actually needs restoration by looking for corrupted-looking chars like ä½
    if 'ä' in content or 'æ' in content or 'ç' in content:
        try:
            # Revert the GBK decoding that PowerShell did
            original_bytes = content.encode('latin1')
            restored_text = original_bytes.decode('utf-8')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(restored_text)
            print(f"Restored: {file_path}")
        except Exception as e:
            print(f"Failed {file_path}: {e}")
    else:
        print(f"Skipped (looks okay): {file_path}")
