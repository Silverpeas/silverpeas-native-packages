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

VER=$1
PKG_VER=$2

echo "Building DEB package"
cd deb/
./build.sh ${VER} ${PKG_VER}
cd ../
if [ ! -e "repo/debian/binary" ]; then
	mkdir -p repo/debian/binary
fi
echo "Building DEB repository"
mv -v deb/silverpeas*${VER}*.deb repo/debian/binary/
cd repo/debian/
dpkg-scanpackages binary /dev/null | gzip -9c > binary/Packages.gz
cd ../../
