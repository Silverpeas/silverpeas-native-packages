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

SILVERPEAS_PKG=debian/silverpeas

ROOT=`pwd`/tmp
export SILVERPEAS_HOME=${ROOT}/opt/silverpeas
export JBOSS_HOME=${SILVERPEAS_HOME}/jboss-6.1.0.Final
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

# prepare silverpeas
tar xzf ../files/silverpeas-${VER}-jboss6.tar.gz
mv silverpeas-${VER}-jboss6 ${SILVERPEAS_HOME}

# prepare jboss
unzip ../files/jboss-as-distribution-6.1.0.Final.zip -d ${SILVERPEAS_HOME}/
pushd ${JBOSS_HOME}/server
rm -rf all jbossweb-standalone minimal standard
popd

for script in `ls ../scripts/`; do
  ../scripts/${script}
done

# Fix EOL in configuration files
for i in ${SILVERPEAS_HOME}/bin/*.sh; do
  echo "dos2unix $i"
  awk '{ sub("\r$", ""); print }' $i > $i.new
  mv $i.new $i
  chmod +x $i
done

pushd ${SILVERPEAS_HOME}/bin
mvn clean install
./appBuilder.sh
mv ../data/* ${SILVERPEAS_DATA}/
rm -rf ../data
popd
if [ ! -e "log" ]; then
	mkdir log
fi
mv ${SILVERPEAS_HOME}/log/* log/
pushd ${SILVERPEAS_HOME}
sed -e "s/kmelia\.export\.formats\.active.*/kmelia.export.formats.active = zip pdf odt doc/g" properties/org/silverpeas/kmelia/settings/kmeliaSettings.properties > /tmp/kmeliaSettings.properties
mv /tmp/kmeliaSettings.properties properties/org/silverpeas/kmelia/settings/kmeliaSettings.properties
popd

# lintian overrides
# mkdir -p tmp/usr/share/lintian/overrides/
# cp -T debian/silverpeas.lintian-overrides tmp/usr/share/lintian/overrides/silverpeas

# license
cp debian/copyright ${SILVERPEAS_DOC}/

# conffiles
cp -T ${SILVERPEAS_PKG}/conffiles ${ROOT}/DEBIAN/conffiles

# configuration
cp ../files/config.properties ${SILVERPEAS_HOME}/setup/settings/config-silverpeas.properties
res=0
grep "app=silverpeas" ${SILVERPEAS_HOME}/bin/silverpeas_start_jboss.sh >& /dev/null || res=1
if [ $res -ne 0 ]; then
  sed 's/#export JBOSS_CLASSPATH/export JAVA_OPTS="-Dapp=silverpeas $JAVA_OPTS"/' ${SILVERPEAS_HOME}/bin/silverpeas_start_jboss.sh > silverpeas_start_jboss.sh.new
  mv silverpeas_start_jboss.sh.new ${SILVERPEAS_HOME}/bin/silverpeas_start_jboss.sh
  sed 's/#export JBOSS_CLASSPATH/export JAVA_OPTS="-Dapp=silverpeas $JAVA_OPTS"/' ${SILVERPEAS_HOME}/bin/silverpeas_debug_jboss.sh > silverpeas_debug_jboss.sh.new
  mv silverpeas_debug_jboss.sh.new ${SILVERPEAS_HOME}/bin/silverpeas_debug_jboss.sh
fi

# set java path
for i in ${SILVERPEAS_HOME}/bin/*.sh; do
  sed "s/\$JAVA_HOME/\/usr/g" $i > $i.new
  mv $i.new $i
  chmod +x $i
done

# init.d
mkdir -p ${ROOT}/etc/init.d/
cp -T ${SILVERPEAS_PKG}/silverpeas.init ${ROOT}/etc/init.d/silverpeas
chmod 755 ${ROOT}/etc/init.d/silverpeas
cp -T ${SILVERPEAS_PKG}/openoffice.init ${ROOT}/etc/init.d/openoffice
chmod 755 ${ROOT}/etc/init.d/openoffice

#environment
mkdir -p ${ROOT}/etc/profile.d/
cp -T ../files/silverpeas.sh ${ROOT}/etc/profile.d/silverpeas.sh
cp -T ../files/jboss.sh ${ROOT}/etc/profile.d/jboss.sh

# preinst, postinst, prerm and postrm
cp -T ${SILVERPEAS_PKG}/silverpeas.preinst ${ROOT}/DEBIAN/preinst
chmod 755 ${ROOT}/DEBIAN/preinst
cp -T ${SILVERPEAS_PKG}/silverpeas.postinst ${ROOT}/DEBIAN/postinst
chmod 755 ${ROOT}/DEBIAN/postinst
cp -T ${SILVERPEAS_PKG}/silverpeas.prerm ${ROOT}/DEBIAN/prerm
chmod 755 ${ROOT}/DEBIAN/prerm
cp -T ${SILVERPEAS_PKG}/silverpeas.postrm ${ROOT}/DEBIAN/postrm
chmod 755 ${ROOT}/DEBIAN/postrm

cp -f ${SILVERPEAS_PKG}/control debian/control
dpkg-gencontrol -v"${VER}-${PKG_VER}" -c${SILVERPEAS_PKG}/control -Ptmp
rm -f debian/control

fakeroot dpkg-deb -b ${ROOT} silverpeas_${VER}-${PKG_VER}_all.deb

