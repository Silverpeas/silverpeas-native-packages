#!/usr/bin/env bash

# Requires:
#   app-arch/dpkg
#   sys-apps/fakeroot

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <version>"
  exit 1
fi

VER=$1

echo "Building DEB package"
cd deb/
./build.sh ${VER}
cd ../
if [ ! -e "repo/deb/binary" ]; then
	mkdir -p repo/deb/binary
fi
echo "Building DEB repository"
cp -v deb/silverpeas.deb repo/deb/binary/silverpeas_${VER}_all.deb
cd repo/deb/
dpkg-scanpackages binary /dev/null | gzip -9c > binary/Packages.gz
cd ../../
