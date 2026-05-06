import os

ROOT_DIR = "Ward_DND_AI"
OLD = "storage"
NEW = "storage"

for subdir, dirs, files in os.walk(ROOT_DIR):
    for fname in files:
        if fname.endswith(".py"):
            fpath = os.path.join(subdir, fname)
            with open(fpath, encoding="utf-8") as f:
                content = f.read()
            if OLD in content:
                new_content = content.replace(OLD, NEW)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Replaced in: {fpath}")
print("All done!")
