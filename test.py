import os, sys
import time
import shutil
from create import MySQLSandbox
from testconfig import config

from holland.cli.main import holland

def setup():
    sandboxroot = os.path.abspath(config['main']['sandbox-root'])
    for version in config['main']['mysql-versions'].split(','):
        version = version.strip()
        local_sandbox = os.path.join(sandboxroot, 'mysql_' + version)
        tarball = config['mysql ' + version]['tarball']
        sb = MySQLSandbox(local_sandbox)
        sb.setup(tarball)
        os.system(os.path.join(local_sandbox, 'start.sh'))
    os.environ['HOME'] = os.path.abspath('sandboxes/mysql_5.0/')
    os.environ['PATH'] = os.path.abspath('sandboxes/mysql_5.0/5.0.91/bin') + \
                         ':' + os.environ['PATH']

def teardown():
    sandboxroot = os.path.abspath(config['main']['sandbox-root'])
    for version in config['main']['mysql-versions'].split(','):
        version = version.strip()
        local_sandbox = os.path.join(sandboxroot, 'mysql_' + version)
        pid_file = os.path.join(local_sandbox, 'data', 'mysql.holland.pid')
        pid = open(pid_file).read().strip()
        os.unlink(pid_file)
        try:
            os.kill(int(pid), 9)
        except OSError:
            pass
        time.sleep(2.0)
        shutil.rmtree(local_sandbox)

def test_default_dryrun():
    holland(['--config', 'holland.conf.d/holland.conf',
             '--log-leve', 'debug',
             'backup', '--dry-run',
             os.path.abspath('holland.conf.d/default.conf')])

def test_default_backupset():
    holland(['--config', 'holland.conf.d/holland.conf',
             '--log-leve', 'debug',
             'backup',
             os.path.abspath('holland.conf.d/default.conf')])

def test_default_all_databases():
    holland(['--config', 'holland.conf.d/holland.conf',
             '--log-leve', 'debug',
             'backup',
             os.path.abspath('holland.conf.d/default_alldatabases.conf')])

def test_default_w_extra_defaults():
    holland(['--config', 'holland.conf.d/holland.conf',
             '--log-leve', 'debug',
             'backup',
             os.path.abspath('holland.conf.d/default_extradefaults.conf')])
