# Development Workflow

## Test Coverage

- **Minimum Coverage:** 80%
- Run tests before committing
- All new features must include tests

## Commit Strategy

- **Frequency:** Commit after each task
- **Format:** Conventional Commits (see code_styleguides/git-commits.md)
- Keep commits atomic and focused

## Task Summaries

- **Method:** Git Notes
- Attach summary to each task completion commit
- Include: what was done, any issues encountered

## Code Review

- Self-review before marking task complete
- Run linters and formatters
- Verify tests pass locally

## Phase Completion

### User Manual Verification Protocol

At the end of each phase, perform manual verification:

1. **Review Changes:** List all files modified/created
2. **Test Functionality:** Manually test new features
3. **Verify Requirements:** Check against spec.md
4. **Document Issues:** Note any deviations or concerns
5. **Sign-off:** Confirm phase completion or request revisions

## Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/<track-id>/<description>` - Feature branches
- `fix/<track-id>/<description>` - Bug fix branches

## Definition of Done

A task is complete when:
- [ ] Code is written and formatted
- [ ] Tests are written and passing
- [ ] Coverage meets minimum threshold
- [ ] Linters pass with no errors
- [ ] Changes are committed with proper message
- [ ] Git note attached with summary
