# Releasing SignifyPy

SignifyPy releases use GitHub Actions and a PyPI API token stored in GitHub.
The package version published to PyPI is always bare semantic versioning like
`0.5.0`. Git tags and GitHub Releases use the same bare `X.Y.Z` format like
`0.5.0`.

## Release Flow

1. Land all releasable pull requests with Towncrier fragments under
   `newsfragments/`.
2. Prepare the release commit locally with one of:
   - `make release-patch`
   - `make release-minor`
   - `make release-major`
3. Review the generated release-prep commit. It should update:
   - `pyproject.toml`
   - `uv.lock`
   - `docs/changelog.md`
   - consumed `newsfragments/`
4. Push the release-prep commit.
5. Create and push the matching Git tag: `X.Y.Z`.
6. Wait for the `Tests` workflow to pass for that tagged commit.
7. Let the release workflow publish automatically once the build and publish
   jobs pass.
8. Confirm the workflow created:
   - a PyPI release `X.Y.Z`
   - a GitHub Release `X.Y.Z`

## Maintainer Commands

- `make dist-check`
  Builds `sdist` and wheel artifacts and validates them with `twine check`.
- `make release-patch`
  Bumps the patch version, rebuilds the changelog, removes consumed release
  fragments, refreshes `uv.lock`, and creates a release-prep commit.
- `make release-minor`
  Same as above for a minor version bump.
- `make release-major`
  Same as above for a major version bump.

The old `make release` target has been removed. Use `make dist-check` for local
artifact validation and `make release-*` for release preparation.

## Changelog Fragments

Every releasable change should land with one Towncrier fragment in
`newsfragments/`.

Use the fragment filename format:

- `<pr-or-issue>.<type>.md`

Valid fragment types are:

- `added`
- `changed`
- `fixed`
- `removed`
- `doc`
- `misc`

Example:

```text
138.fixed.md
```

The fragment body should be a short human-facing sentence or two. The release
prep targets collect those fragments into `docs/changelog.md` and remove the
consumed fragment files.

## Towncrier Examples

Create a fragment for PR or issue `100` using the configured SignifyPy types:

```bash
cd /Users/kbull/code/keri/kentbull/signifypy
./venv/bin/python -m towncrier create --dir newsfragments \
  --content "Documented the repository-secret PyPI publish flow." \
  100.doc.md
```

Another example for a bug fix:

```bash
cd /Users/kbull/code/keri/kentbull/signifypy
./venv/bin/python -m towncrier create --dir newsfragments \
  --content "Fixed release workflow auth to use the repository secret PYPI_API_TOKEN." \
  101.fixed.md
```

You can also create the fragment file yourself if that is faster:

```bash
cd /Users/kbull/code/keri/kentbull/signifypy
cat > newsfragments/102.misc.md <<'EOF'
Clarified the maintainer release runbook with concrete Towncrier examples.
EOF
```

Preview the unreleased changelog without modifying tracked files:

```bash
cd /Users/kbull/code/keri/kentbull/signifypy
./venv/bin/python -m towncrier build --draft --version 0.4.1
```

Build the actual `0.4.1` changelog entry during release preparation:

```bash
cd /Users/kbull/code/keri/kentbull/signifypy
./venv/bin/python -m towncrier build --yes --version 0.4.1
```

Or let the maintained release-prep target do the version bump, lock refresh,
Towncrier build, and release commit together:

```bash
cd /Users/kbull/code/keri/kentbull/signifypy
make release-patch
```

## CI Release Entry Points

SignifyPy supports two release entry points:

- Push a canonical Git tag `X.Y.Z`.
- Run the `Release` workflow manually with `release_tag=X.Y.Z`.

The manual workflow is for publishing an existing tag. It does not create tags,
edit versions, or rewrite release notes.

## CI Release Guards

The release workflow refuses to publish unless:

- the tag is canonical `X.Y.Z`
- `pyproject.toml` and `signify.__version__` both resolve to bare `X.Y.Z`
- the normal `Tests` workflow has passed for the same commit
- a changelog section exists for `X.Y.Z`

## GitHub And PyPI Setup

PyPI publishing currently depends on a project-scoped API token for the
`signifypy` package:

- create the token from a PyPI owner or maintainer account that can manage the
  `signifypy` project
- scope it to the `signifypy` project if possible
- store it as the `PYPI_API_TOKEN` repository secret on `signifypy`
- let `.github/workflows/release.yml` read it from repository secrets at
  publish time

Do not copy this token into `.pypirc`, workflow YAML, or personal shell
history. Treat it as rotation-managed operational state owned by repository
secrets.

## Troubleshooting Publish Auth

If the publish step reports invalid authentication:

- verify the token still exists on PyPI
- verify it is scoped to `signifypy` rather than to an unrelated project
- verify the stored secret includes the full `pypi-...` token value
- verify it is stored as the `PYPI_API_TOKEN` repository secret

## Recovery Rules

- Never overwrite an existing PyPI version.
- If PyPI accepted `X.Y.Z`, treat that release number as permanently consumed.
- If the publish workflow fails after PyPI accepts the version, fix forward
  with a new version and a new `X.Y.Z` tag.
- If the workflow fails before publish, fix the problem on a new commit,
  prepare the correct version again if needed, and push a corrected canonical
  tag.
