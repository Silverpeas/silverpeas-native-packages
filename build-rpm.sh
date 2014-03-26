#!/usr/bin/env bash

# Requires:
#   app-arch/createrepo
#   app-arch/rpm

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <root path> <version> [<package version>]"
  echo "If the package release isn't set, then it is set at 1 by default"
  exit 1
fi

VER=$1
PKG_VER=$2

buildrpm() {
  dist="$1"
  echo "======================================================================="
  echo "Build RPM package for $dist"
  case "$dist" in
    centos-5|rhel-5)
      repo="repo/rpm/rhel/5.x"
      ;;
    centos-6|rhel-6)
      repo="repo/rpm/rhel/6.x"
      ;;
    fedora)
      repo="repo/rpm/fedora/17"
      ;;
    *)
      echo "GNU/Linux distribution $dist not supported!"
      exit 1
  esac
  test -d $repo/noarch || mkdir -p $repo/noarch
  cat > $repo/silverpeas.repo << EOF
[silverpeas]
name=silverpeas
enabled=1
autorefresh=1
baseurl=http://www.silverpeas.org/$repo
gpgcheck=0
type=rpm-md
EOF

  rpm/build.sh $dist $VER $PKG_VER
  test $? -eq 0 || return 1

  cp -v rpm/RPMS/noarch/* $repo/noarch/
  createrepo $repo/
  test $? -eq 0 || return 1

  echo "RPM package build for $dist done"
  echo "======================================================================="

  return 0
}

echo "Building RPM packages for centos, RHEL, Fedora, and OpenSUSE"
if [ -e rpm/SOURCES ]; then
  rm -rf rpm/SOURCES || true
fi

mkdir rpm/SOURCES
cp -v files/* rpm/SOURCES/
cp -v rpm/*.init rpm/SOURCES/
cp -rv scripts rpm/SOURCES/

# for SNAPSHOT version, the packaging doesn't support the '-' character in the version
# so we replace it by the dot and change accordingly the silverpeas installer file name.
res=0
echo "$VER" | grep "\-SNAPSHOT" > /dev/null || res=1
if [ $res -eq 0 ]; then
  OLDVER="$VER"
  VER=${VER%-SNAPSHOT}.SNASPHOT
  mv rpm/SOURCES/silverpeas-${OLDVER}-jboss6.tar.gz rpm/SOURCES/silverpeas-${VER}-jboss6.tar.gz
fi

buildrpm "centos-5"
test $? -eq 0 && buildrpm "centos-6"
test $? -eq 0 && buildrpm "fedora"

