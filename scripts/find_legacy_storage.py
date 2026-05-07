import os

root = "Ward_DND_AI"
keywords = ["obsidian_storage", "ObsidianStorage", "file_storage", "FileStorage", '"obsidian"', '"file"']

for subdir, dirs, files in os.walk(root):
    for fname in files:
        if fname.endswith(".py"):
            with open(os.path.join(subdir, fname), encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            for i, line in enumerate(lines, 1):
                for kw in keywords:
                    if kw in line:
                        print(f"{os.path.join(subdir, fname)}:{i}: {line.strip()}")
