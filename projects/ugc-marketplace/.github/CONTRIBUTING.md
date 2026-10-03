# Contributing to ugc-marketplace

Thank you for your interest in contributing to ugc-marketplace! We welcome contributions from the community and are grateful for your help in making this project better.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ugc-marketplace.git
   cd ugc-marketplace
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/ugc-marketplace/ugc-marketplace.git
   ```
4. **Create a new branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Node.js >= 20.x
- pnpm >= 8.x (recommended) or npm >= 10.x
- Docker (optional, for containerized development)

### Installation

```bash
# Install dependencies
pnpm install

# Copy environment variables
cp .env.example .env

# Start development server
pnpm dev
```

### Docker Setup

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## Project Structure

```
ugc-marketplace/
├── src/                # Main application source code
├── frontend/           # Frontend application
├── sdk/                # SDK for external integrations
├── database/           # Database migrations and schemas
├── docs/               # Documentation
├── docker/             # Docker configuration files
├── k8s/                # Kubernetes manifests
├── monitoring/         # Monitoring and observability configs
├── terraform/          # Infrastructure as Code
├── openapi.json        # OpenAPI specification
├── pyproject.toml      # Python project configuration
├── docker-compose.yml  # Docker Compose configuration
└── Dockerfile          # Main Dockerfile
```

## How to Contribute

### Reporting Bugs

- Check if the bug has already been reported in [existing issues](https://github.com/ugc-marketplace/ugc-marketplace/issues)
- If not, [open a new issue](https://github.com/ugc-marketplace/ugc-marketplace/issues/new?template=bug_report.yml) using the bug report template
- Provide as much detail as possible, including steps to reproduce, expected vs actual behavior, and your environment

### Suggesting Features

- Check if the feature has already been suggested in [existing issues](https://github.com/ugc-marketplace/ugc-marketplace/issues)
- If not, [open a new issue](https://github.com/ugc-marketplace/ugc-marketplace/issues/new?template=feature_request.yml) using the feature request template
- Clearly describe the problem your feature would solve and the proposed solution

### Contributing Code

1. Ensure you have a clear understanding of the issue or feature you're working on
2. Create a new branch from `main`
3. Make your changes following our coding standards
4. Write or update tests as needed
5. Ensure all tests pass
6. Submit a pull request

## Pull Request Process

1. **Update your branch** with the latest changes from upstream:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests** to ensure everything passes:
   ```bash
   pnpm test
   pnpm lint
   pnpm type-check
   ```

3. **Commit your changes** following our commit message guidelines

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request** on GitHub with:
   - A clear title describing the change
   - A detailed description of what was changed and why
   - Reference to any related issues (e.g., "Fixes #123")
   - Screenshots or recordings if applicable

6. **Address review feedback** promptly and professionally

7. **Wait for approval** - a maintainer will review your PR and may request changes

## Coding Standards

### General Guidelines

- Follow the existing code style and conventions
- Write clear, self-documenting code with meaningful variable and function names
- Keep functions small and focused on a single responsibility
- Add comments for complex logic, but avoid obvious comments
- Handle errors gracefully and provide meaningful error messages

### TypeScript/JavaScript

- Use TypeScript for all new code
- Follow the ESLint and Prettier configurations
- Use proper typing - avoid `any` unless absolutely necessary
- Prefer `const` over `let`, and never use `var`

### Python

- Follow PEP 8 style guide
- Use type hints for function signatures
- Write docstrings for public functions and classes

### CSS/Styling

- Use CSS Modules or styled-components
- Follow the BEM naming convention for class names
- Ensure responsive design and accessibility

## Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc.)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools and libraries
- `ci`: Changes to CI configuration files and scripts
- `build`: Changes that affect the build system or external dependencies
- `revert`: Reverts a previous commit

### Examples

```
feat(auth): add OAuth2 login support

fix(api): resolve race condition in user creation

docs(readme): update installation instructions

test(utils): add tests for date formatting functions
```

## Testing

### Running Tests

```bash
# Run all tests
pnpm test

# Run tests in watch mode
pnpm test:watch

# Run tests with coverage
pnpm test:coverage

# Run specific test file
pnpm test path/to/test.spec.ts
```

### Writing Tests

- Write unit tests for all new functions and components
- Follow the Arrange-Act-Assert pattern
- Mock external dependencies
- Aim for high test coverage on critical paths
- Test edge cases and error conditions

## Documentation

- Update documentation for any changes to the API or user-facing features
- Keep the README.md up to date with any new setup instructions
- Document any new environment variables in `.env.example`
- Update the OpenAPI specification for API changes

## Community

- Join our [GitHub Discussions](https://github.com/ugc-marketplace/ugc-marketplace/discussions) for questions and ideas
- Follow our [Security Policy](SECURITY.md) for reporting vulnerabilities
- Be respectful and inclusive in all interactions

## Questions?

If you have any questions about contributing, feel free to:

- Open a [GitHub Discussion](https://github.com/ugc-marketplace/ugc-marketplace/discussions)
- Reach out to the maintainers through the contact methods in the [Code of Conduct](CODE_OF_CONDUCT.md)

Thank you for contributing to ugc-marketplace!
