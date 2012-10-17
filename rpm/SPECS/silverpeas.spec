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

Requires:	postgresql >= 8.2
Requires:	postgresql-server >= 8.2
Requires: %{openoffice}

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
  if [ -e /var/run/silverpeas.pid ]; then \
    pid=`cat /var/run/silverpeas.pid` \
    if [ "Z$pid" != "Z" ]; then \
      pid1=`ps ax | grep -i jboss | tr -s ' ' | cut -d ' ' -f 1 | head -n 1` \
      test "Z$pid1" = "Z" && pid1=`ps ax | grep -i jboss | tr -s ' ' | cut -d ' ' -f 2 | head -n 1` \
      if [ $pid -eq $pid1 ]; then \
        echo "Waiting for Silverpeas shutdown..." \
        /sbin/service silverpeas stop \
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
cp %{_sourcedir}/silverpeas-%{ver}-jboss6.tar.gz %{_builddir}/
tar zxvf silverpeas-%{ver}-jboss6.tar.gz
%setup -q -b 1 -n jboss-6.1.0.Final

%build

%install
[ "Z$JAVA_HOME" = "Z" ] && export JAVA_HOME=/usr/lib/jvm/java-1.6.0
export SILVERPEAS_HOME=%{buildroot}/opt/silverpeas
JBOSS_HOME=${SILVERPEAS_HOME}/jboss-6.1.0.Final
SILVERPEAS_DATA=%{buildroot}/var/data/silverpeas
SILVERPEAS_DOC=%{buildroot}/usr/share/doc/silverpeas

rm -rf %{buildroot}
mkdir -p %{buildroot}/opt
mkdir -p ${SILVERPEAS_DATA}/import

mv %{_builddir}/silverpeas-*-jboss6 ${SILVERPEAS_HOME}
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

%post
if [ $1 -eq 1 ] ; then
  # this is a first installation as opposed to upgrade: create the database and generate the config.properties settings file

  # init postgresql if not yet and add the db user silverpeas
  test -f /var/lib/pgsql/data/pg_hba.conf || service postgresql initdb
  grep "^host[ \t]*all[ \t]*all[ \t]*127.0.0.1/32[ \t]*[(ident)(trust)]*" /var/lib/pgsql/data/pg_hba.conf > /dev/null
  if [ $? -eq 0 ]; then
    # remove the permission for all with an ident or a trust credential
    sed "s/^host[ \t]*all[ \t]*all[ \t]*[(127.0.0.1\/32)(::1\/128)]*[ \t]*[(ident)(trust)]*//" /var/lib/pgsql/data/pg_hba.conf > /tmp/pg_hba.conf
    sudo -u postgres cp /tmp/pg_hba.conf /var/lib/pgsql/data/
    rm -f /tmp/pg_hba.conf >& /dev/null || true
  fi
  # add connection permission for the user silverpeas
  echo "Add connection to the user silverpeas from this host"
  cat >> /var/lib/pgsql/data/pg_hba.conf << EOF
host    silverpeas             silverpeas             127.0.0.1/32            md5
host    silverpeas             silverpeas             ::1/128                 md5
EOF
  chown postgres:postgres /var/lib/pgsql/data/pg_hba.conf

  # add postgresql as a service to run at boot time if not yet and start it
  echo "If not yet, add postgreSQL as a service to run at boot time"
  chkconfig --list | grep postgresql >& /dev/null
  test $? -eq 0 || chkconfig --add postgresql
  LANG=C chkconfig --list | grep postgresql | grep on >& /dev/null
  test $? -eq 0 || chkconfig postgresql on
  service postgresql restart

  SILVER_PWD=`echo $RANDOM | sha1sum | sed "s| -||g" | tr -d " "`
  echo "CREATE USER silverpeas WITH PASSWORD :silver_pwd; CREATE DATABASE silverpeas WITH ENCODING 'UTF-8'; GRANT ALL PRIVILEGES ON DATABASE silverpeas TO silverpeas;" | sudo -u postgres psql -l -v silver_pwd="'$SILVER_PWD'" -f -
  sed "s/@@silver_pwd@@/$SILVER_PWD/g" /opt/silverpeas/setup/settings/defaultConfig.properties > /opt/silverpeas/setup/settings/config.properties
  if [ -e /opt/silverpeas/setup/settings/config.properties ]; then
    echo "config.properties generated"
  else
    echo "Error while generating config.properties!"
    exit 1
  fi
  chown silverpeas:silverpeas /opt/silverpeas/setup/settings/config.properties
fi

service postgresql status >& /dev/null
test $? -eq 0 || service postgresql start
rm /opt/silverpeas/setup/settings/defaultConfig.properties
. /etc/profile.d/jboss.sh
. /etc/profile.d/silverpeas.sh
chmod +x /opt/silverpeas/bin/SilverpeasSettings.sh
chmod +x /opt/silverpeas/bin/dbBuilder.sh
su silverpeas -c "/opt/silverpeas/bin/SilverpeasSettings.sh"
test $? -eq 0 && su silverpeas -c "/opt/silverpeas/bin/dbBuilder.sh"
chmod +x /opt/silverpeas/bin/*.sh

echo "Add OpenOffice.org/LibreOffice as a service to run at boot time and start it"
chkconfig --add openoffice
service openoffice start
echo "Add Silverpeas as a service to run at boot time"
chkconfig --add silverpeas
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
  echo "DROP DATABASE silverpeas; DROP USER silverpeas" | sudo -u postgres psql -l -f -
  if [ -f /var/lib/pgsql/data/pg_hba.conf ]; then
    sed "s/^host[ \t]*silverpeas[ \t]*silverpeas[ \t]*[(127.0.0.1\/32)(::1\/128)]*[ \t]*md5//" /var/lib/pgsql/data/pg_hba.conf > /tmp/pg_hba.conf
    sudo -u postgres cp /tmp/pg_hba.conf /var/lib/pgsql/data/
    rm -f /tmp/pg_hba.conf >& /dev/null || true
    service postgresql restart
  fi
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
