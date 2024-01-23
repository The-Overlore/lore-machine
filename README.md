# overlore

[![Release](https://img.shields.io/github/v/release/elonmusk/overlore)](https://img.shields.io/github/v/release/elonmusk/overlore)
[![Build status](https://img.shields.io/github/actions/workflow/status/elonmusk/overlore/main.yml?branch=main)](https://github.com/elonmusk/overlore/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/elonmusk/overlore/branch/main/graph/badge.svg)](https://codecov.io/gh/elonmusk/overlore)
[![Commit activity](https://img.shields.io/github/commit-activity/m/elonmusk/overlore)](https://img.shields.io/github/commit-activity/m/elonmusk/overlore)
[![License](https://img.shields.io/github/license/elonmusk/overlore)](https://img.shields.io/github/license/elonmusk/overlore)

power to the autonomous, generative agency peoples

- **Github repository**: <https://github.com/elonmusk/overlore/>
- **Documentation** <https://elonmusk.github.io/overlore/>

## Getting started with your project

First, create a repository on GitHub with the same name as this project, and then run the following commands:

```bash
git init -b main
git add .
git commit -m "init commit"
git remote add origin git@github.com:elonmusk/overlore.git
git push -u origin main
```

Finally, install the environment and the pre-commit hooks with

```bash
make install
```

You are now ready to start development on your project!
The CI/CD pipeline will be triggered when you open a pull request, merge to main, or when you create a new release.

To finalize the set-up for publishing to PyPi or Artifactory, see [here](https://fpgmaas.github.io/cookiecutter-poetry/features/publishing/#set-up-for-pypi).
For activating the automatic documentation with MkDocs, see [here](https://fpgmaas.github.io/cookiecutter-poetry/features/mkdocs/#enabling-the-documentation-on-github).
To enable the code coverage reports, see [here](https://fpgmaas.github.io/cookiecutter-poetry/features/codecov/).

## Running your project

From the root of the project, simply run `poetry run lore-machine`

Flags:

- `--mock`: to use mock GTP responses.
- `--address <address>`: address where the websocket connection will be served to (default: `locahost`).

## Running The Overlore System

The Overlore System runs as a plugin to Eternums. The current source of truth of our system design can be found in the [docker compose file](https://github.com/The-Overlore/eternum/blob/main/docker-compose.yml#L3) in our Eternums fork.

We are currently exploring possibly using `litefs` to sync the worlddb maintained by the torii process to our lore machine process. In practice, it means that a `world_db` param can be passed on startup in the loremachine that will be synced from torii, the responsibiliy of which is owned by `litefs.`

## Releasing a new version

---

Repository initiated with [fpgmaas/cookiecutter-poetry](https://github.com/fpgmaas/cookiecutter-poetry).
