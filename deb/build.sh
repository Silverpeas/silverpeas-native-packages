#!/bin/sh

# Requires:
#   app-arch/dpkg
#   sys-apps/fakeroot

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <version>"
  exit 1
fi

VER=$1

# prepare fresh directories
rm -rf tmp/
mkdir -p tmp/DEBIAN/
mkdir -p tmp/opt/
mkdir -p tmp/var/data/silverpeas/import/

# changelog
DATE=`date -R`

echo "silverpeas (${VER}) unstable; urgency=low

  * See http://www.silverpeas.org/docs/core/installation.html for more details.

 -- Silverpeas Development Team <silverpeas-dev@googlegroups.com>  ${DATE}
" > debian/changelog

# prepare silverpeas
tar xzf silverpeas-${VER}-jboss6.tar.gz
mv silverpeas-${VER}-jboss6/ tmp/opt/silverpeas

#prepare jboss
unzip jboss-as-distribution-6.1.0.Final.zip -d tmp/opt/silverpeas/

# Fix EOL in configuration files
for i in tmp/opt/silverpeas/bin/*.sh; do
  echo "dos2unix $i"
  awk '{ sub("\r$", ""); print }' $i > $i.new
  mv $i.new $i
  chmod +x $i
done

cd tmp/opt/silverpeas/
SILVERPEAS_HOME=`pwd`
cd bin
mvn clean install
./appBuilder.sh
cp -Rf ../data/* ../../../../../deb/tmp/var/data/silverpeas/
cd ../../../../../deb

# lintian overrides
# mkdir -p tmp/usr/share/lintian/overrides/
# cp -T debian/silverpeas.lintian-overrides tmp/usr/share/lintian/overrides/silverpeas

# license
mkdir -p tmp/usr/share/doc/silverpeas/
cp debian/copyright tmp/usr/share/doc/silverpeas/

# conffiles
cp -T debian/conffiles tmp/DEBIAN/conffiles

#configuration
cp debian/config.properties tmp/opt/silverpeas/setup/settings/defaultConfig.properties

# init.d
mkdir -p tmp/etc/init.d/
cp -T debian/silverpeas.init tmp/etc/init.d/silverpeas
chmod 755 tmp/etc/init.d/silverpeas

#environment
mkdir -p tmp/etc/profile.d/
cp -T debian/silverpeas.sh tmp/etc/profile.d/silverpeas.sh
cp -T debian/jboss.sh tmp/etc/profile.d/jboss.sh
chmod 755 tmp/etc/init.d/silverpeas

# postinst and postrm
cp -T debian/silverpeas.postinst tmp/DEBIAN/postinst
chmod 755 tmp/DEBIAN/postinst
cp -T debian/silverpeas.postrm tmp/DEBIAN/postrm
chmod 755 tmp/DEBIAN/postrm

dpkg-gencontrol -Ptmp

fakeroot dpkg-deb -b tmp silverpeas.deb
