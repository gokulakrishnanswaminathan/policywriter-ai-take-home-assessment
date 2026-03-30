"""Abstract base class for field extractors (Strategy pattern)."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any


class FieldExtractor(ABC):
    """Abstract base class for field extractors.

    Implements the Strategy pattern: each concrete extractor encapsulates
    one algorithm for extracting a single field from resume text. Extractors
    are interchangeable — the coordinator depends only on this interface.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def extract(self, text: str) -> Any:
        """Extract a field value from raw resume text.

        Args:
            text: The full text content of the resume.

        Returns:
            The extracted value. Type depends on the concrete extractor:
            - str | None for name and email extractors
            - list[str] for skills extractors

        Raises:
            ExtractionError: If extraction fails unrecoverably.
        """
        ...
