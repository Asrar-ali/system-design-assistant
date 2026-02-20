# Contributing to System Design Interview Assistant

Thank you for your interest in contributing! This is primarily a portfolio/learning project, but contributions are welcome.

## How to Contribute

### Reporting Bugs

1. Check if the issue already exists in [Issues](https://github.com/md-asrar/system-design-assistant/issues)
2. Create a new issue with:
   - Clear title
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (Python version, OS)

### Suggesting Features

1. Open an issue with the `enhancement` label
2. Describe the feature and its use case
3. Explain how it improves the project

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Run tests: `pytest`
5. Format code: `black src/ tests/`
6. Commit with clear messages
7. Push and create a PR

## Development Setup

```bash
# Clone your fork
git clone https://github.com/md-asrar/system-design-assistant.git
cd system-design-assistant

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Run app
streamlit run app.py
```

## Code Standards

- Follow PEP 8 style guide
- Use type hints where appropriate
- Add docstrings to functions/classes
- Write tests for new features
- Keep commits atomic and well-described

## Questions?

Open an issue or reach out via GitHub Discussions.

Thank you for contributing! 🎉
