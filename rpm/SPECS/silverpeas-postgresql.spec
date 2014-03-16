# Don't try fancy stuff like debuginfo, which is useless on binary-only
# packages. Don't strip binary too
# Be sure buildpolicy set to do nothing
%define		__spec_install_post %{nil}
%define		debug_package %{nil}
%define		__os_install_post %{_dbpath}/brp-compress

Name:		silverpeas-postgresql-%{branch}
Version:	%{ver}
Release:	%{rel}
Summary:	Open platform to create a collaborative web site
Vendor:		Silverpeas
Packager:	Silverpeas Development Team <silverpeas-dev@googlegroups.com>
Group:		Applications/Internet
License:	AGPLv3
URL:		http://www.silverpeas.org/
Source:	config-postgresql.properties
Provides: silverpeas-datasource

Requires:	postgresql >= 8.2
Requires:	postgresql-server >= 8.2
Requires(post): %{_bindir}/sudo

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
.
This package provides the configuration for Silverpeas to use the RDBMS
PostgreSQL as datasource to store its data.

%prep

%build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/opt/silverpeas/setup/settings

%__install -D -m0644 %{SOURCE0} "%{buildroot}/opt/silverpeas/setup/settings/config-datasource.properties"

%pre
chkconfig --list | grep silverpeas >& /dev/null
if [ $? -eq 0 ]; then
  /sbin/service silverpeas status > /dev/null 2>&1
  test $? -eq 0 && /sbin/service silverpeas stop
fi
if [ $1 -eq 1 ]; then
  # this is a first installation as opposed to upgrade: create the user silverpeas and setup postgresql if not already done
  test `id silverpeas > /dev/null 2>&1` || /usr/sbin/useradd -s /bin/bash -r -d "/opt/silverpeas" silverpeas &>/dev/null || :

  # check maximum shared memory for PostgreSQL
  shmmax=`cat /proc/sys/kernel/shmmax`
  if [ $shmmax -lt 134217728 ]; then
    grep kernel.shmmax /etc/sysctl.conf > /dev/null 2>&1
    if [ $? -eq 0 ]; then
      sed 's/kernel.shmmax.*/kernel.shmmax = 134217728/g' /etc/sysctl.conf > /etc/sysctl.conf.new
      cp /etc/sysctl.conf /etc/sysctl.conf.prev
      mv /etc/sysctl.conf.new /etc/sysctl.conf
    else
      echo 'kernel.shmmax = 134217728' >> /etc/sysctl.conf
    fi
    /sbin/sysctl -p /etc/sysctl.conf
  fi

  # init postgresql if not yet 
  hba_path=/var/lib/pgsql/data/pg_hba.conf
  test -f $hba_path || /sbin/service postgresql initdb

  # add postgresql as a service to run at boot time if not yet and start it
  chkconfig --list | grep postgresql >& /dev/null
  test $? -eq 0 || chkconfig --add postgresql
  LANG=C chkconfig --list | grep postgresql | grep on >& /dev/null
  test $? -eq 0 || chkconfig postgresql on

  /sbin/service postgresql restart > /dev/null 2>&1
fi

exit 0

%post
if [ $1 -eq 1 ] ; then
  # this is a first installation as opposed to upgrade

  hba_path=/var/lib/pgsql/data/pg_hba.conf
  restart=0
  grep "^host[ \t]*all[ \t]*all[ \t]*127.0.0.1/32[ \t]*[(ident)(trust)]*" $hba_path > /dev/null
  if [ $? -eq 0 ]; then
    # remove the permission for all with an ident or a trust credential
    echo "PostgreSQL securing..."
    cp $hba_path $hba_path.save
    sed "s/^host[ \t]*all[ \t]*all[ \t]*[(127.0.0.1\/32)(::1\/128)]*[ \t]*[(ident)(trust)]*//" $hba_path > /tmp/pg_hba.conf
    sudo -E -u postgres cp /tmp/pg_hba.conf /var/lib/pgsql/data/
    rm -f /tmp/pg_hba.conf >& /dev/null || true
    chown postgres:postgres $hba_path
    restart=1
  fi
  
  grep "silverpeas" $hba_path > /dev/null
  if [ $? -ne 0 ]; then
    # add connection permission for the user silverpeas
    echo "Silverpeas user adding for PostgreSQL..."
    cat >> $hba_path << EOF
host    silverpeas             silverpeas             127.0.0.1/32            md5
host    silverpeas             silverpeas             ::1/128                 md5
EOF
    chown postgres:postgres $hba_path
    restart=1
  fi

  # restart PostgreSQL in order to apply the changes in the pg_hba.conf configuration file
  test $restart -eq 1 && /sbin/service postgresql restart

  # update the database connection properties for Silverpeas
  sudo -E -u postgres psql -c 'select * from pg_user' | grep silverpeas > /dev/null
  if [ $? -ne 0 ]; then
    echo "Database and user creation for Silverpeas..."
    SILVER_PWD=`echo $RANDOM | sha1sum | sed "s| -||g" | tr -d " "`
    echo "CREATE USER silverpeas WITH PASSWORD :silver_pwd; CREATE DATABASE silverpeas; GRANT ALL PRIVILEGES ON DATABASE silverpeas TO silverpeas;"  | sudo -E -u postgres psql -l -v silver_pwd="'$SILVER_PWD'" -f - 
    if [ -f /opt/silverpeas/setup/settings/config.properties ]; then
      sed "s/^DB_SERVERTYPE=.*/DB_SERVERTYPE=POSTGRES/g" /opt/silverpeas/setup/settings/config.properties > /tmp/config.properties && mv /tmp/config.properties /opt/silverpeas/setup/settings/config.properties
      sed "s/^DB_SERVER=.*/DB_SERVER=localhost/g" /opt/silverpeas/setup/settings/config.properties > /tmp/config.properties && mv /tmp/config.properties /opt/silverpeas/setup/settings/config.properties
      sed "s/^DB_NAME=.*/DB_NAME=silverpeas/g" /opt/silverpeas/setup/settings/config.properties > /tmp/config.properties && mv /tmp/config.properties /opt/silverpeas/setup/settings/config.properties
      sed "s/^DB_USER=.*/DB_USER=silverpeas/g" /opt/silverpeas/setup/settings/config.properties > /tmp/config.properties && mv /tmp/config.properties /opt/silverpeas/setup/settings/config.properties
      sed "s/^DB_PASSWD=.*/DB_PASSWD=$SILVER_PWD/g" /opt/silverpeas/setup/settings/config.properties > /tmp/config.properties && mv /tmp/config.properties /opt/silverpeas/setup/settings/config.properties
      chown silverpeas:silverpeas /opt/silverpeas/setup/settings/config.properties
      rm /opt/silverpeas/setup/settings/config-datasource.properties
    else
      sed "s/^DB_PASSWD=.*/DB_PASSWD=$SILVER_PWD/g" /opt/silverpeas/setup/settings/config-datasource.properties > /tmp/config-datasource.properties && mv /tmp/config-datasource.properties /opt/silverpeas/setup/settings/config-datasource.properties
    fi
  fi
fi
exit 0

%preun
if [ $1 -eq 0 ]; then
  # this is an uninstallation as opposed to upgrade
  /sbin/service silverpeas status > /dev/null 2>&1
  test $? -eq 0 && /sbin/service silverpeas stop
fi
exit 0

%postun
if [ $1 -eq 0 ] ; then
  # if this is uninstallation as opposed to upgrade
  hba_path=/var/lib/pgsql/data/pg_hba.conf
  if [ -f $hba_path ]; then
    echo "Database and user removing for Silverpeas..."
    /sbin/service postgresql status > /dev/null 2>&1
    test $? -eq 0 || /sbin/service postgresql start
    echo "DROP DATABASE silverpeas; DROP USER silverpeas" | sudo -E -u postgres psql -l -f -
    sed "s/^host[ \t]*silverpeas[ \t]*silverpeas[ \t]*[(127.0.0.1\/32)(::1\/128)]*[ \t]*md5//" $hba_path > /tmp/pg_hba.conf
    sudo -E -u postgres cp /tmp/pg_hba.conf $hba_path
    rm -f /tmp/pg_hba.conf > /dev/null 2>&1 || true
    /sbin/service postgresql restart
  fi
  if [ -f /opt/silverpeas/setup/settings/config.properties ]; then
    sed "s/^DB_SERVERTYPE=.*/DB_SERVERTYPE=/g" /opt/silverpeas/setup/settings/config.properties > /tmp/config.properties && mv /tmp/config.properties /opt/silverpeas/setup/settings/config.properties
    sed "s/^DB_SERVER=.*/DB_SERVER=/g" /opt/silverpeas/setup/settings/config.properties > /tmp/config.properties && mv /tmp/config.properties /opt/silverpeas/setup/settings/config.properties
    sed "s/^DB_NAME=.*/DB_NAME=/g" /opt/silverpeas/setup/settings/config.properties > /tmp/config.properties && mv /tmp/config.properties /opt/silverpeas/setup/settings/config.properties
    sed "s/^DB_USER=.*/DB_USER=/g" /opt/silverpeas/setup/settings/config.properties > /tmp/config.properties && mv /tmp/config.properties /opt/silverpeas/setup/settings/config.properties
    sed "s/^DB_PASSWD=.*/DB_PASSWD=/g" /opt/silverpeas/setup/settings/config.properties > /tmp/config.properties && mv /tmp/config.properties /opt/silverpeas/setup/settings/config.properties
  fi
fi
exit 0

%clean
rm -rf %{buildroot}

%files
/opt/silverpeas
