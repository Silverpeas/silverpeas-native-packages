# Don't try fancy stuff like debuginfo, which is useless on binary-only
# packages. Don't strip binary too
# Be sure buildpolicy set to do nothing
%define		__spec_install_post %{nil}
%define		debug_package %{nil}
%define		__os_install_post %{_dbpath}/brp-compress

Name:		silverpeas
Version:	%{ver}
Release:	1
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
#BuildRoot:	%{_root}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

#BuildRequires: /usr/bin/mvn

%if 0%{?suse_version}
Requires: java = 1.6.0
%if 0%{?suse_version} < 1140
Requires: openoffice.org
%else
Requires: libreoffice
%endif
%endif

%if 0%{?fedora} || 0%{?rhel_version} || 0%{?centos_version}
Requires: java = 1:1.6.0
%if 0%{?fedora} < 15 || 0%{?rhel_version} < 630 || 0%{?centos_version} < 630
Requires: openoffice.org
%else
Requires: libreoffice-headless
%endif
%endif

Requires:	postgresql-server

Requires(pre): %{_sbindir}/useradd
Requires(post): %{_bindir}/sudo

BuildArch:	noarch
Autoreq:	0
Autoprov:	0

%description
Silverpeas is an open source web portal providing useful tools and
applications to facilitate the collaboration between teams and
individuals within an organization.

# macro to stop and unregister the services, and to remove the silverpeas deployment
# directory
%define teardown ( \
  /sbin/service openoffice stop > /dev/null 2>&1 \
  if [ -e /var/run/silverpeas.pid ]; then \
    pid=`cat /var/run/silverpeas.pid` \
    if [ "Z$pid" != "Z" ]; then \
      pid1=`ps ax | grep -i jboss | tr -s ' ' | cut -d ' ' -f 1 | head -n 1` \
      test "Z$pid1" = "Z" && pid1=`ps ax | grep -i jboss | tr -s ' ' | cut -d ' ' -f 2 | head -n 1` \
      if [ $pid -eq $pid1 ]; then \
        echo "Waiting for Silverpeas shutdown..." \
        /sbin/service silverpeas stop > /dev/null 2>&1 \
      fi \
    fi \
  fi \
  /sbin/chkconfig --del silverpeas \
  /sbin/chkconfig --list openoffice &> /dev/null \
  test $? -eq 0 && /sbin/chkconfig --del openoffice \
  echo "Remove any previous silverpeas components..." \
  rm -rf /opt/silverpeas/jboss-6.1.0.Final/server/default/lib/* > /dev/null 2>&1 \
  rm -rf /opt/silverpeas/jboss-6.1.0.Final/server/default/deploy/silverpeas > /dev/null 2>&1)

%prep
%setup -q -n silverpeas-%{ver}-jboss6
%setup -q -b 1 -n jboss-6.1.0.Final

%build

%install
SILVERPEAS_HOME=%{buildroot}/opt/silverpeas
JBOSS_HOME=${SILVERPEAS_HOME}/jboss-6.1.0.Final
SILVERPEAS_DATA=%{buildroot}/var/data/silverpeas
SILVERPEAS_DOC=%{buildroot}/usr/share/doc/silverpeas

rm -rf %{buildroot}
mkdir -p %{buildroot}/opt
mkdir -p ${SILVERPEAS_DATA}/import

mv %{_builddir}/silverpeas-%{ver}-jboss6/ ${SILVERPEAS_HOME}
cp -r %{_builddir}/jboss-6.1.0.Final ${SILVERPEAS_HOME}/

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

for i in ${SILVERPEAS_HOME}/bin/*.sh; do
  sed "s/\$JAVA_HOME/\/usr/g" $i > $i.new
  mv $i.new $i
  chmod +x $i
done

%__install -D -m0755 "%{SOURCE2}" "%{buildroot}/etc/init.d/%{name}"
%__install -D -m0755 "%{SOURCE3}" "%{buildroot}/etc/init.d/openoffice"
%__install -D -m0644 "%{SOURCE4}" "%{buildroot}/etc/profile.d/silverpeas.sh"
%__install -D -m0644 "%{SOURCE5}" "%{buildroot}/etc/profile.d/jboss.sh"
%__install -D -m0644 "%{SOURCE6}" "${SILVERPEAS_HOME}/setup/settings/defaultConfig.properties"

%pre
if [ $1 -eq 1 ]; then
  # this is a first installation as opposed to upgrade: create the user silverpeas
  /usr/sbin/useradd -g adm -s /bin/sh -r -d "/opt/silverpeas" silverpeas &>/dev/null || :
elif [ $1 -eq 2 ]; then
  # this is an upgrade: remove the services of the previous installation
  %teardown
  rm -rf /opt/silverpeas/jar
fi

%post
if [ $1 -eq 1 ] ; then
  # this is a first installation as opposed to upgrade: create the database and generate the config.properties settings file
  SILVER_PWD=`echo $RANDOM | sha1sum | sed "s| -||g" | tr -d " "`
  echo "CREATE USER silverpeas WITH PASSWORD :silver_pwd; CREATE DATABASE silverpeas WITH ENCODING 'UTF-8'; GRANT ALL PRIVILEGES ON DATABASE silverpeas TO silverpeas;" | sudo -u postgres psql -l -v silver_pwd="'$SILVER_PWD'" -f -
  sed "s/@@silver_pwd@@/$SILVER_PWD/g" /opt/silverpeas/setup/settings/defaultConfig.properties > /opt/silverpeas/setup/settings/config.properties
  if [ -e /opt/silverpeas/setup/settings/config.properties ]; then
    echo "config.properties generated"
  else
    echo "Error while generating config.properties!"
    exit 1
  fi
  chown silverpeas:adm /opt/silverpeas/setup/settings/config.properties
fi

rm /opt/silverpeas/setup/settings/defaultConfig.properties
. /etc/profile.d/jboss.sh
. /etc/profile.d/silverpeas.sh
chmod +x /opt/silverpeas/bin/SilverpeasSettings.sh
chmod +x /opt/silverpeas/bin/dbBuilder.sh
su silverpeas -c "/opt/silverpeas/bin/SilverpeasSettings.sh"
test $? -eq 0 && su silverpeas -c "/opt/silverpeas/bin/dbBuilder.sh"
chmod +x /opt/silverpeas/bin/*.sh

rpm -q openoffice.org &> /dev/null
openoffice=$?
rpm -q libreoffice-headless &> /dev/null
libreoffice=$?
if [ $openoffice -eq 0 ] || [ $libreoffice -eq 0 ]; then
  /sbin/chkconfig --add openoffice
  /sbin/service openoffice start > /dev/null 2>&1
else
  echo
  echo "Silverpeas requires OpenOffice.org or LibreOffice service for some of its advanced export functionalities."
  echo "So, to use them, we suggest you to install either openoffice.org or libreoffice in headless mode and then run /sbin/chkconfig --add openoffice to register it as a daemon"
  echo
fi
/sbin/chkconfig --add silverpeas
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
  userdel -f silverpeas || true
  rm -rf /opt/silverpeas/setup/settings/config.properties
  rm -rf /opt/silverpeas/dbRepository
  rm -rf /opt/silverpeas/log/*
  rm -rf /opt/silverpeas/jboss-6.1.0.Final/server/default/log/*
  echo "DROP DATABASE silverpeas; DROP USER silverpeas" | sudo -u postgres psql -l -f -
fi
exit 0

%clean
rm -rf %{buildroot}

%files
%defattr(0644,silverpeas,adm,0755)
/opt/silverpeas
/var/data/silverpeas
%attr(0755,root,root) %config /etc/init.d/silverpeas
%attr(0755,root,root) %config /etc/init.d/openoffice
%attr(0644,root,root) %config /etc/profile.d/silverpeas.sh
%attr(0644,root,root) %config /etc/profile.d/jboss.sh
