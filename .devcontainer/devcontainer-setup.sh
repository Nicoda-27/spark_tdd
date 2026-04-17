#!/bin/sh

set -e
# set -x

export DEBIAN_FRONTEND=noninteractive

# Install dependencies
apt-get update
apt-get install -y \
  git \
  zip \
  curl \
  unzip \
  time \
  gpg \
  lsb-release

curl https://mise.run | MISE_INSTALL_PATH=/usr/local/bin/mise sh
mise trust
mise install

# Install docker
# from https://docs.docker.com/engine/install/debian/
#shellcheck disable=SC2174
mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
		"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list >/dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
docker --version

# Clean up
time rm -rf /var/lib/apt/lists

