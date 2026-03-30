"""Tests for the WordParser."""

from pathlib import Path

import pytest

from resume_parser.exceptions import ParsingError
from resume_parser.parsers.word_parser import WordParser


class TestWordParserHappyPath:
    """Test successful Word document parsing scenarios."""

    def test_parse_valid_docx(self, tmp_docx: Path):
        """A valid .docx returns extracted text content."""
        parser = WordParser()
        text = parser.parse(str(tmp_docx))
        assert "Jane Doe" in text
        assert "jane.doe@gmail.com" in text

    def test_parse_docx_with_tables(self, tmp_docx_with_table: Path):
        """Tables in the document are also extracted."""
        parser = WordParser()
        text = parser.parse(str(tmp_docx_with_table))
        assert "Python" in text
        assert "Machine Learning" in text
        assert "Docker" in text


class TestWordParserEdgeCases:
    """Test Word parser error handling and edge cases."""

    def test_file_not_found(self, tmp_path: Path):
        """Raises FileNotFoundError for non-existent files."""
        parser = WordParser()
        with pytest.raises(FileNotFoundError, match="Resume file not found"):
            parser.parse(str(tmp_path / "nonexistent.docx"))

    def test_corrupted_docx(self, tmp_path: Path):
        """Raises ParsingError for corrupted/invalid .docx data."""
        bad_docx = tmp_path / "corrupted.docx"
        bad_docx.write_text("this is not a docx")
        parser = WordParser()
        with pytest.raises(ParsingError, match="Failed to parse Word"):
            parser.parse(str(bad_docx))

    def test_empty_docx(self, tmp_empty_docx: Path):
        """An empty document returns an empty string."""
        parser = WordParser()
        text = parser.parse(str(tmp_empty_docx))
        assert text == ""

    def test_returns_string_type(self, tmp_docx: Path):
        """Parser always returns a string."""
        parser = WordParser()
        text = parser.parse(str(tmp_docx))
        assert isinstance(text, str)
