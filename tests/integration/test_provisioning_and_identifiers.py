"""
Initial integration test scaffold for provisioning and identifier workflows.
"""

import pytest


pytestmark = pytest.mark.integration


@pytest.mark.skip(reason="Integration harness scaffold only; first live scenario lands next.")
def test_provision_agent_scaffold():
    """Reserve the first integration scenario file and marker wiring."""
