"""Tests for the ResumeExtractor coordinator."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from resume_parser.coordinator import ResumeExtractor
from resume_parser.exceptions import ExtractionError
from resume_parser.extractors.base import FieldExtractor
from resume_parser.models import ResumeData


def _make_mock_extractor(return_value) -> FieldExtractor:
    """Create a mock FieldExtractor that returns the given value."""
    mock = MagicMock(spec=FieldExtractor)
    mock.extract.return_value = return_value
    mock.__class__.__name__ = "MockExtractor"
    return mock


def _make_failing_extractor(error: Exception) -> FieldExtractor:
    """Create a mock FieldExtractor that raises the given error."""
    mock = MagicMock(spec=FieldExtractor)
    mock.extract.side_effect = error
    mock.__class__.__name__ = "FailingExtractor"
    return mock


class TestResumeExtractorHappyPath:
    """Test successful extraction coordination."""

    def test_all_extractors_succeed(self):
        """All fields are populated when all extractors succeed."""
        extractors = {
            "name": _make_mock_extractor("Jane Doe"),
            "email": _make_mock_extractor("jane@example.com"),
            "skills": _make_mock_extractor(["Python", "ML"]),
        }
        coordinator = ResumeExtractor(extractors)
        result = coordinator.extract("Resume text here")

        assert result.name == "Jane Doe"
        assert result.email == "jane@example.com"
        assert result.skills == ["Python", "ML"]

    def test_subset_of_fields(self):
        """Works correctly with a subset of field extractors."""
        extractors = {
            "email": _make_mock_extractor("jane@example.com"),
        }
        coordinator = ResumeExtractor(extractors)
        result = coordinator.extract("Resume text")

        assert result.email == "jane@example.com"
        assert result.name is None
        assert result.skills == []

    def test_returns_resume_data_instance(self):
        """The result is a ResumeData instance."""
        extractors = {"name": _make_mock_extractor("Jane")}
        coordinator = ResumeExtractor(extractors)
        result = coordinator.extract("text")
        assert isinstance(result, ResumeData)


class TestResumeExtractorPartialFailure:
    """Test resilience when individual extractors fail."""

    def test_one_extractor_fails_others_succeed(self):
        """A failing extractor doesn't prevent other fields from populating."""
        extractors = {
            "name": _make_mock_extractor("Jane Doe"),
            "email": _make_failing_extractor(
                ExtractionError("Email extraction failed")
            ),
            "skills": _make_mock_extractor(["Python"]),
        }
        coordinator = ResumeExtractor(extractors)
        result = coordinator.extract("Resume text")

        assert result.name == "Jane Doe"
        assert result.email is None  # Failed, falls back to default
        assert result.skills == ["Python"]

    def test_all_extractors_fail(self):
        """Returns default ResumeData when all extractors fail."""
        extractors = {
            "name": _make_failing_extractor(ExtractionError("fail")),
            "email": _make_failing_extractor(ExtractionError("fail")),
            "skills": _make_failing_extractor(ExtractionError("fail")),
        }
        coordinator = ResumeExtractor(extractors)
        result = coordinator.extract("Resume text")

        assert result.name is None
        assert result.email is None
        assert result.skills == []

    def test_unexpected_exception_handled(self):
        """Non-ExtractionError exceptions are also caught gracefully."""
        extractors = {
            "name": _make_failing_extractor(RuntimeError("unexpected")),
            "email": _make_mock_extractor("jane@test.com"),
        }
        coordinator = ResumeExtractor(extractors)
        result = coordinator.extract("text")

        assert result.name is None
        assert result.email == "jane@test.com"


class TestResumeExtractorValidation:
    """Test input validation."""

    def test_invalid_field_name_raises_value_error(self):
        """Raises ValueError for unrecognized field names."""
        with pytest.raises(ValueError, match="Invalid field name"):
            ResumeExtractor({"phone": _make_mock_extractor("555-1234")})

    def test_non_extractor_instance_raises_type_error(self):
        """Raises TypeError when extractor is not a FieldExtractor."""
        with pytest.raises(TypeError, match="must be a FieldExtractor"):
            ResumeExtractor({"name": "not an extractor"})

    def test_empty_extractors_dict(self):
        """Works with an empty extractors dict, returns defaults."""
        coordinator = ResumeExtractor({})
        result = coordinator.extract("text")
        assert result == ResumeData()

    def test_empty_text_passed_to_extractors(self):
        """Extractors receive empty text; they handle it gracefully."""
        extractors = {
            "name": _make_mock_extractor(None),
            "email": _make_mock_extractor(None),
        }
        coordinator = ResumeExtractor(extractors)
        result = coordinator.extract("")

        assert result.name is None
        assert result.email is None
