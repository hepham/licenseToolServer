# Git Commit Style Guide

## Conventional Commits
Format: `<type>(<scope>): <description>`

## Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

## Scopes
- `api`: Backend API changes
- `auth`: Authentication related
- `license`: License management
- `device`: Device tracking
- `dashboard`: Admin dashboard
- `db`: Database changes

## Examples
```
feat(license): add device limit validation
fix(auth): resolve JWT token refresh issue
docs(api): update license activation endpoint docs
refactor(device): extract fingerprint logic to service
test(license): add expiration date tests
chore(deps): update Django to 5.1
```

## Rules
- Use imperative mood ("add" not "added")
- No period at end
- Max 72 characters for subject
- Body for detailed explanation (optional)
