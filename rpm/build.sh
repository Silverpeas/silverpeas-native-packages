#!/usr/bin/env bash

# Requires:
#   app-arch/createrepo
#   app-arch/rpm
#   app-arch/rpm-build

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <version>"
  exit 1
fi

VER=$1

pushd $(dirname $0)

# prepare fresh directories
rm -rf BUILD RPMS SRPMS tmp || true
mkdir -p BUILD RPMS SRPMS 

# build
rpmbuild -ba --define="_topdir $PWD" --define="_root $PWD/tmp" --define="ver $VER" SPECS/silverpeas.spec
