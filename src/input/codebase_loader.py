import os
import shutil
import zipfile
import git
from pathlib import Path
from urllib.parse import urlparse
from typing import TypedDict

from pygments.lexers import get_lexer_by_filename, guess_lexer_for_filename


CODEBASE_LIMIT = int(os.getenv("CODEBASE_LIMIT", "500"))
ZIP_SIZE_LIMIT = int(os.getenv("ZIP_SIZE_LIMIT", "10485760"))


class LoadResult(TypedDict):
    status: str
    repo_name: str
    path: str
    file_count: int
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
            shutil.rmtree(target_dir)
        
        try:
            git.Repo.clone_from(url, target_dir, depth=1, single_branch=True)
        except Exception as e:
            raise RuntimeError(f"Failed to clone repository: {e}")
        
        file_count = self._count_files(target_dir)
        languages = self._detect_languages(target_dir)
        
        return {
            "status": "success",
            "repo_name": repo_name,
            "path": str(target_dir),
            "file_count": file_count,
            "languages": languages,
            "source": "git",
            "cloned_from": url
        }
    
    def load_from_zip(self, zip_path: str) -> LoadResult:
        path = Path(zip_path)
        
        if not path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")
        
        if not zipfile.is_zipfile(path):
            raise ValueError("Invalid ZIP file")
        
        file_size = path.stat().st_size
        if file_size > ZIP_SIZE_LIMIT:
            raise ValueError(f"ZIP file too large: {file_size} bytes (max: {ZIP_SIZE_LIMIT})")
        
       
        
        with zipfile.ZipFile(path, 'r') as zf:
            members = zf.namelist()
            member_count = len([m for m in members if not m.endswith("/")])
            if member_count > CODEBASE_LIMIT * 10:
                raise ValueError(f"Too many files in ZIP: {member_count} (max: {CODEBASE_LIMIT * 10})")
            
            top_level = self._get_top_level_name(members)
            extract_dir = self.storage_dir / top_level
            
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            
            zf.extractall(self.storage_dir)
        
        file_count = self._count_files(extract_dir)
        languages = self._detect_languages(extract_dir)
        
        return {
            "status": "success",
            "repo_name": top_level,
            "path": str(extract_dir),
            "file_count": file_count,
            "languages": languages,
            "source": "zip",
            "cloned_from": ""
        }
    
    def _is_valid_github_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc in ("github.com", "www.github.com") and parsed.path.endswith((".git", ""))
    
    def _extract_repo_name(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.rstrip(".git")
        return path.lstrip("/").replace("/", "_")
    
    def _count_files(self, directory: Path) -> int:
        count = 0
        for root, _, files in os.walk(directory):
            if "__pycache__" in root or ".git" in root:
                continue
            count += len([f for f in files if not f.startswith(".")])
        return min(count, CODEBASE_LIMIT)
    
    def _detect_languages(self, directory: Path) -> list[str]:
        exts: set[str] = set()
        
        # Fallback dictionary for common file extensions
        ext_to_language = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.html': 'HTML',
            '.css': 'CSS',
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.xml': 'XML',
            '.sql': 'SQL',
            '.sh': 'Shell',
        }
        
        for root, _, files in os.walk(directory):
            if "__pycache__" in root or ".git" in root:
                continue
            for f in files:
                try:
                    lexer = get_lexer_by_filename(f)
                    exts.add(lexer.name)
                except:
                    pass
                
                try:
                    filepath = Path(root) / f
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as fp:
                        content = fp.read(4096)
                    if content:
                        lexer = guess_lexer_for_filename(f, content)
                        exts.add(lexer.name)
                except:
                    pass
                
                # Fallback: use file extension
                if not any(True for _ in exts if f.endswith('.')):
                    file_ext = Path(f).suffix.lower()
                    if file_ext in ext_to_language:
                        exts.add(ext_to_language[file_ext])
        
        return sorted(list(exts))[:5]
    
    def _get_top_level_name(self, names: list[str]) -> str:
        for name in names:
            if name:
                return name.split("/")[0]
        return "extracted"