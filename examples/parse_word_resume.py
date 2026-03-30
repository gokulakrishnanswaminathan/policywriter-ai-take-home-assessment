"""Example: Parse a Word (.docx) resume using field-specific extractors.

This script demonstrates how to use the Resume Parser Framework
to extract structured data from a Word document resume, and how
to swap extraction strategies (e.g., HeuristicNameExtractor vs
SpacyNameExtractor).

Usage:
    python examples/parse_word_resume.py path/to/resume.docx

Requirements:
    - GEMINI_API_KEY environment variable set (or .env file)
"""

from __future__ import annotations

import logging
import sys

from dotenv import load_dotenv

from resume_parser import (
    GeminiSkillsExtractor,
    HeuristicNameExtractor,
    RegexEmailExtractor,
    ResumeExtractor,
    ResumeParserFramework,
)
from resume_parser.logging_config import configure_logging

# Load environment variables from .env file
load_dotenv()


def main() -> None:
    """Parse a Word resume and print the extracted data as JSON."""
    configure_logging(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python examples/parse_word_resume.py <path_to_resume.docx>")
        sys.exit(1)

    file_path = sys.argv[1]

    # Configure field-specific extraction strategies
    # Here we use HeuristicNameExtractor instead of SpacyNameExtractor
    # to demonstrate the Strategy pattern — extractors are swappable
    extractors = {
        "name": HeuristicNameExtractor(),        # Rule-based (no ML dependency)
        "email": RegexEmailExtractor(),           # Regex-based
        "skills": GeminiSkillsExtractor(),        # LLM-based (Google Gemini)
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
