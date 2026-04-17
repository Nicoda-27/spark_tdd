# Chapter 6: A better setup

In [chapter 2](chapter_2_ci.md), we mentioned devcontainers as a way to make the development environment explicit.

A [development container (devcontainer)](https://code.visualstudio.com/docs/devcontainers/containers) describes the developer environment as an OCI image (often built with a `Dockerfile`). The usual runtime is Docker, but tools such as [Podman](https://podman.io/) are compatible with the same workflow. For simplicity, this chapter assumes Docker is installed on your machine.

The full specification lives in the [Dev Container Specification](https://containers.dev/implementors/spec/) on [containers.dev](https://containers.dev/). What follows is only a small subset of what devcontainers can express.

## The devcontainer specification

The repository uses a [.devcontainer](../.devcontainer/) directory to hold the image definition. The [Dockerfile](../.devcontainer/Dockerfile) is the main build recipe; we walk through it below.

The first line selects the Dockerfile syntax version. The base image is Debian (`debian:trixie-slim`); you can swap it for another image if you need a smaller footprint or a different distribution.

```dockerfile
# syntax=docker/dockerfile:1.4
FROM debian:trixie-slim AS build
```

The optional `FORCE_REBUILD` argument is a cache-busting knob: changing its default value invalidates Docker’s layer cache for everything that follows, which is useful when you want a full rebuild without editing other lines.

```dockerfile
ARG FORCE_REBUILD=20260417
```

As in [chapter 1](chapter_1_setup.md), [mise](https://mise.jdx.dev/) drives tool versions. The `mise.toml` file is copied into the build context so `mise install` can install `uv` (and anything else declared there).

Extra environment variables pin where `mise` and `uv` install binaries and Python:

```dockerfile
COPY mise.toml /mise.toml

ENV UV_TOOL_BIN_DIR=/usr/local/bin \
    UV_TOOL_DIR=/opt/uv/venv \
    UV_PYTHON_INSTALL_DIR=/opt/uv/python \
    MISE_DATA_DIR=/opt/mise

ENV PATH="$MISE_DATA_DIR/shims:$PATH"
```

System packages and tooling (for example `git`, `zip`, and the Docker CLI) are installed in [devcontainer-setup.sh](../.devcontainer/devcontainer-setup.sh), which is copied in and executed next:

```dockerfile
COPY devcontainer-setup.sh /devcontainer-setup.sh
RUN /devcontainer-setup.sh

WORKDIR /code

FROM build AS devcontainer
```

The final stage `devcontainer` matches the `target` in [devcontainer.json](../.devcontainer/devcontainer.json), which also selects the Dockerfile, platform, and IDE extensions (here, the Python extension for VS Code).

Build the image from the repository root:

```sh
docker build -f .devcontainer/Dockerfile --target devcontainer .devcontainer
```

## Using the devcontainer in your IDE

Modern editors can open the project *inside* the container using a devcontainer extension—for VS Code, see [Developing inside a Container](https://code.visualstudio.com/docs/devcontainers/containers).

That gives newcomers a reproducible environment: the extension detects `.devcontainer/`, builds (or pulls) the image using `devcontainer.json`, and starts a shell where tools from the image are already on `PATH`. Much of what [chapter 1](chapter_1_setup.md) described as manual setup becomes versioned files in the repo, which you can test in CI so they stay accurate.

## Using the devcontainer in CI

Reusing the same image in continuous integration avoids depending on whatever happens to be preinstalled on the GitHub-hosted runner: the maintainer owns the image, so runner image updates do not silently change your pipeline. That improves **reproducibility**.

The workflow [.github/workflows/ci.yaml](../.github/workflows/ci.yaml) implements this pattern.

### Image tag

A tag is derived from a hash of every file under `.devcontainer/`, so the image only changes when that folder’s content changes (see [`hashFiles`](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions#hashfiles)). The tag is written to **`$GITHUB_OUTPUT`** (so later jobs can use `needs.build-and-push.outputs.tag`) and to **`$GITHUB_ENV`** as `DEVCONTAINER_TAG`.

```yaml
      - name: Compute devcontainer image tag
        id: devcontainer_tag
        run: |
          TAG="devcontainer-${{ hashFiles('.devcontainer/**') }}"
          echo "tag=${TAG}" >> "$GITHUB_OUTPUT"
          echo "DEVCONTAINER_TAG=${TAG}" >> "$GITHUB_ENV"
```

The `build-and-push` job exposes that tag to other jobs with `outputs.tag: ${{ steps.devcontainer_tag.outputs.tag }}`.

### Login, pull cache, then build if missing

The job logs in to Docker Hub, then tries to **pull** the image. If that tag already exists in the registry, the build is skipped; otherwise Buildx builds and pushes.

Configure a repository **variable** `DOCKERHUB_REPOSITORY` (for example `youruser/spark-tdd-devcontainer`) and **secrets** `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`. The `container.image` field cannot use the `secrets` context for the image name, which is why the repository name lives in **`vars`**.

```yaml
      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Pull devcontainer image if already published
        id: pull
        continue-on-error: true
        env:
          REPO: ${{ vars.DOCKERHUB_REPOSITORY }}
        run: docker pull "${REPO}:${DEVCONTAINER_TAG}"

      - name: Set up Docker Buildx
        if: steps.pull.outcome != 'success'
        uses: docker/setup-buildx-action@v3

      - name: Build and push devcontainer image
        if: steps.pull.outcome != 'success'
        uses: docker/build-push-action@v6
        with:
          context: .devcontainer
          file: .devcontainer/Dockerfile
          target: devcontainer
          push: true
          tags: ${{ vars.DOCKERHUB_REPOSITORY }}:${{ env.DEVCONTAINER_TAG }}
```

### Downstream jobs

Formatting and tests run **inside** that image via `jobs.<job_id>.container`, using the tag exported by the `build-and-push` job output (still driven by the same `devcontainer_tag` step):

```yaml
  Formatting:
    runs-on: ubuntu-latest
    needs: [build-and-push]
    container:
      image: ${{ vars.DOCKERHUB_REPOSITORY }}:${{ needs.build-and-push.outputs.tag }}
      credentials:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}
```

The test job also mounts the host Docker socket so [Testcontainers](https://testcontainers.com/) can start sibling containers (for example Spark) from within the job container.
