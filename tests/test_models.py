"""Tests for the ResumeData data model."""

import json

from resume_parser.models import ResumeData


class TestResumeDataConstruction:
    """Test ResumeData initialization."""

    def test_default_values(self):
        """Fields default to None/empty list when not provided."""
        data = ResumeData()
        assert data.name is None
        assert data.email is None
        assert data.skills == []

    def test_all_fields_provided(self):
        """All fields are correctly stored when provided."""
        data = ResumeData(
            name="Jane Doe",
            email="jane@example.com",
            skills=["Python", "ML"],
        )
        assert data.name == "Jane Doe"
        assert data.email == "jane@example.com"
        assert data.skills == ["Python", "ML"]

    def test_partial_fields(self):
        """Some fields can be provided while others use defaults."""
        data = ResumeData(name="Jane Doe")
        assert data.name == "Jane Doe"
        assert data.email is None
        assert data.skills == []

    def test_skills_default_is_independent(self):
        """Each instance gets its own skills list (no shared mutable default)."""
        data1 = ResumeData()
        data2 = ResumeData()
        data1.skills.append("Python")
        assert data2.skills == []


class TestResumeDataSerialization:
    """Test ResumeData serialization methods."""

    def test_to_dict(self):
        """to_dict returns a plain dictionary with all fields."""
        data = ResumeData(name="Jane", email="jane@test.com", skills=["Python"])
        result = data.to_dict()
        assert result == {
            "name": "Jane",
            "email": "jane@test.com",
            "skills": ["Python"],
        }

    def test_to_dict_with_defaults(self):
        """to_dict works with default values."""
        data = ResumeData()
        result = data.to_dict()
        assert result == {"name": None, "email": None, "skills": []}

    def test_to_json(self):
        """to_json returns valid JSON matching the expected structure."""
        data = ResumeData(
            name="Jane Doe",
            email="jane@example.com",
            skills=["Python", "ML"],
        )
        json_str = data.to_json()
        parsed = json.loads(json_str)
        assert parsed["name"] == "Jane Doe"
        assert parsed["email"] == "jane@example.com"
        assert parsed["skills"] == ["Python", "ML"]

    def test_to_json_with_none_values(self):
        """to_json correctly serializes None values."""
        data = ResumeData()
        json_str = data.to_json()
        parsed = json.loads(json_str)
        assert parsed["name"] is None
        assert parsed["email"] is None
        assert parsed["skills"] == []

    def test_to_json_unicode(self):
        """to_json handles unicode characters correctly."""
        data = ResumeData(name="José García", skills=["Análisis"])
        json_str = data.to_json()
        parsed = json.loads(json_str)
        assert parsed["name"] == "José García"
        assert parsed["skills"] == ["Análisis"]
