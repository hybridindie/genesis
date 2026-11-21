#!/usr/bin/env bash
set -eu
cp -R "$(dirname "$0")/files/." .
bash "$(dirname "$0")/setup-git.sh"
