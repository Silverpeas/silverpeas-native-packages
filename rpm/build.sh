#!/usr/bin/env bash

# Requires:
#   app-arch/rpm
#   app-arch/rpm-build

set -e

read -r -d '!' USAGE <<EOF
Usage: `basename $0` <distribution> <version> [<package release>]
With:
  distribution the type of the RPM-based GNU/Linux distribution for which
  Silverpeas has to be packaged: one of centos-5, centos-6, rhel-5, rhel-6, or fedora
If the package release isn't set, then it is set at 1 by default!
EOF

if [ -z "$1" ]; then
  echo "$USAGE"
  exit 1
fi

DIST=$1
VER=$2
PKG_VER=$3
BRANCH=`echo $VER | grep -o "[0-9]\+.[0-9]\+"`
test "Z$PKG_VER" == "Z" && PKG_VER=1

pushd $(dirname $0)

# prepare fresh directories
rm -rf BUILD RPMS SRPMS tmp || true
mkdir -p BUILD RPMS SRPMS 

# use res to fix around a bug with grep in some circumstances
res=0
echo "$DIST" | grep "5" > /dev/null || res=1 
if [ $res -eq 0 ]; then
  openoffice=openoffice.org-headless
else
  openoffice=libreoffice-headless
  res=0
  echo "$DIST" | grep "suse" > /dev/null || res=1
  test $res -eq 0 && openoffice=libreoffice
fi  

# build silverpeas
rpmbuild -ba --define="_topdir $PWD" --define="_root $PWD/tmp" --define="ver $VER" --define="rel $PKG_VER" --define="branch $BRANCH" --define="openoffice $openoffice" SPECS/silverpeas.spec

# build datasources
# -> PostgreSQL
rm -rf BUILD tmp || true
mkdir -p BUILD 
rpmbuild -ba --define="_topdir $PWD" --define="_root $PWD/tmp" --define="ver $VER" --define="rel $PKG_VER" --define="branch $BRANCH" SPECS/silverpeas-postgresql.spec

exit $?
