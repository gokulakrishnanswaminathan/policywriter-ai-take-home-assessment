"""Tests for the RegexEmailExtractor."""

import pytest

from resume_parser.extractors.email_extractor import RegexEmailExtractor


class TestRegexEmailExtractorHappyPath:
    """Test successful email extraction scenarios."""

    def test_single_email(self):
        """Extracts a single email from text."""
        extractor = RegexEmailExtractor()
        result = extractor.extract("Contact: jane.doe@gmail.com")
        assert result == "jane.doe@gmail.com"

    def test_multiple_emails_returns_first(self):
        """Returns the first email when multiple are present."""
        extractor = RegexEmailExtractor()
        text = "jane@gmail.com\nwork: jane@company.com"
        result = extractor.extract(text)
        assert result == "jane@gmail.com"

    def test_email_in_resume_context(self, sample_resume_text: str):
        """Extracts email from a full resume text."""
        extractor = RegexEmailExtractor()
        result = extractor.extract(sample_resume_text)
        assert result == "jane.doe@gmail.com"


class TestRegexEmailExtractorEdgeCases:
    """Test email extraction edge cases."""

    def test_no_email_returns_none(self):
        """Returns None when no email is found."""
        extractor = RegexEmailExtractor()
        result = extractor.extract("No email here, just a phone: 555-1234")
        assert result is None

    def test_empty_text_returns_none(self, empty_text: str):
        """Returns None for empty input."""
        extractor = RegexEmailExtractor()
        result = extractor.extract(empty_text)
        assert result is None

    def test_whitespace_only_returns_none(self):
        """Returns None for whitespace-only input."""
        extractor = RegexEmailExtractor()
        result = extractor.extract("   \n\t  ")
        assert result is None

    def test_plus_addressing(self):
        """Handles plus-addressed emails (user+tag@domain.com)."""
        extractor = RegexEmailExtractor()
        result = extractor.extract("Email: user+tag@gmail.com")
        assert result == "user+tag@gmail.com"

    def test_subdomain_email(self):
        """Handles emails with subdomains."""
        extractor = RegexEmailExtractor()
        result = extractor.extract("Email: user@mail.company.co.uk")
        assert result == "user@mail.company.co.uk"

    def test_missing_tld_not_matched(self):
        """Does not match strings without a valid TLD."""
        extractor = RegexEmailExtractor()
        result = extractor.extract("Not an email: user@localhost")
        assert result is None

    def test_missing_at_sign_not_matched(self):
        """Does not match strings without @ sign."""
        extractor = RegexEmailExtractor()
        result = extractor.extract("Not an email: user.at.domain.com")
        assert result is None

    def test_email_with_dots_in_local(self):
        """Handles dots in the local part of the email."""
        extractor = RegexEmailExtractor()
        result = extractor.extract("first.last@example.com")
        assert result == "first.last@example.com"

    def test_email_with_hyphens_in_domain(self):
        """Handles hyphens in the domain part."""
        extractor = RegexEmailExtractor()
        result = extractor.extract("user@my-company.org")
        assert result == "user@my-company.org"
