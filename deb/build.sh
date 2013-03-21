#!/usr/bin/env bash

# Requires:
#   app-arch/dpkg
#   sys-apps/fakeroot

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <version> [<package version>]"
  echo "If the package release isn't set, then it is set at 1 by default"
  exit 1
fi

./build-silverpeas.sh $*
./build-postgresql.sh $*
