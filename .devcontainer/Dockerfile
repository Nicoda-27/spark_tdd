# syntax=docker/dockerfile:1.4

FROM debian:trixie-slim AS build

ARG FORCE_REBUILD=20260416

COPY mise.toml /mise.toml

ENV UV_TOOL_BIN_DIR=/usr/local/bin \
    UV_TOOL_DIR=/opt/uv/venv \
    UV_PYTHON_INSTALL_DIR=/opt/uv/python \
    MISE_DATA_DIR=/opt/mise

ENV PATH="$MISE_DATA_DIR/shims:$PATH"

COPY devcontainer-setup.sh /devcontainer-setup.sh
RUN /devcontainer-setup.sh

WORKDIR /code

FROM build AS devcontainer
