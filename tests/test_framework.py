"""Tests for the ResumeParserFramework facade."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from resume_parser.coordinator import ResumeExtractor
from resume_parser.exceptions import UnsupportedFileFormatError
from resume_parser.extractors.base import FieldExtractor
from resume_parser.framework import ResumeParserFramework
from resume_parser.models import ResumeData
from resume_parser.parsers.base import FileParser


def _make_mock_parser(text: str = "parsed text") -> FileParser:
    """Create a mock FileParser that returns the given text."""
    mock = MagicMock(spec=FileParser)
    mock.parse.return_value = text
    return mock


def _make_mock_coordinator(
    resume_data: ResumeData | None = None,
) -> ResumeExtractor:
    """Create a mock ResumeExtractor that returns the given data."""
    mock = MagicMock(spec=ResumeExtractor)
    mock.extract.return_value = resume_data or ResumeData(
        name="Jane Doe", email="jane@test.com", skills=["Python"]
    )
    return mock


class TestResumeParserFrameworkHappyPath:
    """Test successful framework operation."""

    def test_parse_pdf_resume(self, tmp_pdf: Path):
        """Routes .pdf files to the PDF parser."""
        mock_parser = _make_mock_parser("Jane Doe\njane@test.com")
        mock_coordinator = _make_mock_coordinator()

        framework = ResumeParserFramework(
            resume_extractor=mock_coordinator,
            parsers={".pdf": mock_parser},
        )
        result = framework.parse_resume(str(tmp_pdf))

        mock_parser.parse.assert_called_once_with(str(tmp_pdf))
        mock_coordinator.extract.assert_called_once()
        assert isinstance(result, ResumeData)

    def test_parse_docx_resume(self, tmp_docx: Path):
        """Routes .docx files to the Word parser."""
        mock_parser = _make_mock_parser("Jane Doe\njane@test.com")
        mock_coordinator = _make_mock_coordinator()

        framework = ResumeParserFramework(
            resume_extractor=mock_coordinator,
            parsers={".docx": mock_parser},
        )
        result = framework.parse_resume(str(tmp_docx))

        mock_parser.parse.assert_called_once_with(str(tmp_docx))
        assert isinstance(result, ResumeData)


class TestResumeParserFrameworkEdgeCases:
    """Test framework error handling and edge cases."""

    def test_unsupported_extension(self, tmp_path: Path):
        """Raises UnsupportedFileFormatError for unknown extensions."""
        txt_file = tmp_path / "resume.txt"
        txt_file.write_text("content")

        mock_coordinator = _make_mock_coordinator()
        framework = ResumeParserFramework(resume_extractor=mock_coordinator)

        with pytest.raises(UnsupportedFileFormatError, match="Unsupported file format"):
            framework.parse_resume(str(txt_file))

    def test_file_not_found(self, tmp_path: Path):
        """Raises FileNotFoundError for non-existent files."""
        mock_coordinator = _make_mock_coordinator()
        framework = ResumeParserFramework(resume_extractor=mock_coordinator)

        with pytest.raises(FileNotFoundError, match="Resume file not found"):
            framework.parse_resume(str(tmp_path / "nonexistent.pdf"))

    def test_case_insensitive_extension(self, tmp_path: Path):
        """Handles uppercase file extensions (.PDF, .DOCX)."""
        # Create a file with uppercase extension
        pdf_file = tmp_path / "resume.PDF"
        pdf_file.write_bytes(b"fake pdf content")

        mock_parser = _make_mock_parser("Jane Doe")
        mock_coordinator = _make_mock_coordinator()

        framework = ResumeParserFramework(
            resume_extractor=mock_coordinator,
            parsers={".pdf": mock_parser},
        )
        result = framework.parse_resume(str(pdf_file))
        assert isinstance(result, ResumeData)

    def test_custom_parser_injection(self, tmp_path: Path):
        """Custom parsers can be injected for new file formats."""
        txt_file = tmp_path / "resume.txt"
        txt_file.write_text("Jane Doe\njane@test.com")

        mock_txt_parser = _make_mock_parser("Jane Doe\njane@test.com")
        mock_coordinator = _make_mock_coordinator()

        framework = ResumeParserFramework(
            resume_extractor=mock_coordinator,
            parsers={".txt": mock_txt_parser},
        )
        result = framework.parse_resume(str(txt_file))

        mock_txt_parser.parse.assert_called_once()
        assert isinstance(result, ResumeData)

    def test_default_parsers_registered(self):
        """Default parsers cover .pdf and .docx."""
        mock_coordinator = _make_mock_coordinator()
        framework = ResumeParserFramework(resume_extractor=mock_coordinator)

        assert ".pdf" in framework._parsers
        assert ".docx" in framework._parsers

    def test_empty_text_logged_but_proceeds(self, tmp_pdf: Path):
        """Empty parsed text triggers a warning but extraction still runs."""
        mock_parser = _make_mock_parser("")  # Empty text
        mock_coordinator = _make_mock_coordinator()

        framework = ResumeParserFramework(
            resume_extractor=mock_coordinator,
            parsers={".pdf": mock_parser},
        )
        result = framework.parse_resume(str(tmp_pdf))

        mock_coordinator.extract.assert_called_once_with("")
        assert isinstance(result, ResumeData)
