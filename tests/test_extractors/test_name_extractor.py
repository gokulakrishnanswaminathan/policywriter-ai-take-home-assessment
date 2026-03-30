"""Tests for SpacyNameExtractor and HeuristicNameExtractor."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from resume_parser.exceptions import ConfigurationError, ExtractionError
from resume_parser.extractors.name_extractor import (
    HeuristicNameExtractor,
    SpacyNameExtractor,
)


# ---------------------------------------------------------------------------
# SpacyNameExtractor tests
# ---------------------------------------------------------------------------

class TestSpacyNameExtractorHappyPath:
    """Test successful spaCy NER name extraction."""

    def test_extracts_person_entity(self):
        """Extracts name from a PERSON entity in the text."""
        extractor = SpacyNameExtractor()

        # Mock the spaCy model and document
        mock_ent = MagicMock()
        mock_ent.text = "Jane Doe"
        mock_ent.label_ = "PERSON"

        mock_doc = MagicMock()
        mock_doc.ents = [mock_ent]

        mock_nlp = MagicMock(return_value=mock_doc)

        with patch("resume_parser.extractors.name_extractor.spacy") as mock_spacy:
            mock_spacy.load.return_value = mock_nlp
            result = extractor.extract("Jane Doe\njane@example.com\n")

        assert result == "Jane Doe"

    def test_returns_first_person_entity(self):
        """Returns the first PERSON entity when multiple exist."""
        extractor = SpacyNameExtractor()

        ent1 = MagicMock(text="Jane Doe", label_="PERSON")
        ent2 = MagicMock(text="John Smith", label_="PERSON")
        mock_doc = MagicMock(ents=[ent1, ent2])
        mock_nlp = MagicMock(return_value=mock_doc)

        with patch("resume_parser.extractors.name_extractor.spacy") as mock_spacy:
            mock_spacy.load.return_value = mock_nlp
            result = extractor.extract("Jane Doe\nManaged by John Smith\n")

        assert result == "Jane Doe"

    def test_all_caps_name_normalized(self):
        """All-caps lines are normalized to title case before NER."""
        extractor = SpacyNameExtractor()

        mock_ent = MagicMock()
        mock_ent.text = "Gokulakrishnan Swaminathan"
        mock_ent.label_ = "PERSON"

        mock_doc = MagicMock()
        mock_doc.ents = [mock_ent]

        mock_nlp = MagicMock(return_value=mock_doc)

        with patch("resume_parser.extractors.name_extractor.spacy") as mock_spacy:
            mock_spacy.load.return_value = mock_nlp
            # Input has all-caps name line — should be normalized before NER
            result = extractor.extract(
                "GOKULAKRISHNAN SWAMINATHAN\ngswaminathanpurdue@gmail.com\n"
            )

        assert result == "Gokulakrishnan Swaminathan"
        # Verify the NLP model received title-cased text
        call_args = mock_nlp.call_args[0][0]
        assert "Gokulakrishnan Swaminathan" in call_args


class TestSpacyNameExtractorEdgeCases:
    """Test spaCy name extractor error handling."""

    def test_empty_text_returns_none(self):
        """Returns None for empty input without loading model."""
        extractor = SpacyNameExtractor()
        result = extractor.extract("")
        assert result is None

    def test_no_person_entity_returns_none(self):
        """Returns None when NER finds no PERSON entities."""
        extractor = SpacyNameExtractor()

        mock_doc = MagicMock(ents=[])
        mock_nlp = MagicMock(return_value=mock_doc)

        with patch("resume_parser.extractors.name_extractor.spacy") as mock_spacy:
            mock_spacy.load.return_value = mock_nlp
            result = extractor.extract("Some text without names")

        assert result is None

    def test_model_not_installed_raises_configuration_error(self):
        """Raises ConfigurationError if the spaCy model is not found."""
        extractor = SpacyNameExtractor(model_name="nonexistent_model")

        with patch("resume_parser.extractors.name_extractor.spacy") as mock_spacy:
            mock_spacy.load.side_effect = OSError("Model not found")
            with pytest.raises(ConfigurationError, match="not installed"):
                extractor.extract("Jane Doe")

    def test_spacy_not_installed_raises_configuration_error(self):
        """Raises ConfigurationError if spaCy is not installed."""
        extractor = SpacyNameExtractor()
        extractor._nlp = None

        with patch("resume_parser.extractors.name_extractor.spacy", None):
            with pytest.raises(ConfigurationError, match="spaCy is required"):
                extractor._load_model()

    def test_lazy_loading_only_loads_once(self):
        """The spaCy model is loaded only on first extraction call."""
        extractor = SpacyNameExtractor()

        mock_doc = MagicMock(ents=[])
        mock_nlp = MagicMock(return_value=mock_doc)

        with patch("resume_parser.extractors.name_extractor.spacy") as mock_spacy:
            mock_spacy.load.return_value = mock_nlp
            extractor.extract("Text 1")
            extractor.extract("Text 2")

        # spacy.load should be called only once (lazy loading)
        mock_spacy.load.assert_called_once()


# ---------------------------------------------------------------------------
# HeuristicNameExtractor tests
# ---------------------------------------------------------------------------

class TestHeuristicNameExtractorHappyPath:
    """Test successful heuristic name extraction."""

    def test_name_on_first_line(self):
        """Extracts name from the first line of the resume."""
        extractor = HeuristicNameExtractor()
        result = extractor.extract("Jane Doe\njane@example.com\nSkills: Python")
        assert result == "Jane Doe"

    def test_name_after_blank_lines(self):
        """Handles leading blank lines before the name."""
        extractor = HeuristicNameExtractor()
        result = extractor.extract("\n\nJane Doe\njane@example.com\n")
        assert result == "Jane Doe"

    def test_three_word_name(self):
        """Handles three-word names."""
        extractor = HeuristicNameExtractor()
        result = extractor.extract("Mary Jane Watson\nemail@test.com\n")
        assert result == "Mary Jane Watson"


class TestHeuristicNameExtractorEdgeCases:
    """Test heuristic name extractor edge cases."""

    def test_empty_text_returns_none(self):
        """Returns None for empty input."""
        extractor = HeuristicNameExtractor()
        assert extractor.extract("") is None

    def test_email_first_line_skipped(self):
        """Skips lines that look like email addresses."""
        extractor = HeuristicNameExtractor()
        result = extractor.extract("jane@example.com\nJane Doe\nSkills: Python")
        assert result == "Jane Doe"

    def test_url_line_skipped(self):
        """Skips lines that contain URLs."""
        extractor = HeuristicNameExtractor()
        result = extractor.extract("https://linkedin.com/in/jane\nJane Doe\n")
        assert result == "Jane Doe"

    def test_header_keyword_skipped(self):
        """Skips common resume section headers."""
        extractor = HeuristicNameExtractor()
        result = extractor.extract("Resume\nJane Doe\njane@test.com\n")
        assert result == "Jane Doe"

    def test_single_word_name_returns_none(self):
        """Returns None for single-word lines (not a full name)."""
        extractor = HeuristicNameExtractor()
        result = extractor.extract("Madonna\njane@test.com\n")
        assert result is None

    def test_very_long_line_skipped(self):
        """Skips lines that are too long to be a name."""
        extractor = HeuristicNameExtractor()
        long_line = "A " * 40  # 80 chars
        result = extractor.extract(f"{long_line}\nJane Doe\n")
        assert result == "Jane Doe"

    def test_no_suitable_candidate_returns_none(self):
        """Returns None when no line looks like a name."""
        extractor = HeuristicNameExtractor()
        result = extractor.extract("jane@test.com\n555-1234\nhttps://github.com\n")
        assert result is None
