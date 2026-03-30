"""Skills extraction using Google Gemini LLM."""

from __future__ import annotations

import json
import os
import re

try:
    from google import genai
except ImportError:
    genai = None  # type: ignore[assignment]

from resume_parser.exceptions import ConfigurationError, ExtractionError
from resume_parser.extractors.base import FieldExtractor


class GeminiSkillsExtractor(FieldExtractor):
    """Extracts skills from resume text using Google Gemini LLM.

    Sends the resume text to Gemini with a structured prompt requesting
    a JSON array of skill strings. Includes defensive parsing to handle
    common LLM response quirks (e.g., markdown-wrapped JSON).
    """

    DEFAULT_MODEL = "gemini-2.5-flash-lite"

    PROMPT_TEMPLATE = (
        "You are a resume skills extractor. Given the following resume text, "
        "extract all technical and professional skills mentioned.\n\n"
        "Rules:\n"
        "- Return ONLY a JSON array of skill strings, nothing else.\n"
        "- Each skill should be a concise phrase (e.g., 'Machine Learning', 'Python', 'Project Management').\n"
        "- Deduplicate skills.\n"
        "- If no skills are found, return an empty array: []\n\n"
        "Resume text:\n"
        "---\n"
        "{resume_text}\n"
        "---\n"
    )

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = DEFAULT_MODEL,
    ) -> None:
        """Initialize the Gemini skills extractor.

        Args:
            api_key: Google Gemini API key. Falls back to the
                GEMINI_API_KEY environment variable if not provided.
            model_name: Gemini model identifier to use.

        Raises:
            ConfigurationError: If no API key is available.
        """
        super().__init__()
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self._api_key:
            raise ConfigurationError(
                "GEMINI_API_KEY must be set as an environment variable "
                "or passed directly to GeminiSkillsExtractor."
            )
        self._model_name = model_name
        self._client = None  # Lazy-loaded

    def _initialize_client(self) -> None:
        """Configure and create the Gemini client."""
        if genai is None:
            raise ConfigurationError(
                "google-genai is required for LLM-based skills extraction. "
                "Install it with: pip install google-genai"
            )
        try:
            self._client = genai.Client(api_key=self._api_key)
            self.logger.info("Initialized Gemini client for model '%s'", self._model_name)
        except Exception as exc:
            raise ConfigurationError(
                f"Failed to initialize Gemini client: {exc}"
            ) from exc

    @staticmethod
    def _parse_skills_response(response_text: str) -> list[str]:
        """Parse the LLM response into a list of skill strings.

        Handles common response quirks like markdown code fences
        wrapping the JSON array.

        Args:
            response_text: Raw text from the Gemini response.

        Returns:
            A list of skill strings.

        Raises:
            ExtractionError: If the response cannot be parsed as JSON.
        """
        cleaned = response_text.strip()

        # Strip markdown code fences (```json ... ``` or ``` ... ```)
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ExtractionError(
                f"Failed to parse Gemini response as JSON: {exc}. "
                f"Raw response: {response_text[:200]}"
            ) from exc

        if not isinstance(parsed, list):
            raise ExtractionError(
                f"Expected a JSON array from Gemini, got {type(parsed).__name__}: "
                f"{response_text[:200]}"
            )

        # Ensure all elements are strings and deduplicate
        skills = list(dict.fromkeys(str(s) for s in parsed))
        return skills

    def extract(self, text: str) -> list[str]:
        """Extract skills from resume text using Gemini LLM.

        Args:
            text: The full text content of the resume.

        Returns:
            A deduplicated list of skill strings.

        Raises:
            ConfigurationError: If the Gemini client cannot be initialized.
            ExtractionError: If the API call or response parsing fails.
        """
        if not text or not text.strip():
            self.logger.debug("Empty text provided; returning empty skills list")
            return []

        if self._client is None:
            self._initialize_client()

        prompt = self.PROMPT_TEMPLATE.format(resume_text=text)

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
                config={"temperature": 0.0},
            )
            response_text = response.text
            self.logger.debug("Gemini raw response: %s", response_text[:300])

        except Exception as exc:
            raise ExtractionError(
                f"Gemini API call failed: {exc}"
            ) from exc

        skills = self._parse_skills_response(response_text)
        self.logger.info("Extracted %d skill(s) via Gemini", len(skills))
        return skills
