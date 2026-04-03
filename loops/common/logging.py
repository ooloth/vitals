"""Shared logger for the vitals agent loops."""

import logging
import sys

logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    stream=sys.stderr,
    force=True,
)

log = logging.getLogger("vitals")
