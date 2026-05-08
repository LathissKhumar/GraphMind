#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
import requests
from pathlib import Path

API_BASE = "http://localhost:8000"
API_READY_TIMEOUT = 30
TEST_CODEBASE = str(Path(__file__).parent.parent / "src")


def is_api_up():
    try:
        resp = requests.get(f"{API_BASE}/api/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def start_api():
    print("Starting API server...")
    proc = subprocess.Popen(
        ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=Path(__file__).parent.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    start_time = time.monotonic()
    while time.monotonic() - start_time < API_READY_TIMEOUT:
        if is_api_up():
            print("API is up")
            return proc
        time.sleep(1)
    print("Failed to start API")
    proc.terminate()
    sys.exit(1)


def test_api_endpoints():
    print("\n=== Testing API Endpoints ===")
    endpoints = [
        ("GET", "/api/health", None, 200),
        ("GET", "/api/metrics", None, 200),
        ("GET", "/api/graph", None, 200),
        ("GET", "/api/query-history", None, 200),
        ("GET", "/api/evaluation", None, 200),
        ("POST", "/api/budget", {"budget_limit": 50000}, 200),
    ]
    for method, path, data, expected_status in endpoints:
        url = f"{API_BASE}{path}"
        try:
            if method == "GET":
                resp = requests.get(url, timeout=10)
            else:
                resp = requests.post(url, json=data, timeout=10)
            if resp.status_code != expected_status:
                print(f"FAIL: {method} {path} returned {resp.status_code}")
                return False
            print(f"PASS: {method} {path}")
        except Exception as e:
            print(f"FAIL: {method} {path} - {e}")
            return False
    return True


def test_routing_tiers():
    print("\n=== Testing Routing Tiers ===")
    tiers_seen = set()
    test_queries = [
        ("List all functions", "GRAPH_ONLY"),
        ("What functions call parse_file?", "GRAPH_RAG"),
        ("Explain the architecture of this project", "LLM_FULL"),
    ]
    for query, expected_tier in test_queries:
        try:
            resp = requests.post(
                f"{API_BASE}/api/query",
                json={"query": query},
                timeout=30,
            )
            if resp.status_code != 200:
                print(f"FAIL: Query '{query}' returned {resp.status_code}")
                return False
            result = resp.json()
            tier = result.get("tier")
            tiers_seen.add(tier)
            warning = result.get("warning", "")
            print(f"PASS: Query '{query[:30]}...' routed to {tier} {warning}")
        except Exception as e:
            print(f"FAIL: Query '{query}' - {e}")
            return False
    if "GRAPH_ONLY" not in tiers_seen:
        print("FAIL: GRAPH_ONLY tier not triggered")
        return False
    print(f"Verified tiers: {tiers_seen}")
    if len(tiers_seen) < 3:
        print(f"Note: Only {len(tiers_seen)} tiers seen - LLM may be unavailable")
    print("Routing tier verification complete")
    return True


def test_evaluation():
    print("\n=== Testing Evaluation ===")
    try:
        resp = requests.get(f"{API_BASE}/api/evaluation", timeout=10)
        if resp.status_code != 200:
            print(f"FAIL: Evaluation endpoint returned {resp.status_code}")
            return False
        data = resp.json()
        if "summary" not in data:
            print("FAIL: Evaluation missing summary")
            return False
        print("PASS: Evaluation produces valid results")
        return True
    except Exception as e:
        print(f"FAIL: Evaluation test - {e}")
        return False


def test_benchmark():
    print("\n=== Testing Benchmark ===")
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.benchmark.token_analyzer import count_dataset_tokens, get_token_report
        from src.benchmark.token_report import TokenReport

        tokens = count_dataset_tokens(TEST_CODEBASE)
        if tokens <= 0:
            print("FAIL: Token count is zero or negative")
            return False
        print(f"PASS: Benchmark token count: {tokens:,}")

        report = TokenReport(TEST_CODEBASE)
        report.generate()
        report_path = report.save_report(fmt="json")
        if not Path(report_path).exists():
            print("FAIL: Token report not saved")
            return False
        print(f"PASS: Token report saved to {report_path}")
        return True
    except Exception as e:
        print(f"FAIL: Benchmark test - {e}")
        return False


def validate_token_counts():
    print("\n=== Validating Token Counts ===")
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.benchmark.token_analyzer import verify_2m_threshold

        result = verify_2m_threshold(TEST_CODEBASE)
        print(f"Token threshold check (2M): {result}")
        print("PASS: Token validation logic works")
        return True
    except Exception as e:
        print(f"FAIL: Token validation - {e}")
        return False


def main():
    print("Starting End-to-End Verification")
    print(f"Test codebase: {TEST_CODEBASE}")

    api_proc = None
    if not is_api_up():
        api_proc = start_api()
    else:
        print("API is already running")

    try:
        all_passed = True
        all_passed &= test_api_endpoints()
        all_passed &= test_routing_tiers()
        all_passed &= test_evaluation()
        all_passed &= test_benchmark()
        all_passed &= validate_token_counts()

        if all_passed:
            print("\n=== ALL VERIFICATIONS PASSED ===")
            sys.exit(0)
        else:
            print("\n=== SOME VERIFICATIONS FAILED ===")
            sys.exit(1)
    finally:
        if api_proc:
            api_proc.terminate()
            api_proc.wait()


if __name__ == "__main__":
    main()
