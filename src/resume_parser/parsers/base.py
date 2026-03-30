"""Abstract base class for file parsers."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from resume_parser.exceptions import ParsingError


class FileParser(ABC):
    """Abstract base class for file parsers.

    Each concrete parser reads a specific file format and returns
    the full text content as a single string.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    def _validate_file_exists(self, file_path: str) -> Path:
        """Check that the file exists and return a Path object.

        Args:
            file_path: Path to the file.

        Returns:
            A resolved Path object.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Resume file not found: {file_path}")
        return path

    @abstractmethod
    def parse(self, file_path: str) -> str:
        """Extract raw text from the given file.

        Args:
            file_path: Path to the resume file.

        Returns:
            The full text content of the file.

        Raises:
            FileNotFoundError: If the file does not exist.
            ParsingError: If the file cannot be read or decoded.
        """
        ...
