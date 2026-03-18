"""
Pytest fixtures for Z Ledger tests.
"""
import pytest


@pytest.fixture
def db_url():
    """Override with DATABASE_URL env var in CI/local."""
    import os
    return os.environ.get("DATABASE_URL", "postgresql://localhost/z_ledger")
