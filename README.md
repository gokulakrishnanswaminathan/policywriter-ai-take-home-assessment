# Resume Parser Framework

A pluggable Python framework for extracting structured data from resumes in **PDF** and **Word (.docx)** formats. Built with Object-Oriented Design principles, it uses the **Strategy pattern** to support configurable, field-specific extraction strategies — including regex, NER (spaCy), and LLM-based (Google Gemini) approaches.

## Output Format

Each resume is parsed into a structured JSON object:

```json
{
  "name": "Jane Doe",
  "email": "jane.doe@gmail.com",
  "skills": ["Machine Learning", "Python", "Docker"]
}
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 ResumeParserFramework                   │
│              parse_resume(file_path) -> ResumeData      │
│                                                         │
│  ┌──────────────────┐    ┌───────────────────────────┐  │
│  │   FileParser      │    │    ResumeExtractor        │  │
│  │   (ABC)           │    │    (Coordinator)          │  │
│  │                   │    │                           │  │
│  │  ┌─ PDFParser     │    │  extractors = {           │  │
│  │  └─ WordParser    │    │    "name":  NameExtractor  │  │
│  │                   │    │    "email": EmailExtractor │  │
│  └──────────────────┘    │    "skills": SkillsExtr.  │  │
│                           │  }                        │  │
│                           └───────────────────────────┘  │
└─────────────────────────────────────────────────────────┘

                    FieldExtractor (ABC)
                   ┌────────┼────────────┐
                   │        │            │
          RegexEmail   SpacyName    GeminiSkills
          Extractor    Extractor    Extractor
                   HeuristicName
                    Extractor
```

**Strategy Pattern**: Each `FieldExtractor` subclass encapsulates one extraction algorithm. Extractors are interchangeable — swap them by passing a different instance to the `ResumeExtractor` coordinator. No existing code changes required.

**Partial Failure Resilience**: If one extractor fails (e.g., Gemini API timeout), the coordinator logs the error and continues. Other fields are still extracted and returned.

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/resume-parser.git
cd resume-parser

# Install with uv
uv sync

# Or with pip
pip install -e ".[dev]"
```

### Download spaCy Model

Required for `SpacyNameExtractor` (NER-based name extraction):

```bash
python -m spacy download en_core_web_sm
```

### Configure API Key

The `GeminiSkillsExtractor` requires a Google Gemini API key. Get one at [Google AI Studio](https://aistudio.google.com/apikey).

```bash
# Copy the example and add your key
cp .env.example .env
# Edit .env and set: GEMINI_API_KEY=your_actual_key
```

> **Note**: Never commit your `.env` file. It is listed in `.gitignore`.

## Usage

### Quick Start

```python
from resume_parser import (
    ResumeParserFramework,
    ResumeExtractor,
    RegexEmailExtractor,
    SpacyNameExtractor,
    GeminiSkillsExtractor,
)

# Configure extraction strategies
extractors = {
    "name": SpacyNameExtractor(),           # ML-based (spaCy NER)
    "email": RegexEmailExtractor(),          # Regex-based
    "skills": GeminiSkillsExtractor(),       # LLM-based (Google Gemini)
}

# Build and run
coordinator = ResumeExtractor(extractors)
framework = ResumeParserFramework(coordinator)
result = framework.parse_resume("path/to/resume.pdf")

print(result.to_json())
```

### Parsing a PDF Resume

```bash
python examples/parse_pdf_resume.py path/to/resume.pdf
```

See [`examples/parse_pdf_resume.py`](examples/parse_pdf_resume.py) for the full source.

### Parsing a Word Resume

```bash
python examples/parse_word_resume.py path/to/resume.docx
```

See [`examples/parse_word_resume.py`](examples/parse_word_resume.py) for the full source.

### Swapping Extraction Strategies

The Strategy pattern makes it trivial to swap extractors:

```python
from resume_parser import HeuristicNameExtractor, SpacyNameExtractor

# Use spaCy NER (requires model download)
extractors = {"name": SpacyNameExtractor(), ...}

# Or use rule-based heuristic (no ML dependency)
extractors = {"name": HeuristicNameExtractor(), ...}
```

### Creating a Custom Extractor

Implement the `FieldExtractor` interface:

```python
from resume_parser import FieldExtractor

class MyCustomEmailExtractor(FieldExtractor):
    """Custom email extractor using a different strategy."""

    def extract(self, text: str) -> str | None:
        # Your extraction logic here
        ...

# Use it like any built-in extractor
extractors = {"email": MyCustomEmailExtractor(), ...}
```

## Extraction Strategies

| Field  | Extractor                 | Strategy     | Description                                      |
|--------|---------------------------|--------------|--------------------------------------------------|
| Name   | `SpacyNameExtractor`      | ML (NER)     | Uses spaCy PERSON entities from the resume head  |
| Name   | `HeuristicNameExtractor`  | Rule-based   | First line that looks like a name (no ML needed)  |
| Email  | `RegexEmailExtractor`     | Regex        | RFC 5322 simplified pattern                       |
| Skills | `GeminiSkillsExtractor`   | LLM          | Google Gemini with structured JSON prompting      |

## Configuration

| Variable        | Description                          | Required For             |
|-----------------|--------------------------------------|--------------------------|
| `GEMINI_API_KEY`| Google Gemini API key                | `GeminiSkillsExtractor`  |

`SpacyNameExtractor` accepts an optional `model_name` parameter (default: `en_core_web_sm`). `GeminiSkillsExtractor` accepts optional `api_key` and `model_name` parameters.

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage report
uv run pytest tests/ -v --cov=resume_parser --cov-report=term-missing

# Run a specific test file
uv run pytest tests/test_extractors/test_email_extractor.py -v
```

All external dependencies (spaCy models, Gemini API) are mocked in tests — no API keys or model downloads needed to run the test suite.

## Project Structure

```
├── pyproject.toml                          # Package config, dependencies, pytest settings
├── README.md
├── .env.example                            # API key template
├── .gitignore
├── examples/
│   ├── parse_pdf_resume.py                 # PDF parsing example
│   └── parse_word_resume.py                # Word parsing example (with strategy swap)
├── src/
│   └── resume_parser/
│       ├── __init__.py                     # Public API exports
│       ├── models.py                       # ResumeData dataclass
│       ├── exceptions.py                   # Custom exception hierarchy
│       ├── logging_config.py               # Structured logging setup
│       ├── parsers/
│       │   ├── base.py                     # FileParser ABC
│       │   ├── pdf_parser.py               # PDFParser (pdfplumber)
│       │   └── word_parser.py              # WordParser (python-docx)
│       ├── extractors/
│       │   ├── base.py                     # FieldExtractor ABC (Strategy interface)
│       │   ├── email_extractor.py          # RegexEmailExtractor
│       │   ├── name_extractor.py           # SpacyNameExtractor + HeuristicNameExtractor
│       │   └── skills_extractor.py         # GeminiSkillsExtractor
│       ├── coordinator.py                  # ResumeExtractor (orchestration)
│       └── framework.py                    # ResumeParserFramework (facade)
└── tests/
    ├── conftest.py                         # Shared fixtures and mocks
    ├── test_models.py                      # ResumeData tests
    ├── test_parsers/
    │   ├── test_pdf_parser.py              # PDFParser tests
    │   └── test_word_parser.py             # WordParser tests
    ├── test_extractors/
    │   ├── test_email_extractor.py         # Email extraction tests
    │   ├── test_name_extractor.py          # Name extraction tests (both strategies)
    │   └── test_skills_extractor.py        # Skills extraction tests (mocked LLM)
    ├── test_coordinator.py                 # Coordinator tests
    ├── test_framework.py                   # Framework facade tests
    └── test_integration.py                 # End-to-end pipeline tests
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Strategy pattern** via `FieldExtractor` ABC | Extractors are interchangeable without modifying the coordinator or framework |
| **Two name extractors** (SpaCy + Heuristic) | Concretely demonstrates strategy swapping; provides a fallback without ML dependencies |
| **Partial failure** in coordinator | One failing extractor doesn't abort the entire extraction — returns partial results |
| **Lazy loading** for spaCy/Gemini | Avoids startup cost; fails only when actually needed |
| **`src/` layout** | Python packaging best practice; prevents accidental imports from the working directory |
| **Custom exception hierarchy** | Enables callers to catch errors at exactly the granularity they need |
| **`pyproject.toml` only** | Modern Python standard (PEP 621); no `requirements.txt` or `setup.py` needed |

## License

MIT
