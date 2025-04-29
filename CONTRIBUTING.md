# Contribution guidelines

Thanks that you want to contribute to viur-cli!

## Issues

In case you encounter a bug, or you miss a feature, please [file an issue](https://github.com/viur-framework/viur-cli/issues).

## Pull Requests

If you created a solution for a problem or added a feature, please make a pull request.
This can also be done as a draft, in case you want to discuss a change or aren't finished.

### Conventional Commits

When creating a pull request, try to follow the [Conventional Commit](https://www.conventionalcommits.org) paradigm.
This is also part of the pull requests naming scheme, as pull requests are usually squash merged.

| Type | | SemVer |
| --- | --- | --- |
| any of following types | - A commit that has a footer:<br />`BREAKING CHANGE: <description>`<br /><br />AND/OR<br /><br /> - A commit that has a ! after the type or optional scope:<br />`<type>[optional scope]!: <description>`  |    `MAJOR`<br />Breaking Change |conventional commit
| `feat` | A new feature, introducing a new feature to the codebase | `MINOR` |
| `fix`  | A bug fix, patching a bug in your codebase | `PATCH` |
| `refactor` | A change that neither fixes a bug nor adds a feature | - |
| `docs` | Documentation only changes | - |
| `style` | Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc) | - |
| `perf` | A code change that improves performance | - |
| `test` | Adding missing or correcting existing tests | - |
| `chore` | Changes to the build process or auxiliary tools and libraries such as documentation generation | - |
| `ci` | Changes to the continuous integration | - |
| `build` | Changes to the build process or code generation | - |

Visit [Vahid Hallaji's Blog](https://hallaji.com/blog/summary-of-conventional-commits) for a nice a short explanation.

### Review

viur-cli needs you! All developers are invited to review pull requests, so we can merge PRs as soon as possible and make changes according to our standards and that only works, if people help out.
If you are not on the reviewers list, just add yourself or ask a maintainer to configure access for you.

If there are documentation changes to review, there should be a 'doc-review' tag added to the issue or pull request

## Documentation

Please document your changes and provide info in any form you can.

## Versioning

`viur-cli` uses the semantic versioning scheme.<br>
Any `major.minor.bugfix` release is being published to [PyPI](https://pypi.org/project/viur-cli).

Furthermore, the following rules provided in [PEP-440](https://peps.python.org/pep-0440/#pre-releases) apply to pre-releases which are also made available to PyPI for open tests.

- `devN` for development and test releases (including release tests, may be broken)
- `alphaN` for feature-incomplete alpha releases
- `betaN` for feature-completed beta releases
- `rcN` for release-candidates, where bugs may be fixed

In all cases, `N` is a number counted upwards for every pre-release kind.

## Dependency management

`viur-cli` has several dependencies, which are maintained by the [`Pipfile`](/Pipfile).

- For local development and dependency management, run `pipenv install --dev`
- Update dependencies with `pipenv update`
- Regenerate requirements.txt from locked pipenv using `pipenv requirements --hash >requirements.txt`

Try to keep external dependencies low.

## Releasing

In case you have appropriate permissions, a release can be done this way:

- Bump version number in `src/viur_cli/version.py`
- Update [`CHANGELOG.md`](/CHANGELOG.md) and also check version number there
- Commit and tag version with `f"v{__version__}`

## Branches

`viur-cli` has two actively maintained branches:

- **main** is the current stable version as released on PyPI.
- **develop**  is the next minor version and may be released as release candidates to PyPI.

## Maintenance

Maintainer of this project is [@grashalmbeisser](https://github.com/Grashalmbeisser).
