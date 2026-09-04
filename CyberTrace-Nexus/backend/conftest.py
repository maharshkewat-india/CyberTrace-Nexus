"""
conftest.py - pytest fixtures shared by all test files.

Provides a `result` TestResult object so tests written in a procedural
style (without a `result` fixture parameter) still work under pytest.
"""

import pytest


class TestResult:
    """Simple result accumulator for procedural tests."""

    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.errors: list = []


@pytest.fixture
def result() -> TestResult:
    """A TestResult instance that tests can populate for aggregation."""
    return TestResult()
