# VERITAS Courtroom Experience

An interactive 15-minute British Crown Court trial experience with AI-driven courtroom simulation.

## Project Structure

```
.
├── src/                    # Source code
│   ├── models.py          # Core Pydantic data models
│   └── __init__.py
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── property/          # Property-based tests
│   └── __init__.py
├── fixtures/              # Sample case content
│   └── sample_case.json   # Example case structure
├── pyproject.toml         # Project configuration
└── README.md
```

## Setup

Install dependencies:

```bash
pip install -e .
```

## Running Tests

```bash
pytest tests/
```

## Core Data Models

- **CaseContent**: Complete case structure with narrative, evidence, and ground truth
- **EvidenceItem**: Individual pieces of evidence (physical, testimonial, documentary)
- **CharacterProfile**: Profiles for victim, defendant, and witnesses
- **TimelineEvent**: Events on the case timeline
- **ReasoningCriteria**: Criteria for evaluating user reasoning quality

## Requirements Implemented

- **Requirement 1.1**: Case content stored in JSON format
- **Requirement 1.2**: Case content validation for required fields
- **Requirement 1.3**: Evidence items constrained to 5-7 items
- **Requirement 1.4**: Character profiles for defendant, victim, and witnesses
- **Requirement 1.5**: Ground truth outcome specified
- **Requirement 1.6**: Serialization/deserialization round-trip support
