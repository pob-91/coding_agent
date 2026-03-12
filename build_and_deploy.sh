#!/bin/bash

set -e

echo "This script will build and create a new version of the deployed image in gitea, are you sure you want to continue?"

read -p "Continue? (y/N): " confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborted."
    exit 1
fi

read -p "Enter version number (e.g. 0.1.2): " version

if [[ -z "$version" ]]; then
    echo "Version number is required."
    exit 1
fi

make build

docker tag coding-agent:latest "git.thesanders.farm/nerd/coding-agent:${version}"

docker push "git.thesanders.farm/nerd/coding-agent:${version}"