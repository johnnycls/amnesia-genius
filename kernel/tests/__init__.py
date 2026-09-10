"""Kernel tests with a fallback LiteLLM stub for dependency-free local runs."""

import importlib.util
import sys
from types import ModuleType
from unittest.mock import MagicMock

if "litellm" not in sys.modules and importlib.util.find_spec("litellm") is None:
    fake = ModuleType("litellm")
    fake.validate_environment = MagicMock(return_value={"keys_in_environment": True})
    fake.acompletion = MagicMock()
    sys.modules["litellm"] = fake
