"""Kernel test package with a lightweight local LiteLLM stub."""

import sys
from types import ModuleType
from unittest.mock import MagicMock

if "litellm" not in sys.modules:
    fake = ModuleType("litellm")
    fake.validate_environment = MagicMock(return_value={"keys_in_environment": True})
    fake.acompletion = MagicMock()
    sys.modules["litellm"] = fake
