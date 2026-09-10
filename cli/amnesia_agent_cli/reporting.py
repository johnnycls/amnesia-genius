"""User-facing CLI error reporting."""

import logging
import sys

logger = logging.getLogger(__name__)


def report_error(
    error: BaseException,
    context: str | None = None,
    *,
    include_traceback: bool = False,
) -> None:
    """Log an error and print one concise user-facing message to stderr."""
    message = f"{context}: {error}" if context else str(error)
    logger.error(message, exc_info=include_traceback)
    print(f"Error: {message}", file=sys.stderr)
