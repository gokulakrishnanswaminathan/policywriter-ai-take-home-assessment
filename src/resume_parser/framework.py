"""Top-level framework facade combining file parsing and field extraction."""

from __future__ import annotations

import logging
from pathlib import Path

from resume_parser.coordinator import ResumeExtractor
from resume_parser.exceptions import UnsupportedFileFormatError
from resume_parser.models import ResumeData
from resume_parser.parsers.base import FileParser
from resume_parser.parsers.pdf_parser import PDFParser
from resume_parser.parsers.word_parser import WordParser


class ResumeParserFramework:
    """Top-level facade that combines file parsing with field extraction.

    Automatically selects the appropriate FileParser based on the file
    extension and delegates field extraction to a ResumeExtractor.

    The framework is extensible: custom parsers can be registered for
    additional file formats via the constructor or by subclassing and
    extending PARSER_REGISTRY.
    """

    # Default mapping of file extensions to parser classes
    PARSER_REGISTRY: dict[str, type[FileParser]] = {
        ".pdf": PDFParser,
        ".docx": WordParser,
    }

    def __init__(
        self,
        resume_extractor: ResumeExtractor,
        parsers: dict[str, FileParser] | None = None,
    ) -> None:
        """Initialize the framework.

        Args:
            resume_extractor: Configured coordinator with field extractors.
            parsers: Optional mapping of file extensions to FileParser instances.
                If not provided, default parsers for .pdf and .docx are used.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self._extractor = resume_extractor
        self._parsers: dict[str, FileParser] = parsers or {
            ext: cls() for ext, cls in self.PARSER_REGISTRY.items()
        }
        self.logger.info(
            "Initialized with parsers for: %s", list(self._parsers.keys())
        )

    def _get_parser(self, file_path: str) -> FileParser:
        """Select the appropriate parser based on file extension.

        Args:
            file_path: Path to the resume file.

        Returns:
            A FileParser instance for the file's format.

        Raises:
            UnsupportedFileFormatError: If no parser is registered for the extension.
        """
        suffix = Path(file_path).suffix.lower()
        parser = self._parsers.get(suffix)

        if parser is None:
            supported = ", ".join(sorted(self._parsers.keys()))
            raise UnsupportedFileFormatError(
                f"Unsupported file format '{suffix}'. "
                f"Supported formats: {supported}"
            )

        self.logger.debug(
            "Selected %s for '%s' files",
            parser.__class__.__name__,
            suffix,
        )
        return parser

    def parse_resume(self, file_path: str) -> ResumeData:
        """Parse a resume file and extract structured data.

        This is the single entry point for the framework. It validates
        the file, parses its content, and runs field extraction.

        Args:
            file_path: Path to a .pdf or .docx resume file.

        Returns:
            A ResumeData instance with extracted name, email, and skills.

        Raises:
            FileNotFoundError: If the file does not exist.
            UnsupportedFileFormatError: If the file extension is not supported.
            ParsingError: If the file content cannot be read.
        """
        self.logger.info("Parsing resume: %s", file_path)

        # Validate file exists before selecting a parser
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        # Select parser and extract text
        parser = self._get_parser(file_path)
        raw_text = parser.parse(file_path)

        if not raw_text.strip():
            self.logger.warning(
                "No text extracted from '%s'; extraction may yield empty results",
                path.name,
            )

        # Run field extraction
        resume_data = self._extractor.extract(raw_text)
        self.logger.info("Resume parsing complete for '%s'", path.name)
        return resume_data
