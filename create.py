"""
create.py
~~~~~~~~~

Create a sandbox

"""

import os
import pwd
import errno
import shutil
import subprocess

# basedir
# datadir
# pid_file
# socket
# tmpdir
# server_id

def create_sandbox(tarball, distdir, sandboxdir, mysql_port):
    """
    Given:
        1) a binary distribution tarball
        2) a place to extract said tarball
        3) a root directory setup a datadir in
        4) a mysql port #

    Do the following:
        1) extract ${tarball} to ${distdir}
        2) locate ${mysqld} under ${distdir}
        3) mkdir -p ${sandboxdir}/${data}
        4) copy ${script_template_dir}/*.sh to ${sandboxdir}
        4a) replace ${basedir} w/ ${distdir}
                    ${sandboxdir} w/ ${sandboxdir}
                    ${datadir} w/ ${sandboxdir}/data/
                    ${pid_file} w/ ${sandboxdir}/data/holland.pid
                    ${socket} w/ ${sandboxdir}/data/holland.sock
                    ${tmpdir} w/ ${sandboxdir}/tmp/
                    ${server_id} w/ ${mysql_port}
        5) copy conf.d/my.${version}.cnf to ${sandboxdir}/my.holland.cnf
        5a) Substitute same parameters as in sandbox scripts
        6) Run ${sandbox}/start.sh

    """

my_cnf_template = '''
[mysqld]
## General
basedir                         = ${basedir}
pid-file                        = ${pid_file}
datadir                         = ${datadir}
tmpdir                          = ${tmpdir}
socket                          = ${socket}
port                            = ${mysql_port}
skip-locking
skip-name-resolve

## Misc
default-storage-engine          = InnoDB
sql-mode                        = NO_ENGINE_SUBSTITUTION
open-files-limit                = 65535

## Cache
thread-cache-size               = 16
table-cache                     = 2048

## Networking
back-log                        = 100
max-connections                 = 200
max-connect-errors              = 10000
max-allowed-packet              = 16M
interactive-timeout             = 3600
wait-timeout                    = 600

## MyISAM
key-buffer-size                 = 128M
myisam-sort-buffer-size         = 512M

## InnoDB
innodb-log-file-size            = 128M
innodb-buffer-pool-size         = ${innodb_buffer_pool_size}
innodb-file-per-table           = 1
innodb-open-files               = 300

## Replication
server-id                       = ${mysql_port}
log-bin                         = holland-bin-log
relay-log                       = holland-relay-log
relay-log-space-limit           = 4G
#log-slave-updates
expire-logs-days                = 7

## Logging
log-slow-queries                = holland-slow-log
long-query-time                 = 2

[client]
user                            = root
password                        =
socket                          = ${socket}
'''

start_script_template = '''
#!/bin/bash

BASEDIR='${basedir}'
export LD_LIBRARY_PATH=$BASEDIR/lib:$BASEDIR/lib/mysql:$LD_LIBRARY_PATH
export DYLD_LIBRARY_PATH=$BASEDIR_/lib:$BASEDIR/lib/mysql:$DYLD_LIBRARY_PATH
MYSQLD_SAFE="$BASEDIR/bin/${mysqld_safe}"
SBDIR="${sandboxdir}"

PIDFILE="$SBDIR/data/mysql.holland.pid"

if [ ! -f $MYSQLD_SAFE ]
then
    echo "mysqld_safe not found in $BASEDIR/bin/"
    exit 1
fi

MYSQLD_SAFE_OK=`sh -n $MYSQLD_SAFE 2>&1`
if [ "$MYSQLD_SAFE_OK" == "" ]
then
    if [ "$SBDEBUG" == "2" ]
    then
        echo "$MYSQLD_SAFE OK"
    fi
else
    echo "$MYSQLD_SAFE has errors"
    echo "((( $MYSQLD_SAFE_OK )))"
    exit 1
fi
TIMEOUT=60
if [ -f $PIDFILE ]
then
    echo "sandbox server already started (found pid file $PIDFILE)"
else
    CURDIR=`pwd`
    cd $BASEDIR
    if [ "$SBDEBUG" = "" ]
    then
        $MYSQLD_SAFE --defaults-file=$SBDIR/my.holland.cnf $@ > /dev/null 2>&1 &
    else
        $MYSQLD_SAFE --defaults-file=$SBDIR/my.holland.cnf $@ > "$SBDIR/start.log" 2>&1 &
    fi
    cd $CURDIR
    ATTEMPTS=1
    while [ ! -f $PIDFILE ]
    do
        ATTEMPTS=$(( $ATTEMPTS + 1 ))
        echo -n "."
        if [ $ATTEMPTS = $TIMEOUT ]
        then
            break
        fi
        sleep 1
    done
fi

if [ -f $PIDFILE ]
then
    echo " sandbox server started"
else
    echo " sandbox server not started yet"
    exit 1
fi
'''
from string import Template

class MySQLSandbox(object):
    def __init__(self, sandboxdir):
        self.sandboxdir = os.path.abspath(sandboxdir)

    def setup(self, tarball):
        mysql_version = tarball.split('-')[1]
        basedir = os.path.join(self.sandboxdir, mysql_version)
        datadir = os.path.join(self.sandboxdir, 'data')
        pid_file = os.path.join(datadir, 'mysql.holland.pid')
        mysql_socket = os.path.join(datadir, 'sandbox.sock')
        tmpdir = os.path.join(self.sandboxdir, 'tmp')
        mysql_port = ''.join(mysql_version.split('.'))

        try:
            shutil.rmtree(self.sandboxdir)
        except OSError, exc:
            if exc.errno != errno.ENOENT:
                raise

        for path in [basedir, datadir, tmpdir]:
            try:
                os.makedirs(path)
            except OSError, exc:
                if exc.errno != errno.EEXIST:
                    raise

        subprocess.check_call([
            'tar',
            'xf',
            tarball,
            '-C', basedir,
            '--strip-components', '1',
            '--totals',
        ], close_fds=True)

        config = Template(my_cnf_template).safe_substitute(
            basedir=basedir,
            datadir=datadir,
            pid_file=pid_file,
            tmpdir=tmpdir,
            socket=mysql_socket,
            mysql_port=mysql_port,
            innodb_buffer_pool_size='128M'
        )

        script = Template(start_script_template).safe_substitute(
            sandboxdir=self.sandboxdir,
            mysqld_safe='mysqld_safe',
            basedir=basedir,
            datadir=datadir,
            pid_file=pid_file,
            tmpdir=tmpdir,
            socket=mysql_socket,
        )

        open(os.path.join(self.sandboxdir, 'my.holland.cnf'), 'w').write(config)
        open(os.path.join(self.sandboxdir, 'start.sh'), 'w').write(script)
        os.chmod(os.path.join(self.sandboxdir, 'start.sh'), 0770)

        subprocess.check_call([
            os.path.join(basedir, 'scripts', 'mysql_install_db'),
            '--no-defaults',
            '--user=' + pwd.getpwuid(os.getuid()).pw_name,
            '--basedir=' + basedir,
            '--datadir=' + datadir,
            '--skip-name-resolve',
        ], stdout=open('/dev/null', 'w'), close_fds=True)



if __name__ == '__main__':
    import shutil
    try:
        shutil.rmtree('sandboxes/msb_5_5_10')
    except:
        pass

    sb = MySQLSandbox('sandboxes/msb_5_5_10')
    sb.setup('mysql.archive/mysql-5.5.10-linux2.6-x86_64.tar.gz')
