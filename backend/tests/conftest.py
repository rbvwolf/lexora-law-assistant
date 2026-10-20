"""Pytest test session configuration.

Ensures that automated test runs (such as test_api_v1.py) operate in a deterministic
offline mode by default, preventing unintended external API calls to Groq Cloud during tests.
"""

import os
import pytest

# Default to mock key for test execution so unit/integration tests don't burn Groq quota or fail offline
os.environ["GROQ_API_KEY"] = "gsk_mock_key_for_dev_mode"
