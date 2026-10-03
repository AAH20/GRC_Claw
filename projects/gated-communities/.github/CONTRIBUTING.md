# Contributing to Gated Communities

Thank you for your interest in contributing to Gated Communities! We welcome contributions from everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/gated-communities.git
   cd gated-communities
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/original-org/gated-communities.git
   ```

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker 24+
- Docker Compose

### Environment Setup

1. **Copy the environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Install frontend dependencies**:
   ```bash
   cd frontend && npm install
   ```

4. **Start the development environment**:
   ```bash
   docker-compose up -d
   ```

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start the development server**:
   ```bash
   # Backend
   uvicorn src.main:app --reload

   # Frontend (in a separate terminal)
   cd frontend && npm run dev
   ```

## Project Structure

```
gated-communities/
├── src/                    # Python backend source
│   ├── api/               # API routes and endpoints
│   ├── core/              # Core business logic
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   └── services/          # Business services
├── frontend/              # React/TypeScript frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom hooks
│   │   ├── services/      # API services
│   │   └── utils/         # Utility functions
├── database/              # Database migrations
├── docker/                # Docker configurations
├── k8s/                   # Kubernetes manifests
├── monitoring/            # Monitoring and alerting
├── e2e/                   # End-to-end tests
├── docs/                  # Documentation
└── tests/                 # Test files
```

## How to Contribute

### Reporting Bugs

- Use the [Bug Report template](https://github.com/your-org/gated-communities/issues/new?template=bug_report.yml)
- Check existing issues first to avoid duplicates
- Provide as much detail as possible

### Suggesting Features

- Use the [Feature Request template](https://github.com/your-org/gated-communities/issues/new?template=feature_request.yml)
- Clearly describe the problem and proposed solution
- Consider alternatives and trade-offs

### Contributing Code

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes** following our coding standards

3. **Write tests** for your changes

4. **Run the test suite** to ensure everything passes

5. **Commit your changes** with a descriptive message:
   ```bash
   git commit -m "feat: add new feature description"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request** using our PR template

## Pull Request Process

1. **Update documentation** if your changes affect the API or user-facing features
2. **Ensure CI passes** - all tests, linting, and type checks must pass
3. **Request review** from at least one maintainer
4. **Address feedback** promptly and professionally
5. **Squash commits** if requested by reviewers
6. **Wait for approval** - PRs require at least one approval before merging

### PR Title Format

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `test:` - Test additions or updates
- `chore:` - Build process or auxiliary tool changes
- `ci:` - CI/CD changes

Examples:
- `feat: add user authentication endpoint`
- `fix: resolve race condition in community creation`
- `docs: update API documentation for v2`

## Coding Standards

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use `ruff` for linting and formatting
- Use `mypy` for type checking

### TypeScript/React

- Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Use functional components with hooks
- Prefer TypeScript over JavaScript
- Use `eslint` and `prettier` for linting and formatting

### General

- Write clear, self-documenting code
- Add comments for complex logic
- Keep functions small and focused
- Follow the Single Responsibility Principle

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_specific.py

# Run specific test
pytest tests/test_specific.py::test_function_name

# Run e2e tests
pytest e2e/

# Run frontend tests
cd frontend && npm test
```

### Writing Tests

- Write tests for all new features
- Aim for >80% code coverage
- Use descriptive test names
- Follow the Arrange-Act-Assert pattern
- Mock external dependencies

## Documentation

- Update README.md if you change setup instructions
- Update API documentation (openapi.yaml) for endpoint changes
- Add docstrings to all public functions and classes
- Update architecture.md for significant architectural changes

## Community

- Join our [GitHub Discussions](https://github.com/your-org/gated-communities/discussions)
- Follow our [Security Policy](SECURITY.md) for reporting vulnerabilities
- Be respectful and inclusive in all interactions

## Questions?

If you have questions about contributing, please:
1. Check our [documentation](docs/)
2. Search [existing issues](https://github.com/your-org/gated-communities/issues)
3. Start a [discussion](https://github.com/your-org/gated-communities/discussions)

Thank you for contributing to Gated Communities!
