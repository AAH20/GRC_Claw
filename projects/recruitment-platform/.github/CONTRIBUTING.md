# Contributing to Recruitment Platform

Thank you for your interest in contributing to the Recruitment Platform! We welcome contributions from the community and are grateful for your help in making this project better.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Issue Reporting](#issue-reporting)
- [Security Issues](#security-issues)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/recruitment-platform.git
   cd recruitment-platform
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/GRC_Claw/recruitment-platform.git
   ```
4. **Create a new branch** for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix-name
   ```

## Development Setup

### Prerequisites

- Node.js >= 20.x
- npm >= 10.x or pnpm >= 8.x
- Git >= 2.x

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

### Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Build for production |
| `npm test` | Run all tests |
| `npm run test:watch` | Run tests in watch mode |
| `npm run test:coverage` | Run tests with coverage report |
| `npm run lint` | Run ESLint |
| `npm run lint:fix` | Run ESLint with auto-fix |
| `npm run format` | Format code with Prettier |
| `npm run type-check` | Run TypeScript type checking |

## How to Contribute

### Reporting Bugs

Before creating a bug report, please check the [existing issues](https://github.com/GRC_Claw/recruitment-platform/issues) to see if the problem has already been reported. If it has, add a comment to the existing issue instead of creating a new one.

When filing a bug report, please use the [Bug Report template](https://github.com/GRC_Claw/recruitment-platform/issues/new?template=bug_report.yml) and include as much detail as possible.

### Suggesting Enhancements

Enhancement suggestions are tracked as [GitHub issues](https://github.com/GRC_Claw/recruitment-platform/issues). Please use the [Feature Request template](https://github.com/GRC_Claw/recruitment-platform/issues/new?template=feature_request.yml) and provide a clear description of the enhancement and its use case.

### Contributing Code

1. Ensure you have a clear understanding of the feature or bug fix
2. Check if there's an existing issue for it, or create one
3. Fork the repository and create a branch
4. Write your code following our [Coding Standards](#coding-standards)
5. Write or update tests as appropriate
6. Ensure all tests pass
7. Submit a [Pull Request](#pull-request-process)

## Pull Request Process

1. **Update your branch** with the latest changes from upstream:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Ensure all tests pass** and the code lints cleanly:
   ```bash
   npm test
   npm run lint
   ```

3. **Commit your changes** following our [Commit Message Guidelines](#commit-message-guidelines)

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request** using the [Pull Request template](PULL_REQUEST_TEMPLATE.md)

6. **Fill out the PR template** completely:
   - Provide a clear description of the changes
   - Link any related issues
   - Include screenshots if applicable
   - Complete the checklist

7. **Address review feedback** promptly and professionally

8. **Wait for approval** from at least one maintainer

### PR Review Criteria

- [ ] Code follows project style and conventions
- [ ] Tests are included and passing
- [ ] Documentation is updated (if applicable)
- [ ] No breaking changes (or clearly documented)
- [ ] PR description is complete and clear
- [ ] Related issues are linked

## Coding Standards

### General Guidelines

- Follow the existing code style and conventions
- Write clear, self-documenting code
- Add comments for complex logic
- Keep functions small and focused
- Follow the Single Responsibility Principle

### TypeScript

- Use strict TypeScript
- Prefer `interface` over `type` for object shapes
- Use `const` assertions where appropriate
- Avoid `any` — use `unknown` if the type is truly unknown

### Testing

- Write unit tests for all new functionality
- Aim for >80% code coverage
- Use descriptive test names: `should <expected behavior> when <condition>`
- Follow the Arrange-Act-Assert pattern
- Mock external dependencies

### File Naming

- Components: `PascalCase.tsx` (e.g., `JobCard.tsx`)
- Utilities: `camelCase.ts` (e.g., `formatDate.ts`)
- Tests: `*.test.ts` or `*.spec.ts`
- Styles: `kebab-case.module.css` or co-located with component

## Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only changes |
| `style` | Changes that do not affect the meaning of the code (white-space, formatting, etc.) |
| `refactor` | A code change that neither fixes a bug nor adds a feature |
| `perf` | A code change that improves performance |
| `test` | Adding missing tests or correcting existing tests |
| `build` | Changes that affect the build system or external dependencies |
| `ci` | Changes to CI configuration files and scripts |
| `chore` | Other changes that don't modify src or test files |
| `revert` | Reverts a previous commit |

### Examples

```
feat(jobs): add bulk job posting functionality

fix(auth): resolve token expiration race condition

docs(readme): update installation instructions

test(api): add integration tests for job search endpoint
```

## Issue Reporting

### Before You File an Issue

1. Search existing issues to avoid duplicates
2. Check the [documentation](https://github.com/GRC_Claw/recruitment-platform/wiki)
3. Check [closed issues](https://github.com/GRC_Claw/recruitment-platform/issues?q=is%3Aissue+is%3Aclosed) — your issue may have been resolved

### Filing a Good Issue

- Use a clear and descriptive title
- Provide steps to reproduce the issue
- Include expected vs. actual behavior
- Specify your environment (OS, browser, Node version)
- Include relevant logs or error messages
- Add screenshots if applicable

## Security Issues

**Do not file public issues for security vulnerabilities.**

Please report security vulnerabilities privately via [GitHub Security Advisories](https://github.com/GRC_Claw/recruitment-platform/security/advisories/new) or email [team@grc-claw.com](mailto:team@grc-claw.com).

See our [Security Policy](SECURITY.md) for more details.

## Questions?

If you have questions about contributing, please:

1. Check our [Documentation](https://github.com/GRC_Claw/recruitment-platform/wiki)
2. Start a [GitHub Discussion](https://github.com/GRC_Claw/recruitment-platform/discussions)
3. Reach out to the maintainers at [team@grc-claw.com](mailto:team@grc-claw.com)

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project. See the [LICENSE](../LICENSE) file for details.

---

Thank you for contributing to the Recruitment Platform! 🎉
