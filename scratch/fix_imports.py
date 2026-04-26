import os
import re
from pathlib import Path

packages = ["providers", "theme", "services", "components", "ads", "session", "agent", "auth"]
src_dir = Path("c:/Users/nwoki/Desktop/agent-project/fletbot/src")

def fix_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for pkg in packages:
        # Avoid double src. if already present
        # Fix "from pkg" and "import pkg" if at start of line or after space
        pattern1 = rf'from {pkg}'
        new_content = re.sub(pattern1, f'from src.{pkg}', new_content)
        
        # Also handle "import pkg" (less common but possible)
        pattern2 = rf'import {pkg}'
        new_content = re.sub(pattern2, f'import src.{pkg}', new_content)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed imports in {file_path}")

for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith(".py"):
            fix_imports(Path(root) / file)
