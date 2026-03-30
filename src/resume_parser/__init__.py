"""Resume Parser Framework.

A pluggable framework for extracting structured data from resumes
in PDF and Word formats, with configurable field extraction strategies.

Example usage::

    from resume_parser import (
        ResumeParserFramework,
        ResumeExtractor,
        RegexEmailExtractor,
        SpacyNameExtractor,
        GeminiSkillsExtractor,
    )

    extractors = {
        "name": SpacyNameExtractor(),
        "email": RegexEmailExtractor(),
        "skills": GeminiSkillsExtractor(),
    }
    coordinator = ResumeExtractor(extractors)
    framework = ResumeParserFramework(coordinator)
    result = framework.parse_resume("resume.pdf")
    print(result.to_json())
"""

from resume_parser.coordinator import ResumeExtractor
from resume_parser.extractors.base import FieldExtractor
from resume_parser.extractors.email_extractor import RegexEmailExtractor
from resume_parser.extractors.name_extractor import (
    HeuristicNameExtractor,
    SpacyNameExtractor,
)
from resume_parser.extractors.skills_extractor import GeminiSkillsExtractor
from resume_parser.framework import ResumeParserFramework
from resume_parser.models import ResumeData
from resume_parser.parsers.base import FileParser
from resume_parser.parsers.pdf_parser import PDFParser
from resume_parser.parsers.word_parser import WordParser

__all__ = [
    "ResumeData",
    "FileParser",
    "PDFParser",
    "WordParser",
    "FieldExtractor",
    "RegexEmailExtractor",
    "SpacyNameExtractor",
    "HeuristicNameExtractor",
    "GeminiSkillsExtractor",
    "ResumeExtractor",
    "ResumeParserFramework",
]
