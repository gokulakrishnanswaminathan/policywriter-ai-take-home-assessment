"""Resume extraction coordinator that orchestrates field extractors."""

from __future__ import annotations

import logging

from resume_parser.exceptions import ExtractionError
from resume_parser.extractors.base import FieldExtractor
from resume_parser.models import ResumeData


class ResumeExtractor:
    """Coordinates field extraction across multiple extractors.

    Takes a dictionary mapping field names to FieldExtractor instances,
    runs each extractor against the provided text, and assembles a
    ResumeData instance. Individual extractor failures are logged but
    do not abort the entire extraction — partial results are returned.
    """

    VALID_FIELDS = frozenset({"name", "email", "skills"})

    def __init__(self, extractors: dict[str, FieldExtractor]) -> None:
        """Initialize the coordinator with field extractors.

        Args:
            extractors: Mapping of field names to extractor instances.
                Valid field names are: 'name', 'email', 'skills'.

        Raises:
            ValueError: If any field name is not recognized.
            TypeError: If any extractor is not a FieldExtractor instance.
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        # Validate field names
        invalid_fields = set(extractors.keys()) - self.VALID_FIELDS
        if invalid_fields:
            raise ValueError(
                f"Invalid field name(s): {invalid_fields}. "
                f"Valid fields are: {sorted(self.VALID_FIELDS)}"
            )

        # Validate extractor types
        for field_name, extractor in extractors.items():
            if not isinstance(extractor, FieldExtractor):
                raise TypeError(
                    f"Extractor for '{field_name}' must be a FieldExtractor instance, "
                    f"got {type(extractor).__name__}"
                )

        self._extractors = extractors
        self.logger.info(
            "Initialized with extractors: %s",
            {name: ext.__class__.__name__ for name, ext in extractors.items()},
        )

    def extract(self, text: str) -> ResumeData:
        """Run all registered extractors and return populated ResumeData.

        Each extractor runs independently. If one fails, the error is
        logged and the corresponding field retains its default value
        (None for name/email, empty list for skills).

        Args:
            text: The full text content of the resume.

        Returns:
            A ResumeData instance with extracted fields.
        """
        results: dict = {}

        for field_name, extractor in self._extractors.items():
            try:
                value = extractor.extract(text)
                results[field_name] = value
                self.logger.info(
                    "Extracted '%s' using %s: %s",
                    field_name,
                    extractor.__class__.__name__,
                    repr(value)[:100],
                )
            except ExtractionError as exc:
                self.logger.error(
                    "Failed to extract '%s' using %s: %s",
                    field_name,
                    extractor.__class__.__name__,
                    exc,
                )
            except Exception as exc:
                self.logger.error(
                    "Unexpected error extracting '%s' using %s: %s",
                    field_name,
                    extractor.__class__.__name__,
                    exc,
                )

        resume_data = ResumeData(**results)
        self.logger.info("Extraction complete: %s", resume_data.to_dict())
        return resume_data
