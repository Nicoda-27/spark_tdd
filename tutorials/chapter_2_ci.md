# Chapter 2: Continuous Integration (ci)

Having a ci is mandatory for any project that aims at having multiple contributors. In the following chapter, a proposal ci will be implemented.

As ci implementation is specific to a collaborative platform being *Github*, *Gitlab*, *Bitbucket*, *Azure Devops* etc. The following chapter will try to provide a technology agnostic ci as much as possible.

Similar concepts are available in all ci, you will have to transpose the concepts that will be used here.

## Content of the ci

The ci here will be very minimal but showcases concepts that you implemented in [Chapter 1](chapter_1_setup.md), namely:

- Python setup
- Project setup
- Code Formatting
- Test automation

There are many more addition to the continuous integration that will not be tackled here. A minimal ci is required to guarantee non regressions in terms of:

- code styling rules to guarantee no indivual contributors diverge from the coding style
- tests, namely all tests must be passing

## Implementation

*Github* provides extensive [documentation](https://github.com/features/actions) for you to tweak your ci.

*Github* is expecting ci files to be provided at a specific location, you can therefore create a file in [`.github/workflows/ci.yaml`](../.github/workflows/ci.yaml).

In this file, you can add

```yaml
name: Continuous Integration
run-name: Continuous Integration
on: [push]
jobs:
  Continuous-Integration:
    runs-on: ubuntu-latest
```

- The `name` and `run-name` define the names of the pipeline that will run.
- The `on` defines the event that will trigger the pipeline to run, `push` means that for every commit the pipeline will run.
- The `jobs` defines a list of jobs, the ci is made of one job with multiple steps for the sake of simplicity.
- The `runs-on` defined the docker image used to run (the runner) the environment against, it's a list of [docker images](https://github.com/actions/runner-images) maintained by *Github*.

Now into the steps section we can add:

```yaml
steps:
  - name: Check out repository code
    uses: actions/checkout@v4
  - uses: jdx/mise-action@v2
  - name: Run Formatting
    run: |
      uv run ruff check
  - name: Run Tests
    run: |
      uv run pytest
```

- The `actions/checkout@v4` is the *Github* action that checkout the current branch of the repository.
- The `jdx/mise-action@v2` is the *Github* action that will read the `mise.toml` and install everything for us.
- The `Run Formatting` step will install the dependencies and run the formatting. It there is an error, the command will fail and the pipeline too.
- The `Run Tests` step will run the tests. It there is an error, the command will fail and the pipeline too.

## Ci as documentation

As it was stated, the ci is the only source of truth. If it passes on ci, it should pass on your local setup. If not, it means there are discrepancies between the ci setup and yours.

Going through the ci implementation will help you on reproducibility. Maybe you're not using the same way to install python version, or the same dependency management tool. You need to align your tools and the ones presented in [chapter 1](chapter_1_setup.md) help not to conflict with your local setup. You might have installed python package globally or you might have manually changed `PYTHON_HOME` or your `PATH` and this can easily be a mess.

To help on reproducibility, a [dev container](https://code.visualstudio.com/docs/devcontainers/containers) approach can be used. It means, the ci will run inside a container and this container can be reused as a developer environment. This will not be implemented for the moment.

## A better ci structure

To improve readability and segregates between code formatting and testing, *Github* actions can be implemented as job with interdependencies. Then, the workflow becomes:

```yaml
name: Continuous Integration
run-name: Continuous Integration
on: [push]
jobs:
  Formatting:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository code
        uses: actions/checkout@v4
      - uses: jdx/mise-action@v2
      - name: Run Formatting
        run: |
          uv run ruff check
  Tests:
    runs-on: ubuntu-latest
    needs: [Formatting]
    steps:
      - name: Check out repository code
        uses: actions/checkout@v4
      - uses: jdx/mise-action@v2
      - name: Run Tests
        run: |
          uv run pytest
```

In here we added the `needs: [Formatting]` to create dependencies between ci job. It means, we will not run the tests until the code style is compliant; this will save some time and resources. Indeed, if the code is not formatted, don't even bother running the tests. The execution graph will be like:

![image](images/ci_execution_graph.png)

We can see here some duplication, which is not ideal as for future code improvements, you will have to do it at two places at the same time. This is technical debt that one would have to tackle using [composite action](https://docs.github.com/en/actions/sharing-automations/creating-actions/creating-a-composite-action). We will consider it's ok for now.

## Caching dependency resolution

You will see additional steps in the [`ci.yaml`](../.github/workflows/ci.yaml), namely related to cache

```yaml
    - name: Restore uv cache
        uses: actions/cache@v4
        with:
          path: /tmp/.uv-cache
          key: uv-${{ runner.os }}-${{ hashFiles('uv.lock') }}
          restore-keys: |
            uv-${{ runner.os }}-${{ hashFiles('uv.lock') }}
            uv-${{ runner.os }}
```

These steps aim at caching the `.venv` when there are no changes on the `uv.lock` and reusing it. The intent is to speed up the ci execution as dependency resolution and installation can be time consuming.

An extra step to minimize caching size is added as *mise* proposes such feature, namely an extra step and an environment variable is added to configure the location of the cache.

```yaml
      - name: Minimize uv cache
        run: uv cache prune --ci
    env:
      UV_CACHE_DIR: /tmp/.uv-cache
```

## What's next

On the next chapter, you will implement your first spark code and implement a way to guarantee test automation of it. This is long overdue as we spent 3 chapters on setup...
