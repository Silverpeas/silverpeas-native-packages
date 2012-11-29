#!/usr/bin/env bash

# Requires:
# For DEB build:
#   app-arch/dpkg
#   sys-apps/fakeroot
# For RPM build:
#   app-arch/createrepo
#   app-arch/rpm

set -e

read -r -d '!' USAGE <<EOF
Usage: `basename $0` (deb|rpm) <version> [<package version>]
with:
  deb 	build a DEB package of Silverpeas
  rpm 	build a RPM package of Silverpeas
  all   build both a DEB and a RPM packages of Silverpeas
If the package release isn't set, then it is set at 1 by default!
EOF

print_usage()
{
  echo "$USAGE"
}

fetch_sources()
{
  pushd files/
  silverpeasFile=silverpeas-${VER}-jboss6.tar.gz
  if [ ! -e "${silverpeasFile}" ]; then
    rm -v silverpeas-*.tar.gz || true
    wget  http://www.silverpeas.org/files/silverpeas-${VER}-jboss6.tar.gz
  fi
  if [ ! -e "jboss-as-distribution-6.1.0.Final.zip" ]; then
    wget http://download.jboss.org/jbossas/6.1/jboss-as-distribution-6.1.0.Final.zip
  fi
  popd
}

if [ $# -lt 2 ]; then
  print_usage
  exit 1
fi

VER=$2
PKG_VER=$3

fetch_sources
case "$1" in
  "deb")
    ./build-deb.sh ${VER} ${PKG_VER}
    ;;
  "rpm")
    ./build-rpm.sh ${VER} ${PKG_VER}
    ;;
  "all")
    ./build-deb.sh ${VER} ${PKG_VER}
    ./build-rpm.sh ${VER} ${PGG_VER}
    ;;
  *)
    print_usage
    ;;
esac

