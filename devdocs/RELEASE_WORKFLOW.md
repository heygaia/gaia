# Release Workflow

This document explains how our automated release process works using Release Please.

## Overview

We use [Release Please](https://github.com/googleapis/release-please) to automate releases. When you push to `master`, Release Please automatically:

1. Parses commit messages for conventional commits
2. Creates/updates a Release PR with version bumps and changelog
3. Tags and creates a GitHub release when the Release PR is merged

## How It Works

### 1. Write Conventional Commits

Use these prefixes in your commit messages:

- `feat:` - New feature (minor version bump)
- `fix:` - Bug fix (patch version bump)
- `feat!:` or `fix!:` - Breaking change (major version bump)
- `chore:`, `docs:`, `refactor:` - No version bump

**Example:**

```
feat: add user authentication
fix: resolve login button issue
feat!: change API response format
```

### 2. Push to Master

When commits with releasable changes (`feat`, `fix`, `deps`) are pushed to master, Release Please automatically creates or updates a Release PR.

### 3. Release PR Lifecycle

Release PRs have status labels:

- `autorelease: pending` - PR is ready for review/merge
- `autorelease: tagged` - PR merged, release tagged
- `autorelease: published` - GitHub release published

### 4. Merge Release PR

When you merge the Release PR, Release Please:

1. Updates `CHANGELOG.md` and version files
2. Creates a git tag with the new version
3. Creates a GitHub Release

## Best Practices

- **Use squash-merge** for PRs to maintain clean commit history
- **Write clear commit messages** that explain the change's impact
- **Review Release PRs** before merging to ensure correct version bumps

## Manual Version Override

To release a specific version, add `Release-As: x.x.x` to your commit body:

```bash
git commit --allow-empty -m "chore: release 2.0.0" -m "Release-As: 2.0.0"
```

## Troubleshooting

### No Release PR Created?

1. **Check for releasable commits** - Ensure you have `feat:`, `fix:`, or `deps:` commits
2. **Remove stale labels** - Look for old PRs with `autorelease: pending` labels
3. **Force rerun** - Add `release-please:force-run` label to trigger manually

### Fix Release Notes

Edit the merged PR body and add:

```
BEGIN_COMMIT_OVERRIDE
feat: corrected commit message for release notes
END_COMMIT_OVERRIDE
```

## Resources

- [Release Please Docs](https://github.com/googleapis/release-please)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Customizing Guide](https://github.com/googleapis/release-please/blob/main/docs/customizing.md)
- [Troubleshooting Guide](https://github.com/googleapis/release-please/blob/main/docs/troubleshooting.md)
