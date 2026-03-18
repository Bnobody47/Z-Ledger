"""
Double-decision concurrency test: two concurrent asyncio tasks appending to the same
stream at expected_version=3. Asserts exactly one succeeds, one raises
OptimisticConcurrencyError, and total stream length = 4.
"""
import pytest


@pytest.mark.asyncio
async def test_double_decision_concurrency():
    """
    Two AI agents simultaneously attempt to append CreditAnalysisCompleted to the same
    loan application stream. Both read at version 3 and pass expected_version=3.
    Exactly one must succeed. The other must receive OptimisticConcurrencyError.
    Total events appended = 4 (not 5).
    """
    raise NotImplementedError
