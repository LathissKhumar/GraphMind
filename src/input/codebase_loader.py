import os
import shutil
import tempfile
import zipfile
import git
from git.exc import GitCommandError, GitCommandNotFound
from pathlib import Path
from urllib.parse import urlparse
from typing import TypedDict

from pygments.lexers import get_lexer_for_filename, guess_lexer_for_filename


CODEBASE_LIMIT = int(os.getenv("CODEBASE_LIMIT", "500"))
ZIP_SIZE_LIMIT = int(os.getenv("ZIP_SIZE_LIMIT", "10485760"))


class LoadResult(TypedDict):
    status: str
    repo_name: str
    path: str
    file_count: int
    total_files: int
    languages: list[str]
    source: str
    cloned_from: str


class CodebaseLoader:
    def __init__(self, storage_dir: str = ".codebase"):
        self.storage_dir: Path = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def load_from_git(self, url: str) -> LoadResult:
        if not self._is_valid_github_url(url):
            raise ValueError(f"Invalid GitHub URL: {url}")

        repo_name = self._extract_repo_name(url)
        target_dir = self.storage_dir / repo_name

        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)

        try:
            git.Repo.clone_from(url, target_dir, depth=1, single_branch=True)
        except GitCommandNotFound as e:
            raise RuntimeError(f"Git not found on system: {e}") from e
        except GitCommandError as e:
            raise RuntimeError(f"Failed to clone repository: {e}") from e
        except Exception as e:
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to clone repository: {e}") from e

        total_files = self._count_files(target_dir)
        languages = self._detect_languages(target_dir)

        return {
            "status": "success",
            "repo_name": repo_name,
            "path": str(target_dir),
            "file_count": min(total_files, CODEBASE_LIMIT),
            "total_files": total_files,
            "languages": languages,
            "source": "git",
            "cloned_from": url,
        }

    def load_from_zip(self, zip_path: str) -> LoadResult:
        path = Path(zip_path)

        if not path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        if not zipfile.is_zipfile(path):
            raise ValueError(f"Not a valid ZIP file: {zip_path}")

        file_size = path.stat().st_size
        if file_size > ZIP_SIZE_LIMIT:
            limit_mb = ZIP_SIZE_LIMIT / (1024 * 1024)
            raise ValueError(
                f"ZIP file too large: {file_size / (1024 * 1024):.1f}MB (max: {limit_mb:.1f}MB)"
            )

        with zipfile.ZipFile(path, "r") as zf:
            bad_file = zf.testzip()
            if bad_file is not None:
                raise ValueError(f"Corrupt ZIP: bad member '{bad_file}'")

            members = zf.namelist()
            file_members = [m for m in members if not m.endswith("/")]
            total_files = len(file_members)

            if total_files > CODEBASE_LIMIT * 10:
                max_files = CODEBASE_LIMIT * 10
                raise ValueError(
                    f"Too many files in ZIP: {total_files} (max: {max_files})"
                )

            top_level = self._get_top_level_name(members)
            final_dir = self.storage_dir / top_level

            if final_dir.exists():
                shutil.rmtree(final_dir, ignore_errors=True)

            staging_dir = Path(tempfile.mkdtemp(dir=self.storage_dir, prefix=".zip_staging_"))
            try:
                for member in members:
                    resolved = self._safe_extract_path(staging_dir, member)
                    if member.endswith("/"):
                        resolved.mkdir(parents=True, exist_ok=True)
                    else:
                        resolved.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as src, open(resolved, "wb") as dst:
                            shutil.copyfileobj(src, dst)

                shutil.move(str(staging_dir / top_level), str(final_dir))
            except Exception as e:
                if final_dir.exists():
                    shutil.rmtree(final_dir, ignore_errors=True)
                raise RuntimeError(f"Failed to extract ZIP: {e}") from e
            finally:
                if staging_dir.exists():
                    shutil.rmtree(staging_dir, ignore_errors=True)

        total_files = self._count_files(final_dir)
        languages = self._detect_languages(final_dir)

        return {
            "status": "success",
            "repo_name": top_level,
            "path": str(final_dir),
            "file_count": min(total_files, CODEBASE_LIMIT),
            "total_files": total_files,
            "languages": languages,
            "source": "zip",
            "cloned_from": "",
        }

    def _safe_extract_path(self, base_dir: Path, member: str) -> Path:
        resolved = (base_dir / member).resolve()
        base_resolved = base_dir.resolve()

        if not str(resolved).startswith(str(base_resolved) + os.sep) and resolved != base_resolved:
            raise ValueError(f"ZipSlip detected: '{member}' escapes extraction directory")

        if ".." in Path(member).parts:
            raise ValueError(f"Unsafe path in ZIP member: '{member}'")

        return resolved

    def _is_valid_github_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        if parsed.netloc not in ("github.com", "www.github.com"):
            return False
        parts = parsed.path.strip("/").split("/")
        return len(parts) == 2 and all(parts)

    def _extract_repo_name(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return path.lstrip("/").replace("/", "_")

    def _count_files(self, directory: Path) -> int:
        count = 0
        for root, dirs, files in os.walk(directory):
            dir_parts = Path(root).parts
            if "__pycache__" in dir_parts or ".git" in dir_parts:
                dirs.clear()
                continue
            count += len([f for f in files if not f.startswith(".")])
        return count

    def _detect_languages(self, directory: Path) -> list[str]:
        languages: set[str] = set()

        for root, dirs, files in os.walk(directory):
            dir_parts = Path(root).parts
            if "__pycache__" in dir_parts or ".git" in dir_parts:
                dirs.clear()
                continue
            for filename in files:
                if filename.startswith("."):
                    continue
                filepath = Path(root) / filename
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(4096)
                    if content:
                        lexer = guess_lexer_for_filename(filename, content)
                        languages.add(lexer.name)
                except (OSError, ValueError):
                    try:
                        lexer = get_lexer_for_filename(filename)
                        languages.add(lexer.name)
                    except (OSError, ValueError):
                        pass

        return sorted(languages)[:5]

    def _get_top_level_name(self, names: list[str]) -> str:
        for name in names:
            if name and "/" in name:
                return name.split("/")[0]
        return "extracted"
