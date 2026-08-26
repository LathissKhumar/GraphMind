#!/usr/bin/env python3
"""QA scenarios for Task 1: Codebase Input Handler."""

import os
import sys
import zipfile
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.input.codebase_loader import CodebaseLoader, CODEBASE_LIMIT, ZIP_SIZE_LIMIT

EVIDENCE_DIR = Path(".sisyphus/evidence")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

def write_evidence(name: str, content: str):
    path = EVIDENCE_DIR / name
    with open(path, "w") as f:
        f.write(content)
    print(f"  Evidence: {path}")

def scenario_git_clone():
    print("\n=== Scenario: Clone public repo ===")
    loader = CodebaseLoader(storage_dir=".codebase_test")
    try:
        result = loader.load_from_git("https://github.com/fastapi/fastapi")
        assert result["status"] == "success", f"Status not success: {result['status']}"
        assert result["repo_name"], "No repo name"
        assert Path(result["path"]).exists(), "Path does not exist"
        py_files = list(Path(result["path"]).rglob("*.py"))
        assert len(py_files) > 0, "No .py files found"
        print(f"  PASS: Cloned '{result['repo_name']}' -> {result['path']}")
        print(f"  Files: {result['file_count']}, Languages: {result['languages']}")
        write_evidence("task-1-git-clone.txt",
            f"Status: {result['status']}\n"
            f"Repo: {result['repo_name']}\n"
            f"Path: {result['path']}\n"
            f"Files: {result['file_count']}\n"
            f"Total: {result['total_files']}\n"
            f"Languages: {result['languages']}\n"
            f"Source: {result['source']}\n"
            f"Cloned from: {result['cloned_from']}\n"
            f"Python files found: {len(py_files)}\n")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        write_evidence("task-1-git-clone.txt", f"FAIL: {e}")
        return False
    finally:
        shutil.rmtree(".codebase_test", ignore_errors=True)

def scenario_valid_zip():
    print("\n=== Scenario: Upload valid ZIP ===")
    loader = CodebaseLoader(storage_dir=".codebase_test")
    tmpdir = tempfile.mkdtemp()
    zip_path = os.path.join(tmpdir, "test_repo.zip")

    try:
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test_repo/main.py", "def hello():\n    return 'world'\n")
            zf.writestr("test_repo/utils.py", "def helper():\n    pass\n")
            zf.writestr("test_repo/config.py", "DEBUG = True\n")

        result = loader.load_from_zip(zip_path)
        assert result["status"] == "success", f"Status not success: {result['status']}"
        assert result["repo_name"] == "test_repo", f"Wrong repo name: {result['repo_name']}"
        assert Path(result["path"]).exists(), "Path does not exist"
        py_files = list(Path(result["path"]).rglob("*.py"))
        assert len(py_files) == 3, f"Expected 3 .py files, got {len(py_files)}"
        print(f"  PASS: Extracted '{result['repo_name']}' -> {result['path']}")
        print(f"  Files: {result['file_count']}, Languages: {result['languages']}")
        write_evidence("task-1-zip-upload.txt",
            f"Status: {result['status']}\n"
            f"Repo: {result['repo_name']}\n"
            f"Path: {result['path']}\n"
            f"Files: {result['file_count']}\n"
            f"Total: {result['total_files']}\n"
            f"Languages: {result['languages']}\n"
            f"Source: {result['source']}\n"
            f"Python files: {len(py_files)}\n")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        write_evidence("task-1-zip-upload.txt", f"FAIL: {e}")
        return False
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        shutil.rmtree(".codebase_test", ignore_errors=True)

def scenario_invalid_zip():
    print("\n=== Scenario: Reject invalid ZIP ===")
    loader = CodebaseLoader(storage_dir=".codebase_test")
    tmpdir = tempfile.mkdtemp()

    try:
        corrupt_path = os.path.join(tmpdir, "corrupt.zip")
        with open(corrupt_path, "wb") as f:
            f.write(b"this is not a zip file at all")

        try:
            loader.load_from_zip(corrupt_path)
            print("  FAIL: Should have raised ValueError")
            write_evidence("task-1-invalid-zip.txt", "FAIL: No exception raised")
            return False
        except ValueError as e:
            print(f"  PASS: ValueError raised: {e}")
            write_evidence("task-1-invalid-zip.txt",
                f"PASS: ValueError raised for corrupt ZIP\nError: {e}\n")
            return True
        except Exception as e:
            print(f"  FAIL: Wrong exception type: {type(e).__name__}: {e}")
            write_evidence("task-1-invalid-zip.txt", f"FAIL: {type(e).__name__}: {e}")
            return False
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        shutil.rmtree(".codebase_test", ignore_errors=True)

def scenario_file_limit():
    print("\n=== Scenario: Enforce 500-file limit ===")
    loader = CodebaseLoader(storage_dir=".codebase_test")
    tmpdir = tempfile.mkdtemp()
    zip_path = os.path.join(tmpdir, "large_repo.zip")

    try:
        with zipfile.ZipFile(zip_path, "w") as zf:
            for i in range(600):
                zf.writestr(f"large_repo/file_{i:04d}.py", f"# File {i}\ndef func_{i}(): pass\n")

        result = loader.load_from_zip(zip_path)
        assert result["status"] == "success", f"Status not success: {result['status']}"
        assert result["total_files"] == 600, f"Expected 600 total, got {result['total_files']}"
        assert result["file_count"] == CODEBASE_LIMIT, (
            f"Expected file_count={CODEBASE_LIMIT}, got {result['file_count']}"
        )
        print(f"  PASS: Total files={result['total_files']}, Reported for parsing={result['file_count']}")
        write_evidence("task-1-file-limit.txt",
            f"Total files in ZIP: {result['total_files']}\n"
            f"Files reported for parsing: {result['file_count']}\n"
            f"CODEBASE_LIMIT: {CODEBASE_LIMIT}\n"
            f"PASS: file_count capped at {CODEBASE_LIMIT}\n")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        write_evidence("task-1-file-limit.txt", f"FAIL: {e}")
        return False
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        shutil.rmtree(".codebase_test", ignore_errors=True)

def scenario_zip_size_limit():
    print("\n=== Scenario: Enforce 10MB ZIP limit ===")
    loader = CodebaseLoader(storage_dir=".codebase_test")
    tmpdir = tempfile.mkdtemp()
    oversized_path = os.path.join(tmpdir, "oversized.zip")

    try:
        with zipfile.ZipFile(oversized_path, "w") as zf:
            data = b"x" * (ZIP_SIZE_LIMIT + 1024)
            zf.writestr("big_file.bin", data)

        try:
            loader.load_from_zip(oversized_path)
            print("  FAIL: Should have raised ValueError")
            write_evidence("task-1-zip-size.txt", "FAIL: No exception raised")
            return False
        except ValueError as e:
            print(f"  PASS: ValueError raised: {e}")
            write_evidence("task-1-zip-size.txt",
                f"PASS: ValueError raised for oversized ZIP\nError: {e}\n"
                f"ZIP_SIZE_LIMIT: {ZIP_SIZE_LIMIT} bytes ({ZIP_SIZE_LIMIT / (1024*1024):.1f}MB)\n")
            return True
        except Exception as e:
            print(f"  FAIL: Wrong exception type: {type(e).__name__}: {e}")
            write_evidence("task-1-zip-size.txt", f"FAIL: {type(e).__name__}: {e}")
            return False
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        shutil.rmtree(".codebase_test", ignore_errors=True)

if __name__ == "__main__":
    results = []
    results.append(("Git clone", scenario_git_clone()))
    results.append(("Valid ZIP", scenario_valid_zip()))
    results.append(("Invalid ZIP", scenario_invalid_zip()))
    results.append(("500-file limit", scenario_file_limit()))
    results.append(("10MB ZIP limit", scenario_zip_size_limit()))

    print("\n" + "=" * 50)
    print("QA Results Summary:")
    all_pass = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_pass = False

    print(f"\nOverall: {'ALL PASS' if all_pass else 'SOME FAILED'}")
    sys.exit(0 if all_pass else 1)
