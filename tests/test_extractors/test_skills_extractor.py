"""Tests for the GeminiSkillsExtractor."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from resume_parser.exceptions import ConfigurationError, ExtractionError
from resume_parser.extractors.skills_extractor import GeminiSkillsExtractor


@pytest.fixture
def extractor() -> GeminiSkillsExtractor:
    """Create a GeminiSkillsExtractor with a dummy API key."""
    return GeminiSkillsExtractor(api_key="test-key")


def _make_mock_client(response: MagicMock) -> MagicMock:
    """Create a mock genai.Client with a models.generate_content method."""
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = response
    return mock_client


class TestGeminiSkillsExtractorHappyPath:
    """Test successful Gemini-based skills extraction."""

    def test_extracts_skills_from_valid_response(
        self, extractor: GeminiSkillsExtractor, mock_gemini_response: MagicMock
    ):
        """Parses a clean JSON array response into a skills list."""
        mock_client = _make_mock_client(mock_gemini_response)

        with patch("resume_parser.extractors.skills_extractor.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            result = extractor.extract("Skills: Python, ML, Docker, AWS")

        assert result == ["Python", "Machine Learning", "Docker", "AWS"]

    def test_handles_markdown_wrapped_response(
        self, extractor: GeminiSkillsExtractor, mock_gemini_response_markdown: MagicMock
    ):
        """Strips markdown code fences from the response."""
        mock_client = _make_mock_client(mock_gemini_response_markdown)

        with patch("resume_parser.extractors.skills_extractor.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            result = extractor.extract("Skills: Python, ML, Docker")

        assert result == ["Python", "Machine Learning", "Docker"]

    def test_deduplicates_skills(self, extractor: GeminiSkillsExtractor):
        """Duplicate skills are removed from the result."""
        response = MagicMock()
        response.text = '["Python", "Python", "Docker"]'
        mock_client = _make_mock_client(response)

        with patch("resume_parser.extractors.skills_extractor.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            result = extractor.extract("Skills: Python, Docker")

        assert result == ["Python", "Docker"]


class TestGeminiSkillsExtractorEdgeCases:
    """Test Gemini skills extractor error handling."""

    def test_missing_api_key_raises_configuration_error(self):
        """Raises ConfigurationError when no API key is available."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ConfigurationError, match="GEMINI_API_KEY"):
                GeminiSkillsExtractor(api_key=None)

    def test_api_key_from_env_variable(self):
        """Reads API key from environment variable when not passed directly."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "env-key"}):
            extractor = GeminiSkillsExtractor()
            assert extractor._api_key == "env-key"

    def test_empty_text_returns_empty_list(self, extractor: GeminiSkillsExtractor):
        """Returns empty list for empty input without calling API."""
        result = extractor.extract("")
        assert result == []

    def test_api_error_raises_extraction_error(
        self, extractor: GeminiSkillsExtractor
    ):
        """Raises ExtractionError when the Gemini API call fails."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("API timeout")

        with patch("resume_parser.extractors.skills_extractor.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            with pytest.raises(ExtractionError, match="Gemini API call failed"):
                extractor.extract("Some resume text")

    def test_malformed_json_raises_extraction_error(
        self, extractor: GeminiSkillsExtractor
    ):
        """Raises ExtractionError when the response is not valid JSON."""
        response = MagicMock()
        response.text = "Here are the skills: Python, Docker"
        mock_client = _make_mock_client(response)

        with patch("resume_parser.extractors.skills_extractor.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            with pytest.raises(ExtractionError, match="Failed to parse"):
                extractor.extract("Some resume text")

    def test_non_array_json_raises_extraction_error(
        self, extractor: GeminiSkillsExtractor
    ):
        """Raises ExtractionError when response is JSON but not an array."""
        response = MagicMock()
        response.text = '{"skills": ["Python"]}'
        mock_client = _make_mock_client(response)

        with patch("resume_parser.extractors.skills_extractor.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            with pytest.raises(ExtractionError, match="Expected a JSON array"):
                extractor.extract("Some resume text")

    def test_empty_array_response(self, extractor: GeminiSkillsExtractor):
        """Returns empty list when Gemini responds with an empty array."""
        response = MagicMock()
        response.text = "[]"
        mock_client = _make_mock_client(response)

        with patch("resume_parser.extractors.skills_extractor.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            result = extractor.extract("Resume with no obvious skills")

        assert result == []


class TestParseSkillsResponse:
    """Test the static _parse_skills_response method directly."""

    def test_clean_json_array(self):
        """Parses a clean JSON array string."""
        result = GeminiSkillsExtractor._parse_skills_response('["Python", "SQL"]')
        assert result == ["Python", "SQL"]

    def test_markdown_json_fences(self):
        """Strips ```json ... ``` wrapper."""
        result = GeminiSkillsExtractor._parse_skills_response(
            '```json\n["Python", "SQL"]\n```'
        )
        assert result == ["Python", "SQL"]

    def test_markdown_bare_fences(self):
        """Strips ``` ... ``` wrapper without json tag."""
        result = GeminiSkillsExtractor._parse_skills_response(
            '```\n["Python"]\n```'
        )
        assert result == ["Python"]

    def test_non_string_elements_converted(self):
        """Non-string elements in the array are converted to strings."""
        result = GeminiSkillsExtractor._parse_skills_response('[1, true, "Python"]')
        assert "1" in result
        assert "True" in result
        assert "Python" in result

    def test_invalid_json_raises(self):
        """Raises ExtractionError for unparseable text."""
        with pytest.raises(ExtractionError, match="Failed to parse"):
            GeminiSkillsExtractor._parse_skills_response("not json at all")
