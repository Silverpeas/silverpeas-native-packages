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
test "Z$PKG_VER" == "Z" && PKG_VER=1

SILVERPEAS_PKG=debian/silverpeas-postgresql

ROOT=`pwd`/tmp
export SILVERPEAS_HOME=${ROOT}/opt/silverpeas
JBOSS_HOME=${SILVERPEAS_HOME}/jboss-6.1.0.Final
SILVERPEAS_DATA=${ROOT}/var/data/silverpeas
SILVERPEAS_DOC=${ROOT}/usr/share/doc/silverpeas

# prepare fresh directories
rm -rf ${ROOT}
mkdir -p ${ROOT}/DEBIAN
mkdir -p ${ROOT}/opt
mkdir -p ${SILVERPEAS_DATA}/import
mkdir -p ${SILVERPEAS_DOC}

# changelog
DATE=`date -R`

echo "silverpeas (${VER}) stable; urgency=low

  * See the release note in https://www.silverpeas.org/docs/core/releasenotes.html for more details
    about the ${VERS} release.

 -- Silverpeas Development Team <silverpeas-dev@googlegroups.com>  ${DATE}

" | cat - debian/changelog > /tmp/changelog && mv /tmp/changelog debian/changelog

# lintian overrides
# mkdir -p tmp/usr/share/lintian/overrides/
# cp -T debian/silverpeas.lintian-overrides tmp/usr/share/lintian/overrides/silverpeas

# configuration
mkdir -p ${SILVERPEAS_HOME}/setup/settings
cp ../files/config-postgresql.properties ${SILVERPEAS_HOME}/setup/settings/config-datasource.properties

# preinst, postinst, prerm and postrm
cp -T ${SILVERPEAS_PKG}/silverpeas-postgresql.preinst ${ROOT}/DEBIAN/preinst
chmod 755 ${ROOT}/DEBIAN/preinst
cp -T ${SILVERPEAS_PKG}/silverpeas-postgresql.postinst ${ROOT}/DEBIAN/postinst
chmod 755 ${ROOT}/DEBIAN/postinst
cp -T ${SILVERPEAS_PKG}/silverpeas-postgresql.prerm ${ROOT}/DEBIAN/prerm
chmod 755 ${ROOT}/DEBIAN/prerm
cp -T ${SILVERPEAS_PKG}/silverpeas-postgresql.postrm ${ROOT}/DEBIAN/postrm
chmod 755 ${ROOT}/DEBIAN/postrm

dpkg-gencontrol -v"${VER}-${PKG_VER}" -c${SILVERPEAS_PKG}/control -Ptmp

fakeroot dpkg-deb -b ${ROOT} silverpeas-postgresql_${VER}-${PKG_VER}_all.deb

