# Chapter 1: Setup

In this chapter, multiples tool will be introduced and setup. The intent is to have a clean python environment to reproduce the code. This is a very opinionated section, but it might be useful to challenge your existing tools with this section.

## Python version management

[*Mise*](https://mise.jdx.dev/) will be leveraged to handle python versions. It claims to be the *The front-end to your dev env* and it will be used to install specific versions of languages and tools.

It can be used for much more, and it is strongly advised to look at the [documentation](https://mise.jdx.dev/getting-started.html) to understand the true power of this tool not limited to python developement.

*Mise* first needs to be installed, see [documentation](https://mise.jdx.dev/getting-started.html#_1-install-mise-cli) for further instructions. You can launch the following:

```sh
curl https://mise.run | sh
```

Once installed, you will have to customize your `.bashrc` or your `.zhsrc` (or other terminal support) to activate *mise* on your terminal.

```sh
echo 'eval "$(~/.local/bin/mise activate bash)"' >> ~/.bashrc
```

*Mise* can now be used to install python at a specific version with the following command:

```sh
mise install python@3.12
```

It will download a pre-compiled version of python and make it available globally.

Let's now use it, you first need to position yourself at the root of the project and launch:

```sh
mise use python@3.12
```

It will create a [mise.toml](mise.toml) file with the following section

```toml
[tools]
python = "3.12"
```

And a [.python-version](.python-version) with the indication

```txt
3.12
```

With the help of these files, *mise* will be able to activate when located at the root of your project. It's also a great way to document other contributors of the requirements to launch this project without relying on README that becomes easily outdated.

## Python dependency management

A tool to help us add, remove and download dependencies is necessary. [Uv](https://docs.astral.sh/uv/), will be used later on as it's very fast and easy to use.

To install it, the official [documentation](https://docs.astral.sh/uv/getting-started/installation/); but in this tutorial *mise* will be leveraged:

```sh
mise use uv
```

This will both install and setup uv for the project. See how [mise.toml](.mise.toml) has been modified with the addition of:

```toml
[tools]
python = "3.12"
uv = "latest"
```

Now it can be used to initialize the project, namely:

```sh
uv init
```

This will create a folder structure for you and a `hello.py`. In this project, we have customized it a bit to add a tests section a pyspark_tdd package as part of `src` so it looks like:

```txt
.
├── src
│   ├── hello.py
├── tests
├── .python-version
├── .mise.toml
└── pyproject.toml
```

## Ignoring files

Every repository needs a set of files to ignore before adding them to a commit. This is done via a [.gitignore](../.gitignore) file and anyone can leverage existing templates for your language of preference.

If you start a project from scratch, you will need to first setup git

```sh
git init
```

*Github* maintains ignore files [template](https://github.com/github/gitignore/tree/main) for each language. You can leverage it with:

```sh
curl -L -o .gitignore https://raw.githubusercontent.com/github/gitignore/refs/heads/main/Python.gitignore
```

The chosen language for gitignore is in this project the python template.

## Adding formatting and linting

### Python

Linters and formatters are powerful tools to enforce code writing rules among developers. It takes away the pain of having to care how the code is written at the syntax level.

*Ruff* will be leveraged to format our python code as it's very powerful and can be run at file saves without latency.

*Ruff* will be added as a project *dev* dependency. A *dev* dependency is one that the project does not need to run, it can be related to tests, experimentation, formatting etc. Everything that is not meant to be shipped to production must be retained as a *dev* dependency to keep your python package as self contained as possible.

We can add *ruff* like so:

```sh
uv add ruff --dev
```

This will add a *dev* dependency in the [pyproject.toml](../pyproject.toml) with

```toml
[dependency-groups]
dev = [
    "ruff>=0.8.4",
]
```

This will also create a `.venv` at the current working directory. You might notice that the `.venv` is ignored from git which is intended. Indeed, you don't want to commit your `.venv` directory as it's a copy of the dependencies of your project and can be quite extensive.

It will also create an [uv.lock](../uv.lock) that documents your direct dependencies version and the indirect dependencies (the dependencies of your dependencies). This mechanism allows to segregates dependencies of your project from the rest.

Your project should now look like

```txt
.
├── .venv
├── src
│   ├── hello.py
├── tests
├── .python-version
├── .gitignore
├── .mise.toml
├── pyproject.toml
└── uv.lock
```

### Other languages

As a project is not just python files, but also configuration, pipelines, documentation etc, formatting these files too is also necessary.

Documenting how these files will be formatted is done using [editorconfig](https://editorconfig.org/#overview).
We will use the one from the [editorconfig](../.editorconfig) website.

### Your Integrated Development Environment (IDE)

Whichever *IDE* will be used, it's very important that you setup formatting at file saves to save you time and remove the pain from handling it by hand.

If you are using VSCode, you can install the [ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) extension and adjust the following to your *settings.json*

```json
"editor.formatOnSave": true,
"[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.fixAll": "explicit",
        "source.organizeImports": "explicit"
    },
    "editor.defaultFormatter": "charliermarsh.ruff"
},
```

## The first test

To see if everything works as expected, you will write a very simple unit test. In a test driven approach, the test is written before the source code.

A test framework is required to launch the test automation, [*pytest*](https://docs.pytest.org/en/stable/) will be used. You need to add it as a *dev* dependency

```sh
uv add pytest --dev
```

You can create a [`tests/test_dummy.py`](../tests/test_dummy.py) with the following code:

```python
from your_python_package.multiply import multiply


def test_my_dummy_function():
    assert multiply(1, 2) == 2
```

This requires a function `multiply` that can be defined as in `src/your_python_package/multiply.py`:

 ```python
 def multiply(a: int, b: int) -> int:
    return a * b
```

You can now run the tests, make sure you're using the right python from the `.venv`

```sh
which python
```

should display something like `/$HOME/somepath/your_project/.venv/bin/python`. If not, you can restart a new terminal, *mise* should be able to resolve.

Then run

```sh
pytest
```

Then it will display an error:

```txt
tests/test_dummy.py:1: in <module>
    from your_python_package.multiply import multiply
E   ModuleNotFoundError: No module named 'your_python_package'
```

You need to add an extra entry for *pytest* to detect the `src` layout. In [pyproject.toml](../pyproject.toml), you can add:

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
```

Now

```sh
pytest
```

should display

```txt
============================================================= test session starts ===============================================================
platform linux -- Python 3.12.8, pytest-8.3.4, pluggy-1.5.0
rootdir: /home/somepath/src/your_project
configfile: pyproject.toml
collected 1 item                                                                                                                                 

tests/test_dummy.py .                                                                                                                      [100%]

=============================================================== 1 passed in 0.01s ================================================================
```

You can do some housekeeping and remove the unnecessary `src/your_python_package/hello.py`.

You now have a proper setup to start working.

## What's next

Now that one test is implemented, the continuous integration (ci) must be setup. In a collaborative way of working, the ci is the only source of truth to guarantee if everything is broken or not.

That will be the topic of the next chapter.
