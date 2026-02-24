import os
import tempfile

import pytest

from utils.file import find_file, generate_top_level_file_tree, read_file


class TestFindFile:
    def test_find_file_in_root_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = "test.txt"
            file_path = os.path.join(tmpdir, test_file)
            with open(file_path, "w") as f:
                f.write("content")

            result = find_file(tmpdir, test_file)
            assert result == file_path

    def test_find_file_in_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "subdir")
            os.makedirs(subdir)
            test_file = "test.txt"
            file_path = os.path.join(subdir, test_file)
            with open(file_path, "w") as f:
                f.write("content")

            result = find_file(tmpdir, test_file)
            assert result == file_path

    def test_find_file_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = find_file(tmpdir, "nonexistent.txt")
            assert result is None

    def test_find_file_in_nested_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "level1", "level2", "level3")
            os.makedirs(nested_path)
            test_file = "deep.txt"
            file_path = os.path.join(nested_path, test_file)
            with open(file_path, "w") as f:
                f.write("content")

            result = find_file(tmpdir, test_file)
            assert result == file_path


class TestGenerateTopLevelFileTree:
    def test_generate_file_tree_with_files_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = ["file1.txt", "file2.py", "file3.md"]
            for f in files:
                with open(os.path.join(tmpdir, f), "w") as file:
                    file.write("content")

            result = generate_top_level_file_tree(tmpdir)
            for f in files:
                assert f"{f}\n" in result

    def test_generate_file_tree_with_directories_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dirs = ["dir1", "dir2", "dir3"]
            for d in dirs:
                os.makedirs(os.path.join(tmpdir, d))

            result = generate_top_level_file_tree(tmpdir)
            for d in dirs:
                assert f"{d}/\n" in result

    def test_generate_file_tree_with_mixed_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = ["file1.txt", "file2.py"]
            dirs = ["dir1", "dir2"]

            for f in files:
                with open(os.path.join(tmpdir, f), "w") as file:
                    file.write("content")

            for d in dirs:
                os.makedirs(os.path.join(tmpdir, d))

            result = generate_top_level_file_tree(tmpdir)
            for f in files:
                assert f"{f}\n" in result
            for d in dirs:
                assert f"{d}/\n" in result

    def test_generate_file_tree_with_sub_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = "subdir"
            os.makedirs(os.path.join(tmpdir, subdir))
            test_file = "test.txt"
            with open(os.path.join(tmpdir, subdir, test_file), "w") as f:
                f.write("content")

            result = generate_top_level_file_tree(tmpdir, subdir)
            assert f"{test_file}\n" in result

    def test_generate_file_tree_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_top_level_file_tree(tmpdir)
            assert result == ""

    def test_generate_file_tree_nonexistent_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                generate_top_level_file_tree(tmpdir, "nonexistent")


class TestReadFile:
    def test_read_file_full_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = "test.txt"
            content = "line1\nline2\nline3\n"
            file_path = os.path.join(tmpdir, test_file)
            with open(file_path, "w") as f:
                f.write(content)

            result = read_file(tmpdir, test_file, 1, 3)
            assert result == content

    def test_read_file_partial_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = "test.txt"
            content = "line1\nline2\nline3\nline4\n"
            file_path = os.path.join(tmpdir, test_file)
            with open(file_path, "w") as f:
                f.write(content)

            result = read_file(tmpdir, test_file, 2, 3)
            assert result == "line2\nline3\n"

    def test_read_file_single_line(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = "test.txt"
            content = "line1\nline2\nline3\n"
            file_path = os.path.join(tmpdir, test_file)
            with open(file_path, "w") as f:
                f.write(content)

            result = read_file(tmpdir, test_file, 2, 2)
            assert result == "line2\n"

    def test_read_file_with_sub_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = "subdir"
            os.makedirs(os.path.join(tmpdir, subdir))
            test_file = "test.txt"
            content = "line1\nline2\n"
            file_path = os.path.join(tmpdir, subdir, test_file)
            with open(file_path, "w") as f:
                f.write(content)

            result = read_file(tmpdir, os.path.join(subdir, test_file), 1, 2)
            assert result == content

    def test_read_file_nonexistent_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                read_file(tmpdir, "nonexistent.txt", 1, 10)

    def test_read_file_from_agents_md(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result = read_file(project_root, "AGENTS.md", 1, 3)
        assert "# Agents Guidelines For This Repository" in result
        assert "### Overview Of The Project" in result

    def test_read_file_specific_section_from_agents_md(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result = read_file(project_root, "AGENTS.md", 19, 20)
        assert "### Architecture" in result
