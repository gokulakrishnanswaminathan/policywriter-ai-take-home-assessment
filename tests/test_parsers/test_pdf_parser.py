"""Tests for the PDFParser."""

from pathlib import Path

import pytest

from resume_parser.exceptions import ParsingError
from resume_parser.parsers.pdf_parser import PDFParser


class TestPDFParserHappyPath:
    """Test successful PDF parsing scenarios."""

    def test_parse_valid_pdf(self, tmp_pdf: Path):
        """A valid PDF returns extracted text content."""
        parser = PDFParser()
        text = parser.parse(str(tmp_pdf))
        assert "Jane Doe" in text
        assert "jane.doe@gmail.com" in text

    def test_parse_multipage_pdf(self, tmp_pdf_multipage: Path):
        """Multi-page PDFs have all pages concatenated."""
        parser = PDFParser()
        text = parser.parse(str(tmp_pdf_multipage))
        assert "Jane Doe" in text
        assert "Python" in text


class TestPDFParserEdgeCases:
    """Test PDF parser error handling and edge cases."""

    def test_file_not_found(self, tmp_path: Path):
        """Raises FileNotFoundError for non-existent files."""
        parser = PDFParser()
        with pytest.raises(FileNotFoundError, match="Resume file not found"):
            parser.parse(str(tmp_path / "nonexistent.pdf"))

    def test_corrupted_pdf(self, tmp_path: Path):
        """Raises ParsingError for corrupted/invalid PDF data."""
        bad_pdf = tmp_path / "corrupted.pdf"
        bad_pdf.write_text("this is not a pdf")
        parser = PDFParser()
        with pytest.raises(ParsingError, match="Failed to parse PDF"):
            parser.parse(str(bad_pdf))

    def test_empty_pdf(self, tmp_empty_pdf: Path):
        """An empty PDF returns an empty string without raising."""
        parser = PDFParser()
        text = parser.parse(str(tmp_empty_pdf))
        assert text == ""

    def test_returns_string_type(self, tmp_pdf: Path):
        """Parser always returns a string."""
        parser = PDFParser()
        text = parser.parse(str(tmp_pdf))
        assert isinstance(text, str)
