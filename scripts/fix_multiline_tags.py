import os
import re

def fix_multiline_tags(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Fix {% ... %} tags - normalize multiple spaces and newlines to single space
                fixed_content = re.sub(
                    r'\{%\s+(.*?)\s+%\}', 
                    lambda m: '{% ' + re.sub(r'\s+', ' ', m.group(1).strip()) + ' %}', 
                    content, 
                    flags=re.DOTALL
                )
                
                # Fix {{ ... }} tags - normalize multiple spaces and newlines to single space
                fixed_content = re.sub(
                    r'\{\{\s+(.*?)\s+\}\}', 
                    lambda m: '{{ ' + re.sub(r'\s+', ' ', m.group(1).strip()) + ' }}', 
                    fixed_content, 
                    flags=re.DOTALL
                )

                if content != fixed_content:
                    print(f"Fixed multiline tags in: {file_path}")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)

if __name__ == "__main__":
    templates_dir = 'templates'
    if os.path.exists(templates_dir):
        fix_multiline_tags(templates_dir)
    else:
        print(f"Directory not found: {templates_dir}")
