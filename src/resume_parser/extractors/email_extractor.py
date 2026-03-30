"""Email extraction using regex pattern matching."""

from __future__ import annotations

import re

from resume_parser.extractors.base import FieldExtractor


class RegexEmailExtractor(FieldExtractor):
    """Extracts email addresses using a regex pattern.

    Uses a simplified RFC 5322 pattern that covers the vast majority
    of real-world email formats found in resumes.
    """

    # Handles standard emails, plus-addressing, subdomains, and long TLDs
    EMAIL_PATTERN = re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    )

    def extract(self, text: str) -> str | None:
        """Extract the first email address from resume text.

        Args:
            text: The full text content of the resume.

        Returns:
            The first email address found, or None if no email is present.
        """
        if not text or not text.strip():
            self.logger.debug("Empty text provided; no email to extract")
            return None

        matches = self.EMAIL_PATTERN.findall(text)

        if not matches:
            self.logger.info("No email address found in resume text")
            return None

        if len(matches) > 1:
            self.logger.info(
                "Found %d email addresses; returning first: %s (all: %s)",
                len(matches),
                matches[0],
                ", ".join(matches),
            )
        else:
            self.logger.info("Extracted email: %s", matches[0])

        return matches[0]
