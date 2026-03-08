import os
from difflib import SequenceMatcher
from itertools import islice


def find_file(folder: str, file: str) -> str | None:
    for root, _, files in os.walk(folder):
        if file in files:
            return os.path.join(root, file)
    return None


def generate_top_level_file_tree(
    root: str,
    sub_path: str | None = None,
) -> str:
    path = root
    if sub_path is not None:
        path = os.path.join(path, sub_path)

    if not os.path.exists(path):
        raise FileNotFoundError()

    file_tree = ""
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)):
            file_tree += f"{f}\n"
            continue
        file_tree += f"{f}/\n"

    return file_tree


def read_file(
    root: str,
    sub_path: str,
    start_line: int,
    end_line: int,
) -> str:
    path = os.path.join(root, sub_path)

    if not os.path.exists(path):
        raise FileNotFoundError()

    with open(path, "r") as f:
        lines = islice(f, start_line - 1, end_line)
        return "".join(lines)


def replace_text(
    root: str,
    sub_path: str,
    search: str,
    text: str,
    fuzzy_threshold: float = 0.8,
) -> bool:
    path = os.path.join(root, sub_path)

    if not os.path.exists(path):
        raise FileNotFoundError()

    with open(path, "r") as f:
        content = f.read()

    if search in content:
        content = content.replace(search, text)
        with open(path, "w") as f:
            f.write(content)
        return True

    search_len = len(search)
    best_ratio = 0.0
    best_start = -1

    for i in range(len(content) - search_len + 1):
        candidate = content[i : i + search_len]
        ratio = SequenceMatcher(None, search, candidate).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_start = i

    if best_ratio < fuzzy_threshold:
        return False

    content = content[:best_start] + text + content[best_start + search_len :]

    with open(path, "w") as f:
        f.write(content)

    return True


def insert_after(
    root: str,
    sub_path: str,
    search: str,
    text: str,
    fuzzy_threshold: float = 0.8,
) -> bool:
    path = os.path.join(root, sub_path)

    if not os.path.exists(path):
        raise FileNotFoundError()

    with open(path, "r") as f:
        content = f.read()

    if search in content:
        idx = content.index(search) + len(search)
        content = content[:idx] + text + content[idx:]
        with open(path, "w") as f:
            f.write(content)
        return True

    search_len = len(search)
    best_ratio = 0.0
    best_start = -1

    for i in range(len(content) - search_len + 1):
        candidate = content[i : i + search_len]
        ratio = SequenceMatcher(None, search, candidate).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_start = i

    if best_ratio < fuzzy_threshold:
        return False

    insert_pos = best_start + search_len
    content = content[:insert_pos] + text + content[insert_pos:]

    with open(path, "w") as f:
        f.write(content)

    return True


def create_file(
    root: str,
    sub_path: str,
    text: str = "",
) -> None:
    path = os.path.join(root, sub_path)

    if os.path.exists(path):
        raise FileExistsError()

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w") as f:
        f.write(text)


def delete_text(
    root: str,
    sub_path: str,
    search: str,
    fuzzy_threshold: float = 0.8,
) -> bool:
    path = os.path.join(root, sub_path)

    if not os.path.exists(path):
        raise FileNotFoundError()

    with open(path, "r") as f:
        content = f.read()

    if search in content:
        content = content.replace(search, "", 1)
        with open(path, "w") as f:
            f.write(content)
        return True

    search_len = len(search)
    best_ratio = 0.0
    best_start = -1

    for i in range(len(content) - search_len + 1):
        candidate = content[i : i + search_len]
        ratio = SequenceMatcher(None, search, candidate).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_start = i

    if best_ratio < fuzzy_threshold:
        return False

    content = content[:best_start] + content[best_start + search_len :]

    with open(path, "w") as f:
        f.write(content)

    return True
