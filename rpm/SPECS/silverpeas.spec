# Don't try fancy stuff like debuginfo, which is useless on binary-only
# packages. Don't strip binary too
# Be sure buildpolicy set to do nothing
%define		__spec_install_post %{nil}
%define		debug_package %{nil}
%define		__os_install_post %{_dbpath}/brp-compress

Name:		silverpeas
Version:	%{ver}
Release:	%{rel}
Summary:	Open platform to create a collaborative web site
Vendor:		Silverpeas
Packager:	Silverpeas Development Team <silverpeas-dev@googlegroups.com>
Group:		Development/Tools
License:	AGPLv3
URL:		http://www.silverpeas.org/
Source:		silverpeas-%{ver}-jboss6.tar.gz
Source1:	jboss-as-distribution-6.1.0.Final.zip
Source2:	silverpeas.init
Source3:	openoffice.init
Source4:	silverpeas.sh
Source5:	jboss.sh
Source6:	config.properties
Provides: silverpeas

Requires:	silverpeas-datasource
Requires: %{openoffice}
Requires: ImageMagick
Requires: ghostscript
Requires: swftools >= 0.9.1

Requires(pre): %{_sbindir}/useradd
Requires(post): %{_bindir}/sudo

#BuildRequires: java >= 1.6.0, java < 1.7.0 => on debian machine this build requirement isn't relevent
BuildArch:	noarch
Autoreq:	0
Autoprov:	0

%description
Silverpeas is an open source web portal providing useful tools and
applications to facilitate the collaboration between teams and
individuals within an organization.
It features document management, collaborative management, knowledge
management, content management, connectors to data sources, and a
transversal social network.

# macro to stop and unregister the services, and to remove the silverpeas deployment
# directory
%define teardown ( \
  /sbin/service openoffice stop > /dev/null 2>&1 \
  /sbin/service silverpeas stop > /dev/null 2>&1 \
  /sbin/chkconfig --list silverpeas &> /dev/null \
  test $? -eq 0 && /sbin/chkconfig --del silverpeas \
  /sbin/chkconfig --list openoffice &> /dev/null \
  test $? -eq 0 && /sbin/chkconfig --del openoffice \
  echo "Remove any previous silverpeas components..." \
  rm -rf /opt/silverpeas/jboss-6.1.0.Final/server/default/lib/* > /dev/null 2>&1 \
  rm -rf /opt/silverpeas/jboss-6.1.0.Final/server/default/deploy/silverpeas > /dev/null 2>&1)

%prep
cp %{_sourcedir}/silverpeas-%{ver}-jboss6.tar.gz %{_builddir}/
tar zxvf silverpeas-%{ver}-jboss6.tar.gz
%setup -q -b 1 -n jboss-6.1.0.Final

%build

%install
[ "Z$JAVA_HOME" = "Z" ] && export JAVA_HOME=/usr/lib/jvm/java-1.6.0
export SILVERPEAS_HOME=%{buildroot}/opt/silverpeas
export JBOSS_HOME=${SILVERPEAS_HOME}/jboss-6.1.0.Final
SILVERPEAS_DATA=%{buildroot}/var/data/silverpeas
SILVERPEAS_DOC=%{buildroot}/usr/share/doc/silverpeas

rm -rf %{buildroot}
mkdir -p %{buildroot}/opt
mkdir -p ${SILVERPEAS_DATA}/import

mv %{_builddir}/silverpeas-*-jboss6 ${SILVERPEAS_HOME}
cp -r %{_builddir}/jboss-6.1.0.Final ${SILVERPEAS_HOME}/
cd ${SILVERPEAS_HOME}/jboss-6.1.0.Final/server
rm -rf all jbossweb-standalone minimal standard

for script in `ls %{_sourcedir}/scripts`; do
  %{_sourcedir}/scripts/${script}
done

# Fix EOL in configuration files
for i in ${SILVERPEAS_HOME}/bin/*.sh; do
  echo "dos2unix $i"
  awk '{ sub("\r$", ""); print }' $i > $i.new
  mv $i.new $i
  chmod +x $i
done

cd ${SILVERPEAS_HOME}/bin
mvn clean install
./appBuilder.sh
mv ../data/* ${SILVERPEAS_DATA}/
rm -rf ../data

sed -e "s/kmelia\.export\.formats\.active.*/kmelia.export.formats.active = zip pdf odt doc/g" ${SILVERPEAS_HOME}/properties/org/silverpeas/kmelia/settings/kmeliaSettings.properties > /tmp/kmeliaSettings.properties
mv /tmp/kmeliaSettings.properties ${SILVERPEAS_HOME}/properties/org/silverpeas/kmelia/settings/kmeliaSettings.properties

for i in ${SILVERPEAS_HOME}/bin/*.sh; do
  sed "s/\$JAVA_HOME/\/usr/g" $i > $i.new
  mv $i.new $i
  chmod +x $i
done

%__install -D -m0755 "%{SOURCE2}" "%{buildroot}/etc/init.d/%{name}"
%__install -D -m0755 "%{SOURCE3}" "%{buildroot}/etc/init.d/openoffice"
%__install -D -m0644 "%{SOURCE4}" "%{buildroot}/etc/profile.d/silverpeas.sh"
%__install -D -m0644 "%{SOURCE5}" "%{buildroot}/etc/profile.d/jboss.sh"
%__install -D -m0644 "%{SOURCE6}" "%{buildroot}/opt/silverpeas/setup/settings/config-silverpeas.properties"

%pre
java -version &> /tmp/java-version 
grep 1.6.0 /tmp/java-version > /dev/null
if [ $? -ne 0 ]; then
  echo
  echo "Java 1.6.0 not installed. Silverpeas requires it. Stop the installation"
  echo
  exit 1
fi
if [ $1 -eq 1 ]; then
  # this is a first installation as opposed to upgrade: create the user silverpeas
  test `id silverpeas > /dev/null 2>&1` || /usr/sbin/useradd -s /bin/bash -r -d "/opt/silverpeas" silverpeas &>/dev/null || :
elif [ $1 -eq 2 ]; then
  # this is an upgrade: remove the services of the previous installation
  %teardown
  rm -rf /opt/silverpeas/jar
fi
exit 0

%post
if [ $1 -eq 1 ] ; then
  # this is a first installation as opposed to upgrade 
  if [ ! -e /opt/silverpeas/setup/settings/config.properties ]; then
    cp /opt/silverpeas/setup/settings/config-silverpeas.properties /opt/silverpeas/setup/settings/config.properties
    if [ -e /opt/silverpeas/setup/settings/config-datasource.properties ]; then
      cat /opt/silverpeas/setup/settings/config-datasource.properties >> /opt/silverpeas/setup/settings/config.properties
      rm /opt/silverpeas/setup/settings/config-datasource.properties
    fi
  fi
  rm /opt/silverpeas/setup/settings/config-silverpeas.properties 2>/dev/null
  chown silverpeas:silverpeas /opt/silverpeas/setup/settings/config.properties
fi
. /etc/profile.d/jboss.sh
. /etc/profile.d/silverpeas.sh
chmod +x /opt/silverpeas/bin/SilverpeasSettings.sh
chmod +x /opt/silverpeas/bin/dbBuilder.sh
su silverpeas -c "/opt/silverpeas/bin/SilverpeasSettings.sh"
test $? -eq 0 && su silverpeas -c "/opt/silverpeas/bin/dbBuilder.sh"
chmod +x /opt/silverpeas/bin/*.sh

chkconfig --add silverpeas
chkconfig --add openoffice
/sbin/service openoffice start
exit 0

%preun
if [ $1 -eq 0 ]; then
  # this is an uninstallation as opposed to upgrade: remove the services
  %teardown
fi
exit 0

%postun
if [ $1 -eq 0 ] ; then
  # if this is uninstallation as opposed to upgrade, drop the user silverpeas, the database
  # and remove some silverpeas directories
  echo "Remove the user silverpeas from this host"
  userdel -f silverpeas || true
  rm -rf /opt/silverpeas/setup/settings/config.properties
  rm -rf /opt/silverpeas/dbRepository
  rm -rf /opt/silverpeas/log/*
  rm -rf /opt/silverpeas/jboss-6.1.0.Final/server/default/log/*
  test -f /opt/silverpeas/jboss-6.1.0.Final/server/default/deploy/jms-ra.rar && rm -rf /opt/silverpeas/jboss-6.1.0.Final/server/default/deploy/jms-ra.rar > /dev/null 2>&1
  test -d /opt/silverpeas/data || rm -rf /opt/silverpeas
fi
exit 0

%clean
rm -rf %{buildroot}

%files
%defattr(0644,silverpeas,silverpeas,0755)
/opt/silverpeas
/var/data/silverpeas
%attr(0755,root,root) %config /etc/init.d/silverpeas
%attr(0755,root,root) %config /etc/init.d/openoffice
%attr(0644,root,root) %config /etc/profile.d/silverpeas.sh
%attr(0644,root,root) %config /etc/profile.d/jboss.sh
