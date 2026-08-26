import os
import zipfile
import tempfile
import shutil
from git import Repo, GitCommandError
from urllib.parse import urlparse
from typing import Dict, Any, Tuple, List
import logging

logger = logging.getLogger(__name__)

class CodebaseLoader:
    def __init__(self):
        self.max_files = int(os.environ.get('CODEBASE_LIMIT', 500))
        self.max_zip_size = int(os.environ.get('ZIP_SIZE_LIMIT', 10485760)) # 10MB
        self.allowed_extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.go': 'Go',
            '.rs': 'Rust',
            '.java': 'Java',
            '.c': 'C',
            '.cpp': 'C++',
            '.h': 'C/C++ Header',
            '.cs': 'C#'
        }

    def _is_valid_github_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            return parsed.scheme in ['http', 'https'] and parsed.netloc in ['github.com', 'www.github.com']
        except Exception:
            return False

    def load_from_git(self, url: str) -> Dict[str, Any]:
        """Clone GitHub repo, return path and stats."""
        if not self._is_valid_github_url(url):
            return {"status": "error", "message": "Invalid GitHub URL."}

        try:
            # Create a temporary directory for the clone
            extract_path = tempfile.mkdtemp(prefix="codegraphx_git_")
            
            # Shallow clone, no submodules
            Repo.clone_from(url, extract_path, depth=1, recursive=False)
            
            repo_name = urlparse(url).path.strip('/')
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]

            file_count, languages = self._analyze_directory(extract_path)
            
            reported_count = min(file_count, self.max_files)
            
            return {
                "status": "success",
                "path": extract_path,
                "repo_name": repo_name,
                "file_count": reported_count,
                "languages": languages
            }

        except GitCommandError as e:
            return {"status": "error", "message": f"Git clone failed: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Error cloning repo: {str(e)}"}

    def load_from_zip(self, zip_path: str) -> Dict[str, Any]:
        """Extract ZIP, validate, return path and stats."""
        try:
            # Check file size before doing anything
            if os.path.getsize(zip_path) > self.max_zip_size:
                return {"status": "error", "message": "ZIP file exceeds 10MB limit."}
                
            if not zipfile.is_zipfile(zip_path):
                return {"status": "error", "message": "Invalid ZIP file."}

            extract_path = tempfile.mkdtemp(prefix="codegraphx_zip_")

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # ZipSlip prevention and size validation during extraction
                total_size = 0
                for zip_info in zip_ref.filelist:
                    # Zip slip check
                    if zip_info.filename.startswith('/') or '..' in zip_info.filename:
                        shutil.rmtree(extract_path)
                        return {"status": "error", "message": "Invalid ZIP archive: potential directory traversal (ZipSlip)."}
                    
                    total_size += zip_info.file_size
                    if total_size > self.max_zip_size:
                        shutil.rmtree(extract_path)
                        return {"status": "error", "message": "Extracted contents exceed 10MB limit."}

                zip_ref.extractall(extract_path)

            file_count, languages = self._analyze_directory(extract_path)
            reported_count = min(file_count, self.max_files)

            return {
                "status": "success",
                "path": extract_path,
                "file_count": reported_count,
                "languages": languages
            }

        except Exception as e:
            return {"status": "error", "message": f"Error extracting ZIP: {str(e)}"}

    def _analyze_directory(self, path: str) -> Tuple[int, List[str]]:
        file_count = 0
        languages_found = set()

        for root, _, files in os.walk(path):
            if '.git' in root:
                continue
            for file in files:
                file_count += 1
                _, ext = os.path.splitext(file)
                if ext in self.allowed_extensions:
                    languages_found.add(self.allowed_extensions[ext])

        return file_count, list(languages_found)
