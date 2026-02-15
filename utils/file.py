import os


def find_file(folder: str, file: str) -> str | None:
    for root, _, files in os.walk(folder):
        if file in files:
            return os.path.join(root, file)
    return None


def generate_top_level_file_tree(root: str) -> str:
    if not os.path.exists(root):
        raise Exception(f"{root} not found - cannot generate file tree")

    file_tree = ""
    for f in os.listdir(root):
        if os.path.isfile(os.path.join(root, f)):
            file_tree += f"{f}\n"
            continue
        file_tree += f"{f}/\n"

    return file_tree
