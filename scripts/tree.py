import os
import sys


def tree(path, file, prefix=""):
    """
    Recursively writes a directory tree starting at path, excluding __pycache__, into the given file.
    """
    try:
        entries = sorted(os.listdir(path))
    except PermissionError:
        return

    for idx, name in enumerate(entries):
        full_path = os.path.join(path, name)
        is_last = idx == len(entries) - 1
        connector = "└── " if is_last else "├── "
        file.write(prefix + connector + name + "\n")
        if os.path.isdir(full_path) and name != "__pycache__":
            extension = "    " if is_last else "│   "
            tree(full_path, file, prefix + extension)


if __name__ == "__main__":
    # Determine project root and AI directory regardless of script location
    script_dir = os.path.abspath(os.path.dirname(__file__))
    base_name = os.path.basename(script_dir)
    if base_name.lower() == "ward_dnd_ai":
        ai_dir = script_dir
    else:
        ai_dir = os.path.join(script_dir, "Ward_DND_AI")

    if not os.path.isdir(ai_dir):
        print(f"Error: 'Ward_DND_AI' folder not found (expected at {ai_dir})")
        sys.exit(1)

    output_path = os.path.join(os.path.dirname(ai_dir), "ward_dnd_ai_tree.txt")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(os.path.basename(ai_dir) + "/\n")
            tree(ai_dir, f)
        print(f"Directory tree written to {output_path}")
    except Exception as e:
        print(f"Error writing to {output_path}: {e}")
