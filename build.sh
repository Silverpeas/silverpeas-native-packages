#!/usr/bin/env bash

# Requires:
# For DEB build:
#   app-arch/dpkg
#   sys-apps/fakeroot
# For RPM build:
#   app-arch/createrepo
#   app-arch/rpm

set -e

print_usage()
{
  echo "Usage: $0 (deb|rpm|all) <version> \n\
with:
  deb 	build a DEB package of Silverpeas
  rpm 	build a RPM package of Silverpeas
  all 	build both a DEB and a RPM package of Silverpeas"
}

fetch_sources()
{
  cd files/
  silverpeasFile=silverpeas-${VER}-jboss6.tar.gz
  if [ ! -e "${silverpeasFile}" ]; then
    rm -v silverpeas-*.tar.gz || true
    wget  http://www.silverpeas.org/files/silverpeas-${VER}-jboss6.tar.gz
  fi
  if [ ! -e "jboss-as-distribution-6.1.0.Final.zip" ]; then
    wget http://download.jboss.org/jbossas/6.1/jboss-as-distribution-6.1.0.Final.zip
  fi
  cd ..
}

if [ $# -lt 2 ]; then
  print_usage
  exit 1
fi

VER=$2

fetch_sources
case "$1" in
  "deb")
    ./build-deb.sh ${VER}
    ;;
  "rpm")
    ./build-rpm.sh ${VER}
    ;;
  "all")
    ./build-deb.sh ${VER}
    ./build-rpm.sh ${VER}
    ;;
  *)
    print_usage
    ;;
esac

