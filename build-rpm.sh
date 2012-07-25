#!/usr/bin/env bash

# Requires:
#   app-arch/createrepo
#   app-arch/rpm

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <root path> <version>"
  exit 1
fi

VER=$1

echo "Building RPM package"
if [ -e rpm/SOURCES ]; then
  rm -rf rpm/SOURCES || true
fi
mkdir rpm/SOURCES
cp -v files/* rpm/SOURCES/
cp -v rpm/*.init rpm/SOURCES/
rpm/build.sh ${VER}

echo "Building RPM repository"
cp -v rpm/RPMS/noarch/* repo/rpm/noarch/
cd repo
createrepo -s sha rpm
cd ../
