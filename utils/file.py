import os
from itertools import islice


def find_file(folder: str, file: str) -> str | None:
    for root, _, files in os.walk(folder):
        if file in files:
            return os.path.join(root, file)
    return None


def generate_top_level_file_tree(root: str) -> str:
    if not os.path.exists(root):
        raise FileNotFoundError()

    file_tree = ""
    for f in os.listdir(root):
        if os.path.isfile(os.path.join(root, f)):
            file_tree += f"{f}\n"
            continue
        file_tree += f"{f}/\n"

    return file_tree


def read_file(
    path: str,
    start_line: int,
    end_line: int,
) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError()

    with open(path, "r") as f:
        lines = islice(f, start_line - 1, end_line)
        return "".join(lines)
