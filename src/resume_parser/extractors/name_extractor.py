"""Name extraction strategies: spaCy NER and heuristic-based."""

from __future__ import annotations

import re

try:
    import spacy
except ImportError:
    spacy = None  # type: ignore[assignment]

from resume_parser.exceptions import ConfigurationError, ExtractionError
from resume_parser.extractors.base import FieldExtractor


class SpacyNameExtractor(FieldExtractor):
    """Extracts candidate name using spaCy's named entity recognition.

    Uses the PERSON entity label to identify names. Processes only the
    first portion of the resume text, since names typically appear at
    the top of a resume.
    """

    # Number of characters from the start of the resume to analyze
    HEAD_CHAR_LIMIT = 500

    def __init__(self, model_name: str = "en_core_web_sm") -> None:
        super().__init__()
        self._model_name = model_name
        self._nlp = None  # Lazy-loaded to avoid startup cost

    def _load_model(self) -> None:
        """Lazy-load the spaCy model on first use.

        Raises:
            ConfigurationError: If spaCy or the model is not installed.
        """
        if spacy is None:
            raise ConfigurationError(
                "spaCy is required for NER-based name extraction. "
                "Install it with: pip install spacy"
            )

        try:
            self._nlp = spacy.load(self._model_name)
            self.logger.info("Loaded spaCy model '%s'", self._model_name)
        except OSError as exc:
            raise ConfigurationError(
                f"spaCy model '{self._model_name}' is not installed. "
                f"Download it with: python -m spacy download {self._model_name}"
            ) from exc

    def extract(self, text: str) -> str | None:
        """Extract the candidate's name using NER.

        Args:
            text: The full text content of the resume.

        Returns:
            The detected name, or None if no PERSON entity is found.

        Raises:
            ConfigurationError: If spaCy or the model is unavailable.
            ExtractionError: If NER processing fails unexpectedly.
        """
        if not text or not text.strip():
            self.logger.debug("Empty text provided; no name to extract")
            return None

        if self._nlp is None:
            self._load_model()

        try:
            # Analyze only the head of the resume for efficiency
            head_text = text[: self.HEAD_CHAR_LIMIT]

            # Normalize ALL-CAPS lines to title case — spaCy NER models
            # perform poorly on all-uppercase input (common in resume headers)
            lines = head_text.splitlines()
            normalized_lines = [
                line.title() if line.isupper() else line for line in lines
            ]
            head_text = "\n".join(normalized_lines)

            doc = self._nlp(head_text)

            # Collect PERSON entities
            person_entities = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]

            if not person_entities:
                self.logger.info("No PERSON entity found in resume head")
                return None

            # Return the first PERSON entity (most likely the candidate's name)
            name = person_entities[0]
            self.logger.info(
                "Extracted name '%s' (found %d PERSON entities)",
                name,
                len(person_entities),
            )
            return name

        except (ConfigurationError, ExtractionError):
            raise
        except Exception as exc:
            raise ExtractionError(
                f"spaCy NER processing failed: {exc}"
            ) from exc


class HeuristicNameExtractor(FieldExtractor):
    """Extracts candidate name using rule-based heuristics.

    Assumes the name is typically the first non-empty line of the resume
    that does not look like an email address, phone number, or URL.
    Useful as a lightweight fallback when spaCy is not available.
    """

    # Patterns for lines that are NOT names
    _EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@")
    _PHONE_PATTERN = re.compile(r"[\d\(\)\-\+\s]{7,}")
    _URL_PATTERN = re.compile(r"https?://|www\.|linkedin\.com|github\.com", re.IGNORECASE)
    _HEADER_KEYWORDS = re.compile(
        r"^(resume|curriculum vitae|cv|objective|summary|experience|education|skills)$",
        re.IGNORECASE,
    )

    def extract(self, text: str) -> str | None:
        """Extract the candidate's name from the first few lines.

        Args:
            text: The full text content of the resume.

        Returns:
            The detected name, or None if no suitable candidate is found.
        """
        if not text or not text.strip():
            self.logger.debug("Empty text provided; no name to extract")
            return None

        lines = text.strip().splitlines()

        for line in lines[:10]:  # Check only the first 10 lines
            candidate = line.strip()

            if not candidate:
                continue

            # Skip lines that match non-name patterns
            if self._EMAIL_PATTERN.search(candidate):
                continue
            if self._PHONE_PATTERN.fullmatch(candidate):
                continue
            if self._URL_PATTERN.search(candidate):
                continue
            if self._HEADER_KEYWORDS.fullmatch(candidate):
                continue

            # A name should be relatively short (under 60 chars)
            # and contain at least two words
            words = candidate.split()
            if len(words) < 2 or len(candidate) > 60:
                continue

            # Check that words look like name parts (mostly alphabetic)
            if all(re.match(r"^[A-Za-z\.\-\']+$", w) for w in words):
                self.logger.info("Extracted name '%s' via heuristic", candidate)
                return candidate

        self.logger.info("No suitable name candidate found via heuristic")
        return None
