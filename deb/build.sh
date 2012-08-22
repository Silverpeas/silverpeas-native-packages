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
ROOT=`pwd`/tmp
SILVERPEAS_HOME=${ROOT}/opt/silverpeas
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

echo "silverpeas (${VER}) unstable; urgency=low

  * See http://www.silverpeas.org/docs/core/installation.html for more details.

 -- Silverpeas Development Team <silverpeas-dev@googlegroups.com>  ${DATE}
" > debian/changelog

# prepare silverpeas
tar xzf ../files/silverpeas-${VER}-jboss6.tar.gz
mv silverpeas-${VER}-jboss6 ${SILVERPEAS_HOME}

# prepare jboss
unzip ../files/jboss-as-distribution-6.1.0.Final.zip -d ${SILVERPEAS_HOME}/

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
cp -Rf ../data/* ${SILVERPEAS_DATA}/
popd
if [ ! -e "log" ]; then
	mkdir log
fi
mv ${SILVERPEAS_HOME}/log/* log/

# lintian overrides
# mkdir -p tmp/usr/share/lintian/overrides/
# cp -T debian/silverpeas.lintian-overrides tmp/usr/share/lintian/overrides/silverpeas

# license
cp debian/copyright ${SILVERPEAS_DOC}/

# conffiles
cp -T debian/conffiles ${ROOT}/DEBIAN/conffiles

# configuration
cp ../files/config.properties ${SILVERPEAS_HOME}/setup/settings/defaultConfig.properties

# set java path
for i in ${SILVERPEAS_HOME}/bin/*.sh; do
  sed "s/\$JAVA_HOME/\/usr/g" $i > $i.new
  mv $i.new $i
  chmod +x $i
done

# init.d
mkdir -p ${ROOT}/etc/init.d/
cp -T debian/silverpeas.init ${ROOT}/etc/init.d/silverpeas
chmod 755 ${ROOT}/etc/init.d/silverpeas
cp -T debian/openoffice.init ${ROOT}/etc/init.d/openoffice
chmod 755 ${ROOT}/etc/init.d/openoffice

#environment
mkdir -p ${ROOT}/etc/profile.d/
cp -T ../files/silverpeas.sh ${ROOT}/etc/profile.d/silverpeas.sh
cp -T ../files/jboss.sh ${ROOT}/etc/profile.d/jboss.sh

# postinst, prerm and postrm
cp -T debian/silverpeas.postinst ${ROOT}/DEBIAN/postinst
chmod 755 ${ROOT}/DEBIAN/postinst
cp -T debian/silverpeas.prerm ${ROOT}/DEBIAN/prerm
chmod 755 ${ROOT}/DEBIAN/prerm
cp -T debian/silverpeas.postrm ${ROOT}/DEBIAN/postrm
chmod 755 ${ROOT}/DEBIAN/postrm

dpkg-gencontrol -Ptmp

fakeroot dpkg-deb -b ${ROOT} silverpeas.deb
