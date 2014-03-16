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
DIST=`echo $VER | grep -o "[0-9]\+.[0-9]\+"`
REPO="repo/debian/dists/${DIST}/main/binary-all"

echo "Building DEB package"
cd deb/
./build.sh ${VER} ${PKG_VER}
cd ../
if [ ! -e "$REPO" ]; then
	mkdir -p "$REPO"
fi
echo "Building DEB repository"
mv -v deb/silverpeas*${VER}*.deb "$REPO"
pushd "$REPO/../"
dpkg-scanpackages binary-all /dev/null dists/$DIST/main/ | gzip -9c > binary-all/Packages.gz
popd
cat > repo/debian/silverpeas-${DIST}.list << EOF
deb [arch=all] http://www.silverpeas.org/repo/debian ${DIST} main
EOF
cd ../../
