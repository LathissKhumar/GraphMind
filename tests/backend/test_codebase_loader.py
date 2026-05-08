import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import os
import git

sys_path = Path(__file__).parent.parent / "src"
import sys
sys.path.insert(0, str(sys_path))

from src.input.codebase_loader import CodebaseLoader, LoadResult
from git import GitCommandError as GitError, GitCommandNotFound


class TestCodebaseLoader:
    def test_init_default(self):
        loader = CodebaseLoader()
        assert loader.storage_dir == Path(".codebase")
        assert loader.storage_dir.exists()

    def test_init_custom_dir(self, tmp_path):
        loader = CodebaseLoader(storage_dir=str(tmp_path / "custom"))
        assert loader.storage_dir == tmp_path / "custom"
        assert loader.storage_dir.exists()

    def test_is_valid_github_url_valid(self):
        loader = CodebaseLoader()
        assert loader._is_valid_github_url("https://github.com/user/repo") is True
        assert loader._is_valid_github_url("https://www.github.com/user/repo") is True

    def test_is_valid_github_url_invalid(self):
        loader = CodebaseLoader()
        assert loader._is_valid_github_url("https://google.com/user/repo") is False
        assert loader._is_valid_github_url("not_a_url") is False
        assert loader._is_valid_github_url("https://github.com/user") is False  # Only 1 path component

    def test_extract_repo_name(self):
        loader = CodebaseLoader()
        result = loader._extract_repo_name("https://github.com/user/repo.git")
        assert result == "user_repo"
        
        result = loader._extract_repo_name("https://github.com/user/repo")
        assert result == "user_repo"

    def test_count_files(self, tmp_path):
        loader = CodebaseLoader()
        # Create some test files
        (tmp_path / "file1.py").write_text("test")
        (tmp_path / "file2.py").write_text("test")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "test.pyc").write_text("test")
        
        count = loader._count_files(tmp_path)
        assert count == 2  # Should skip __pycache__

    def test_detect_languages(self, tmp_path):
        loader = CodebaseLoader()
        # Create test files
        (tmp_path / "file1.py").write_text("print('hello')")
        (tmp_path / "file2.js").write_text("console.log('hello')")
        
        languages = loader._detect_languages(tmp_path)
        assert "Python" in languages or "JavaScript" in languages

    def test_load_from_git_invalid_url(self):
        loader = CodebaseLoader()
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            loader.load_from_git("https://not-github.com/user/repo")

    @patch("src.input.codebase_loader.git.Repo")
    def test_load_from_git_success(self, mock_repo, tmp_path):
        loader = CodebaseLoader(storage_dir=str(tmp_path / "storage"))
        mock_repo.clone_from.return_value = MagicMock()
        
        with patch.object(loader, '_count_files', return_value=10):
            with patch.object(loader, '_detect_languages', return_value=["Python"]):
                result = loader.load_from_git("https://github.com/user/repo")
        
        assert result["status"] == "success"
        assert result["repo_name"] == "user_repo"
        assert result["source"] == "git"

    def test_load_from_zip_not_found(self):
        loader = CodebaseLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_from_zip("/nonexistent/file.zip")

    def test_load_from_zip_invalid_zip(self, tmp_path):
        fake_zip = tmp_path / "fake.zip"
        fake_zip.write_text("not a zip")
        
        loader = CodebaseLoader()
        with pytest.raises(ValueError, match="Not a valid ZIP"):
            loader.load_from_zip(str(fake_zip))

    def test_get_top_level_name(self):
        loader = CodebaseLoader()
        names = ["dir1/file1.py", "dir1/file2.py", "dir2/file3.py"]
        assert loader._get_top_level_name(names) == "dir1"

    def test_get_top_level_name_no_subdir(self):
        loader = CodebaseLoader()
        names = ["file1.py", "file2.py"]
        assert loader._get_top_level_name(names) == "extracted"

    @patch("src.input.codebase_loader.git.Repo")
    def test_load_from_git_git_not_found(self, mock_repo):
        loader = CodebaseLoader()
        mock_repo.clone_from.side_effect = GitCommandNotFound("git", "cause")
        with pytest.raises(RuntimeError):
            loader.load_from_git("https://github.com/user/repo")

    @patch("src.input.codebase_loader.git.Repo")
    def test_load_from_git_clone_error(self, mock_repo):
        loader = CodebaseLoader()
        mock_repo.clone_from.side_effect = Exception("Clone failed")
        with pytest.raises(RuntimeError, match="Failed to clone"):
            loader.load_from_git("https://github.com/user/repo")

    def test_load_from_zip_too_large(self, tmp_path):
        loader = CodebaseLoader()
        fake_zip = tmp_path / "large.zip"
        fake_zip.write_text("dummy")  # Create the file so it exists
        with patch("src.input.codebase_loader.zipfile.is_zipfile", return_value=True):
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 10485761  # Just over 10MB limit
                with pytest.raises(ValueError, match="too large"):
                    loader.load_from_zip(str(fake_zip))

    def test_load_from_zip_corrupt(self, tmp_path):
        loader = CodebaseLoader()
        fake_zip = tmp_path / "corrupt.zip"
        fake_zip.write_text("not a zip")
        
        with patch("zipfile.is_zipfile", return_value=True):
            with patch("zipfile.ZipFile") as mock_zip:
                mock_zip_instance = MagicMock()
                mock_zip_instance.testzip.return_value = "bad_file.zip"
                mock_zip.return_value.__enter__ = lambda s: mock_zip_instance
                mock_zip.return_value.__exit__ = MagicMock(return_value=False)
                with pytest.raises(ValueError, match="Corrupt ZIP"):
                    loader.load_from_zip(str(fake_zip))

    def test_load_from_zip_too_many_files(self, tmp_path):
        loader = CodebaseLoader()
        fake_zip = tmp_path / "many_files.zip"
        fake_zip.write_text("dummy")
        
        with patch("src.input.codebase_loader.zipfile.is_zipfile", return_value=True):
            with patch("src.input.codebase_loader.zipfile.ZipFile") as mock_zip:
                mock_zip_instance = MagicMock()
                mock_zip_instance.testzip.return_value = None
                mock_zip_instance.namelist.return_value = [f"file{i}.py" for i in range(5001)]
                mock_zip.return_value.__enter__ = lambda s: mock_zip_instance
                mock_zip.return_value.__exit__ = MagicMock(return_value=False)
                with pytest.raises(ValueError, match="Too many files"):
                    loader.load_from_zip(str(fake_zip))

    def test_safe_extract_path_zipslip(self):
        loader = CodebaseLoader()
        base_dir = Path("/tmp/test")
        with pytest.raises(ValueError, match="ZipSlip"):
            loader._safe_extract_path(base_dir, "../../etc/passwd")

    def test_safe_extract_path_dots(self):
        loader = CodebaseLoader()
        base_dir = Path("/tmp/test")
        with pytest.raises(ValueError, match="ZipSlip"):
            loader._safe_extract_path(base_dir, "../escape")
            loader._safe_extract_path(base_dir, "../escape")

    def test_count_files_skip_git(self, tmp_path):
        loader = CodebaseLoader()
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("git config")
        (tmp_path / "file.py").write_text("test")
        
        count = loader._count_files(tmp_path)
        assert count == 1  # Should skip .git directory

    def test_detect_languages_no_lexer(self, tmp_path):
        loader = CodebaseLoader()
        (tmp_path / "unknown.xyz").write_text("some content")
        
        with patch("pygments.lexers.guess_lexer_for_filename") as mock_guess:
            mock_guess.side_effect = Exception("No lexer")
            with patch("pygments.lexers.get_lexer_for_filename") as mock_get:
                mock_get.side_effect = Exception("No lexer")
                languages = loader._detect_languages(tmp_path)
                assert len(languages) == 0
