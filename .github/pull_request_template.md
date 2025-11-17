## Description

Please include a summary of the changes and the related issue. Include relevant motivation and context.

Fixes # (issue)

## Type of Change

Please delete options that are not relevant.

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement
- [ ] Test coverage improvement

## Changes Made

Please describe the changes in detail:
- 
- 
- 

## Testing

Describe the tests that you ran to verify your changes:

- [ ] Unit tests pass
- [ ] Integration tests pass (if applicable)
- [ ] Manual testing completed
- [ ] Tested with sample DICOM data

### Test Configuration

* 3D Slicer Version:
* Python Version:
* Operating System:

## Screenshots (if applicable)

Add screenshots to demonstrate the changes, especially for UI modifications.

## Checklist

### Code Quality

- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

### Pre-commit Checks

- [ ] Code formatted with Black (`black --check tavi_analytics/`)
- [ ] Imports sorted with isort (`isort --check tavi_analytics/`)
- [ ] Flake8 linting passes (`flake8 tavi_analytics/`)
- [ ] Pylint checks pass (`pylint tavi_analytics/`)
- [ ] Bandit security scan passes (`bandit -r tavi_analytics/`)

### Documentation

- [ ] I have updated the README.md (if needed)
- [ ] I have updated CHANGELOG.md
- [ ] I have updated relevant documentation in `/doc`
- [ ] I have added docstrings to new functions/classes

### Testing

- [ ] I have added unit tests for new functionality
- [ ] All existing tests still pass
- [ ] Test coverage has not decreased
- [ ] I have tested edge cases and error conditions

## Module-Specific Changes

If your changes affect specific modules, please indicate:

- [ ] Module 1 (Data Import)
- [ ] Module 2 (Segmentation)
- [ ] Module 3 (Measurements)
- [ ] Module 4 (Visualization)
- [ ] Module 5 (Reports)
- [ ] Core infrastructure
- [ ] UI components
- [ ] Utilities

## Breaking Changes

Does this PR introduce breaking changes?

- [ ] No breaking changes
- [ ] Yes, breaking changes (please describe below)

If yes, describe what breaks and how users should adapt:

## Dependencies

Does this PR add new dependencies?

- [ ] No new dependencies
- [ ] Yes, new dependencies (please list below)

If yes, list new dependencies and justify their inclusion:

## Related Issues/PRs

List any related issues or pull requests:
- Related to #
- Depends on #
- Closes #

## Additional Notes

Add any additional notes for reviewers here.

---

## For Reviewers

### Review Checklist

- [ ] Code quality is acceptable
- [ ] Changes are well-documented
- [ ] Tests are comprehensive
- [ ] No security vulnerabilities introduced
- [ ] Performance impact is acceptable
- [ ] UI/UX changes are intuitive (if applicable)
- [ ] Changes align with project architecture
- [ ] CHANGELOG.md is updated
