"""Logging configuration for the resume parser framework."""

import logging


def configure_logging(level: int = logging.INFO) -> None:
    """Configure structured logging with a consistent format.

    Args:
        level: The logging level (default: INFO).
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
