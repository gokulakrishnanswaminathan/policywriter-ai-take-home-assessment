"""PDF file parser using pdfplumber."""

from __future__ import annotations

from resume_parser.exceptions import ParsingError
from resume_parser.parsers.base import FileParser


class PDFParser(FileParser):
    """Extracts text from PDF files using pdfplumber.

    Reads all pages and concatenates their text content, including
    text found within tables.
    """

    def parse(self, file_path: str) -> str:
        """Extract text from a PDF file.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Concatenated text from all pages.

        Raises:
            FileNotFoundError: If the file does not exist.
            ParsingError: If the PDF cannot be read.
        """
        path = self._validate_file_exists(file_path)

        try:
            import pdfplumber
        except ImportError as exc:
            raise ParsingError(
                "pdfplumber is required to parse PDF files. "
                "Install it with: pip install pdfplumber"
            ) from exc

        try:
            pages_text: list[str] = []
            with pdfplumber.open(path) as pdf:
                self.logger.info(
                    "Opened PDF '%s' with %d page(s)", path.name, len(pdf.pages)
                )
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    if text:
                        pages_text.append(text)
                    else:
                        self.logger.debug("Page %d has no extractable text", i + 1)

            full_text = "\n".join(pages_text)
            self.logger.info(
                "Extracted %d characters from '%s'", len(full_text), path.name
            )
            return full_text

        except Exception as exc:
            if isinstance(exc, (FileNotFoundError, ParsingError)):
                raise
            raise ParsingError(
                f"Failed to parse PDF file '{path.name}': {exc}"
            ) from exc
