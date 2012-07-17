#!/bin/sh

# Requires:
#   app-arch/dpkg

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <version>"
  exit 1
fi

VER=$1

echo "Building DEB package"
rm -v deb/*.tar.gz || true
silverpeasFile=silverpeas-${VER}-jboss6.tar.gz
cd deb/
if [ ! -e "$silverpeasFile" ]
then
  wget  http://www.silverpeas.org/files/silverpeas-${VER}-jboss6.tar.gz
fi
if [ ! -e "jboss-as-distribution-6.1.0.Final.zip" ]
then
  wget http://download.jboss.org/jbossas/6.1/jboss-as-distribution-6.1.0.Final.zip
fi
./build.sh ${VER}
cd ..

echo "Building DEB repository"
cp -v deb/silverpeas.deb repo/deb/binary/silverpeas_${VER}_all.deb
cd repo/deb/
dpkg-scanpackages binary /dev/null | gzip -9c > binary/Packages.gz
cd ../../
