"""Example: Parse a PDF resume using field-specific extractors.

This script demonstrates how to use the Resume Parser Framework
to extract structured data from a PDF resume file.

Usage:
    python examples/parse_pdf_resume.py path/to/resume.pdf

Requirements:
    - GEMINI_API_KEY environment variable set (or .env file)
    - spaCy English model: python -m spacy download en_core_web_sm
"""

from __future__ import annotations

import logging
import sys

from dotenv import load_dotenv

from resume_parser import (
    GeminiSkillsExtractor,
    RegexEmailExtractor,
    ResumeExtractor,
    ResumeParserFramework,
    SpacyNameExtractor,
)
from resume_parser.logging_config import configure_logging

# Load environment variables from .env file
load_dotenv()


def main() -> None:
    """Parse a PDF resume and print the extracted data as JSON."""
    configure_logging(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python examples/parse_pdf_resume.py <path_to_resume.pdf>")
        sys.exit(1)

    file_path = sys.argv[1]

    # Configure field-specific extraction strategies
    extractors = {
        "name": SpacyNameExtractor(),           # ML-based (spaCy NER)
        "email": RegexEmailExtractor(),          # Regex-based
        "skills": GeminiSkillsExtractor(),       # LLM-based (Google Gemini)
    }

    # Build the extraction coordinator and framework
    coordinator = ResumeExtractor(extractors)
    framework = ResumeParserFramework(coordinator)

    # Parse the resume
    result = framework.parse_resume(file_path)

    # Output the structured result
    print("\n--- Extracted Resume Data ---")
    print(result.to_json())


if __name__ == "__main__":
    main()
