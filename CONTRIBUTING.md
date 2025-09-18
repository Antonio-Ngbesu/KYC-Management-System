# Contributing to KYC System

Thank you for your interest in contributing to the KYC System! We welcome contributions from the community.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Git
- Basic understanding of FastAPI and Streamlit

### Development Setup

1. Fork the repository
2. Clone your fork locally
3. Create a virtual environment
4. Install dependencies: `pip install -r requirements.txt`
5. Run tests to ensure everything works: `python -m pytest`

## 🤝 How to Contribute

### Reporting Bugs

- Use GitHub Issues to report bugs
- Include detailed reproduction steps
- Provide system information (OS, Python version, etc.)

### Suggesting Features

- Open a GitHub Issue with the "enhancement" label
- Describe the feature and its benefits
- Discuss implementation approaches

### Code Contributions

#### Pull Request Process

1. **Create a branch**: `git checkout -b feature/your-feature-name`
2. **Write code**: Follow our coding standards
3. **Add tests**: Ensure your code is tested
4. **Update docs**: Update README.md if needed
5. **Commit**: Use clear, descriptive commit messages
6. **Push**: Push your branch to your fork
7. **Pull Request**: Open a PR with a clear description

#### Coding Standards

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions small and focused
- Use meaningful variable names

#### Testing

- Write unit tests for new functionality
- Ensure all tests pass before submitting
- Aim for good test coverage
- Include integration tests where appropriate

## 📋 Development Guidelines

### Code Style

```python
# Good
def process_document(document_id: str) -> DocumentResult:
    """Process a KYC document and return results."""
    # Implementation here
    pass

# Avoid
def proc_doc(doc_id):
    # No docstring, unclear naming
    pass
```

### Commit Messages

```bash
# Good
feat: add document risk assessment algorithm
fix: resolve authentication token expiration issue
docs: update API documentation for upload endpoint

# Avoid
fix stuff
update code
changes
```

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

## 🔍 Code Review Process

1. **Automated Checks**: GitHub Actions will run tests and linting
2. **Manual Review**: Maintainers will review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, your PR will be merged

## 📚 Documentation

### README Updates

- Keep the README.md current with new features
- Update installation instructions if needed
- Add examples for new functionality

### Code Documentation

- Use clear docstrings
- Include parameter and return type information
- Provide usage examples where helpful

## 🏆 Recognition

Contributors will be:

- Listed in the README.md contributors section
- Mentioned in release notes for significant contributions
- Invited to join the maintainers team for substantial contributions

## ❓ Questions?

- Open a GitHub Discussion for questions
- Check existing issues and PRs for similar topics
- Contact maintainers directly for sensitive matters

## 📋 Issue Labels

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements to documentation
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention is needed
- `priority: high` - High priority issues
- `priority: low` - Low priority issues

Thank you for contributing to the KYC System! 🎉
