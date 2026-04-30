import os

for root, dirs, files in os.walk('.'):
    if '.git' in root or '__pycache__' in root or 'venv' in root:
        continue
    for file in files:
        if file.endswith(('.py', '.txt', '.md', '.env', '.yml', '.sample')):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'ANIKA' in content or 'yukii' in content or 'Anika' in content:
                    content = content.replace('anikamusic', 'anikamusic')
                    content = content.replace('ANIKA', 'ANIKA')
                    content = content.replace('yukii', 'yukii')
                    content = content.replace('Anika', 'Anika')
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
            except Exception:
                pass

if os.path.exists('anikamusic'):
    os.rename('anikamusic', 'anikamusic')
    print("✅ Folder Renamed to anikamusic")
