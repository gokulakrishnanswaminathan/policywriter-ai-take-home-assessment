"""Integration tests for the full resume parsing pipeline."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from resume_parser.coordinator import ResumeExtractor
from resume_parser.extractors.email_extractor import RegexEmailExtractor
from resume_parser.extractors.name_extractor import HeuristicNameExtractor
from resume_parser.extractors.skills_extractor import GeminiSkillsExtractor
from resume_parser.framework import ResumeParserFramework
from resume_parser.models import ResumeData


def _mock_gemini_context(response_text: str):
    """Create a patched genai context with a mock client returning the given text."""
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    ctx = patch("resume_parser.extractors.skills_extractor.genai")
    return ctx, mock_client


class TestEndToEndWithPDF:
    """End-to-end tests parsing a real PDF file."""

    def test_full_pipeline_pdf(self, tmp_pdf: Path):
        """Full pipeline: PDF -> parse -> extract fields -> ResumeData."""
        ctx, mock_client = _mock_gemini_context(
            '["Python", "Machine Learning", "Docker"]'
        )

        with ctx as mock_genai:
            mock_genai.Client.return_value = mock_client

            extractors = {
                "email": RegexEmailExtractor(),
                "name": HeuristicNameExtractor(),
                "skills": GeminiSkillsExtractor(api_key="test-key"),
            }
            coordinator = ResumeExtractor(extractors)
            framework = ResumeParserFramework(coordinator)

            result = framework.parse_resume(str(tmp_pdf))

        assert isinstance(result, ResumeData)
        assert result.email == "jane.doe@gmail.com"
        assert isinstance(result.skills, list)
        assert len(result.skills) > 0


class TestEndToEndWithDocx:
    """End-to-end tests parsing a real Word document."""

    def test_full_pipeline_docx(self, tmp_docx: Path):
        """Full pipeline: DOCX -> parse -> extract fields -> ResumeData."""
        ctx, mock_client = _mock_gemini_context(
            '["Python", "Machine Learning", "Docker"]'
        )

        with ctx as mock_genai:
            mock_genai.Client.return_value = mock_client

            extractors = {
                "email": RegexEmailExtractor(),
                "name": HeuristicNameExtractor(),
                "skills": GeminiSkillsExtractor(api_key="test-key"),
            }
            coordinator = ResumeExtractor(extractors)
            framework = ResumeParserFramework(coordinator)

            result = framework.parse_resume(str(tmp_docx))

        assert isinstance(result, ResumeData)
        assert result.email == "jane.doe@gmail.com"
        assert isinstance(result.skills, list)


class TestEndToEndOutputFormat:
    """Verify the output matches the expected JSON schema."""

    def test_json_output_schema(self, tmp_pdf: Path):
        """Output JSON has exactly the three required keys."""
        ctx, mock_client = _mock_gemini_context('["Python"]')

        with ctx as mock_genai:
            mock_genai.Client.return_value = mock_client

            extractors = {
                "email": RegexEmailExtractor(),
                "name": HeuristicNameExtractor(),
                "skills": GeminiSkillsExtractor(api_key="test-key"),
            }
            coordinator = ResumeExtractor(extractors)
            framework = ResumeParserFramework(coordinator)

            result = framework.parse_resume(str(tmp_pdf))

        output = result.to_dict()
        assert set(output.keys()) == {"name", "email", "skills"}
        assert isinstance(output["skills"], list)

    def test_json_serialization_roundtrip(self, tmp_pdf: Path):
        """ResumeData can be serialized to JSON and parsed back."""
        import json

        ctx, mock_client = _mock_gemini_context('["Python", "Docker"]')

        with ctx as mock_genai:
            mock_genai.Client.return_value = mock_client

            extractors = {
                "email": RegexEmailExtractor(),
                "name": HeuristicNameExtractor(),
                "skills": GeminiSkillsExtractor(api_key="test-key"),
            }
            coordinator = ResumeExtractor(extractors)
            framework = ResumeParserFramework(coordinator)

            result = framework.parse_resume(str(tmp_pdf))

        json_str = result.to_json()
        parsed = json.loads(json_str)
        assert "name" in parsed
        assert "email" in parsed
        assert "skills" in parsed
