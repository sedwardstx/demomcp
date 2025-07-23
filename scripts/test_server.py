#!/usr/bin/env python
"""Test script for the MCP Log Analyzer server."""

import argparse
import json
import logging
import sys
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

import requests
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("test_server")


class TestResult(BaseModel):
    """Test result."""

    name: str
    success: bool
    message: str
    response: Dict[str, Any] = Field(default_factory=dict)


def run_test(name: str, func: callable, *args, **kwargs) -> TestResult:
    """Run a test function.

    Args:
        name: Test name.
        func: Test function.
        *args: Arguments for the test function.
        **kwargs: Keyword arguments for the test function.

    Returns:
        Test result.
    """
    logger.info(f"Running test: {name}")
    try:
        response = func(*args, **kwargs)
        return TestResult(
            name=name, success=True, message="Test successful", response=response
        )
    except Exception as e:
        logger.exception(f"Test failed: {e}")
        return TestResult(name=name, success=False, message=f"Test failed: {str(e)}")


def test_health(base_url: str) -> Dict[str, Any]:
    """Test health endpoint.

    Args:
        base_url: Base URL of the server.

    Returns:
        Response from the server.
    """
    response = requests.get(f"{base_url}/api/health")
    response.raise_for_status()
    return response.json()


def test_register_source(
    base_url: str, source_name: str, source_type: str, source_path: str
) -> Dict[str, Any]:
    """Test registering a log source.

    Args:
        base_url: Base URL of the server.
        source_name: Name of the source.
        source_type: Type of the source.
        source_path: Path to the source.

    Returns:
        Response from the server.
    """
    data = {
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "client_id": "test-client",
        "name": source_name,
        "type": source_type,
        "path": source_path,
        "metadata": {"test": True, "description": "Test source"},
    }
    response = requests.post(f"{base_url}/api/sources", json=data)
    response.raise_for_status()
    return response.json()


def test_list_sources(base_url: str) -> Dict[str, Any]:
    """Test listing log sources.

    Args:
        base_url: Base URL of the server.

    Returns:
        Response from the server.
    """
    response = requests.get(f"{base_url}/api/sources")
    response.raise_for_status()
    return response.json()


def test_query_logs(base_url: str, source_id: str = None) -> Dict[str, Any]:
    """Test querying logs.

    Args:
        base_url: Base URL of the server.
        source_id: Source ID to query.

    Returns:
        Response from the server.
    """
    data = {
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "client_id": "test-client",
        "query": {
            "source_ids": [source_id] if source_id else None,
            "start_time": (datetime.now() - timedelta(days=1)).isoformat(),
            "end_time": datetime.now().isoformat(),
            "limit": 10,
            "offset": 0,
        },
    }
    response = requests.post(f"{base_url}/api/query", json=data)
    response.raise_for_status()
    return response.json()


def test_analyze_logs(base_url: str, source_id: str = None) -> Dict[str, Any]:
    """Test analyzing logs.

    Args:
        base_url: Base URL of the server.
        source_id: Source ID to analyze.

    Returns:
        Response from the server.
    """
    data = {
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "client_id": "test-client",
        "query": {
            "source_ids": [source_id] if source_id else None,
            "start_time": (datetime.now() - timedelta(days=1)).isoformat(),
            "end_time": datetime.now().isoformat(),
            "limit": 10,
            "offset": 0,
        },
        "analysis_type": "summary",
        "parameters": {"include_statistics": True},
    }
    response = requests.post(f"{base_url}/api/analyze", json=data)
    response.raise_for_status()
    return response.json()


def main() -> None:
    """Run the test script."""
    parser = argparse.ArgumentParser(description="Test MCP Log Analyzer Server")
    parser.add_argument("--url", help="Server URL", default="http://localhost:5000")
    parser.add_argument(
        "--source-name", help="Log source name", default="System Event Log"
    )
    parser.add_argument("--source-type", help="Log source type", default="event")
    parser.add_argument("--source-path", help="Log source path", default="System")
    parser.add_argument("--output", help="Output file for test results", default=None)
    args = parser.parse_args()

    logger.info(f"Testing server at {args.url}")

    # Run tests
    tests = []

    # Test health
    tests.append(run_test("health", test_health, args.url))

    # Test source registration
    register_result = run_test(
        "register_source",
        test_register_source,
        args.url,
        args.source_name,
        args.source_type,
        args.source_path,
    )
    tests.append(register_result)

    # Get source ID if registration was successful
    source_id = None
    if register_result.success and "source" in register_result.response:
        source_id = register_result.response["source"]["id"]

    # Test listing sources
    tests.append(run_test("list_sources", test_list_sources, args.url))

    # Test querying logs
    tests.append(run_test("query_logs", test_query_logs, args.url, source_id))

    # Test analyzing logs
    tests.append(run_test("analyze_logs", test_analyze_logs, args.url, source_id))

    # Print test results
    logger.info("Test results:")
    success_count = 0
    for test in tests:
        status = "✅ Success" if test.success else "❌ Failure"
        logger.info(f"{status}: {test.name} - {test.message}")
        if test.success:
            success_count += 1

    logger.info(f"{success_count}/{len(tests)} tests succeeded")

    # Write test results to file if specified
    if args.output:
        with open(args.output, "w") as f:
            json.dump([test.dict() for test in tests], f, indent=2)

    # Exit with error if any test failed
    if success_count < len(tests):
        sys.exit(1)


if __name__ == "__main__":
    main()
