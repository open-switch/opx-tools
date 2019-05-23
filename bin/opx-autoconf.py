#! /usr/bin/python
import sys, shutil, atexit
import os
import time
import signal

PIDFILE = '/tmp/opx-autoconf.pidfile'
STDOUT = '/tmp/opx-autoconf.stdout'
STDERR = '/tmp/opx-autoconf.stderr'
AUTOCONF_FILE = '/etc/opx/opx-autoconf'

#******************************************************************************
def _terminate(msg):
    print(msg)
    runUninstall(False)
    sys.exit(1)

#******************************************************************************
def _spCommand(cmd, supressError=False):
    import subprocess as sp
    process = sp.Popen(cmd, shell = True, stdout = sp.PIPE, stderr = sp.PIPE)
    out, err = process.communicate()
    if supressError == False:
        if len(err):
            out += err
    return process.returncode, out

###############################################################################
def runSetup(verbose, install_file):
    qos_name = None
    files=os.listdir('/lib/systemd/system/')
    for file in  os.listdir('/lib/systemd/system/'):
        if 'qos-init' in file and file.endswith('service'):
            qos_name = file
            break
    if qos_name is None:
        _terminate('Failed to locate qos_init.service')
    service_file='''
[Unit]
Description=Auto Config Service
After=%s
DefaultDependencies=no

[Service]
Type=oneshot
EnvironmentFile=/etc/opx/opx-environment
ExecStart=/usr/bin/python /usr/bin/opx-autoconf.py
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
''' % (qos_name)
    file=open(os.path.join('/lib/systemd/system/opx-autoconf.service'), 'w')
    file.write(service_file)
    file.close()
    if os.path.exists('/usr/bin/opx-autoconf.py'):
        os.unlink('/usr/bin/opx-autoconf.py')
    shutil.copy(install_file, '/usr/bin/opx-autoconf.py')
    if verbose:
        print('Installed %s' % install_file)
    s,o = _spCommand(cmd='systemctl enable opx-autoconf.service')
    if s:
        _terminate('failed to enable service: %s' % o)
    s,o = _spCommand(cmd='systemctl start opx-autoconf.service')
    if s:
        _terminate('failed to start service: %s' % o)
    elif verbose:
        print('Service Installed/Started OK: %s' % o)


###############################################################################
def runUninstall(verbose):
    if os.path.exists('/lib/systemd/system/opx-autoconf.service'):
        _spCommand(cmd='systemctl stop opx-autoconf.service')
        _spCommand(cmd='systemctl disable opx-autoconf.service')
        os.unlink('/lib/systemd/system/opx-autoconf.service')
        _spCommand(cmd='systemctl daemon-reload')
        if verbose:
            print('Service Uninstalled')
    else:
        print('Service not installed')
    if os.path.exists('/usr/bin/opx-autoconf.py'):
        os.unlink('/usr/bin/opx-autoconf.py')

###############################################################################
def runScripts(script=AUTOCONF_FILE, verbose=False):
    if os.path.exists(script):
        data = open(script, 'r').read()
        for cmd in data.splitlines():
            if not cmd.lstrip().startswith('#'):
                s,o = _spCommand(cmd)
                if s:
                    print('ERROR: cmd=%s, out:%s' % (cmd, o))
        print 'AutoConf: Completed'
    else:
        open(AUTOCONF_FILE, 'w').close()
        print 'AutoConf: Nothing to do'

###############################################################################
def insCommand(cmd, script):
    if cmd.startswith('#'):
        s=0
        o='comment inserted.'
    else:
        s,o = _spCommand(cmd)
    if s:
        print('ERROR: cmd=%s, out:%s' % (cmd, o))
    else:
        file=open(AUTOCONF_FILE, 'a+')
        file.write(cmd+'\n')
        print('CMD:%s [OK]\nOUT:%s' % (cmd, o))
        file.close()

###############################################################################
def rmCommand(cmd, script):
    data = None
    if os.path.exists(script):
        file = open(script, 'r')
        data = file.read()
        file.close()
    if data and cmd in data:
        file=open(AUTOCONF_FILE, 'w')
        data = data.replace(cmd,'')
        file.write(data)
        file.close()
        print('Command %s was removed.' % (cmd))
    else:
        print('Command does not exist!')

def runClear():
    open(AUTOCONF_FILE, 'w').close()


###############################################################################
###############################################################################
if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser(usage="%prog [options]\nAuto Config tool\n")

#   parser.add_option('--setup', dest='setup', default=False, action ='store_true', help='Setup tool as a service')
#   parser.add_option('--uninstall', dest='uninstall', default=False, action ='store_true', help='Uninstall tool')
    parser.add_option('--clear', dest='clear', default=False, action ='store_true', help='Clear start-up configuration')
    parser.add_option('--script', dest='script', default=AUTOCONF_FILE, action ='store', help='script file. default: %default')
    parser.add_option('-i', dest='ins', default=None, action ='store', help='Execute command and store')
    parser.add_option('-r', dest='rem', default=None, action ='store', help='Remove a command')
    parser.add_option('--verbose', dest='verbose', default=False, action ='store_true', help='Verbose mode.')

    (opts, args) = parser.parse_args()

    try:
        shutil.copy('/etc/hosts', '/etc/hosts1')
        os.unlink('/etc/hosts1')
    except:
       print ("You must have root permissions, please use sudo!")
       sys.exit(1)

#    if opts.setup and opts.uninstall:
#        print('Conflicting options specified')
#        sys.exit(1)
#    if opts.setup:
#        runSetup(opts.verbose, install_file=os.path.join(os.getcwd(),os.path.basename(sys.argv[0])))
#    elif opts.uninstall:
#        runUninstall(opts.verbose)
    if opts.clear:
        runClear()
    elif opts.ins is not None:
        insCommand(opts.ins, opts.script)
    elif opts.rem is not None:
        rmCommand(opts.rem, opts.script)
    else:
        runScripts(opts.script, opts.verbose)
    sys.exit(0)
