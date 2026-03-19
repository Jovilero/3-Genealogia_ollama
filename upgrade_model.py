import os

def upgrade_model(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'qwen3:30b' in content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content.replace('qwen3:30b', 'qwen3:30b'))
        print(f"Updated {path}")

for root, _, files in os.walk('.'):
    for filename in files:
        if filename.endswith('.py') or filename.endswith('.md'):
            filepath = os.path.join(root, filename)
            if '0-antigravity' in filepath or '.venv' in filepath or '.git' in filepath:
                continue
            upgrade_model(filepath)
