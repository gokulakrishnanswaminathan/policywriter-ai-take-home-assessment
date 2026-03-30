"""Data model for structured resume information."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass
class ResumeData:
    """Encapsulates the three extracted resume fields.

    Attributes:
        name: The candidate's full name, or None if not extracted.
        email: The candidate's email address, or None if not extracted.
        skills: A list of extracted skill strings (empty if none found).
    """

    name: str | None = None
    email: str | None = None
    skills: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a plain dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serialize to a formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
