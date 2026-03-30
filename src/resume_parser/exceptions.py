"""Custom exception hierarchy for the resume parser framework.

All framework-specific exceptions inherit from ResumeParserError,
allowing callers to catch errors at the desired granularity.
"""


class ResumeParserError(Exception):
    """Base exception for all resume parser errors."""


class UnsupportedFileFormatError(ResumeParserError):
    """Raised when the file extension is not supported (e.g., not .pdf or .docx)."""


class ParsingError(ResumeParserError):
    """Raised when file content cannot be read or decoded by a parser."""


class ExtractionError(ResumeParserError):
    """Raised when a field extractor encounters an unrecoverable error."""


class ConfigurationError(ResumeParserError):
    """Raised for missing API keys, unloaded models, or invalid configuration."""
