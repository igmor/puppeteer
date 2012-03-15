#!/usr/bin/python
 
import paramiko
import cmd
import sys, errno, optparse, os
import shlex
import fileinput
import socket
from threading import Thread

ON_POSIX = 'posix' in sys.builtin_module_names

g_hosts = []

def enqueue_output(out, host, cmd):
    for line in iter(out.readline, ''):
        sys.stdout.write(host)
        sys.stdout.write(line)
    cmd.onecmd('')
        
class RunCommand(cmd.Cmd):
    """ Simple shell to run a command on the host """
 
    prompt = 'ssh > '
 
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.hosts = g_hosts
        self.connections = []

    def emptyline(self):        
        """Leaving it unimplemented """
        
    def do_add_host(self, args):
        """add_host <host,user,password>
        Add the host to the host list"""
        if args:
            self.hosts.append(args.split(','))
        else:
            print "usage: host <hostip,user,password>"
 
    def do_connect(self, args):
        """Connect to all hosts in the hosts list"""
        for host in self.hosts:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())
            iphost = socket.gethostbyname(host[0])            
            client.connect(iphost, 
                username=host[1], 
                password=host[2])
            self.connections.append(client)
 
    def do_run(self, command):
        """run <command>
        Execute this command on all hosts in the list"""
        if command:
            for host, conn in zip(self.hosts, self.connections):
                stdin, stdout, stderr = conn.exec_command(command,bufsize=1)
                stdin.close()
                t = Thread(target=enqueue_output, args=(stdout, host[0] + ': ', self))
                t.daemon = True # thread dies with the program
                t.start()
        else:
            print "usage: run <command>"

    def do_deep_copy(self, host, sftpcli, src, dst):
        """Does a deep copy of src directory to a remote location"""        
        try:
            attr = sftpcli.listdir_attr(dst)        
        except IOError, e:
            if e.errno == errno.ENOENT:
                sftpcli.mkdir(dst)
        for l in os.listdir(src):
            if os.path.isdir(src + os.sep + l) == True:
                try:
                    attr = sftpcli.listdir_attr(dst + os.sep + l)        
                except IOError, e:
                    if e.errno == errno.ENOENT:
                        sftpcli.mkdir(dst + os.sep + l)
                print "copying to " host + ': ' + + dst + os.sep + l
                self.do_deep_copy(host, sftpcli, src + os.sep + l, dst + os.sep + l)
            else:
                print "copying to " + host + ': ' + dst + os.sep + l
                sftpcli.put(src + os.sep + l, dst + os.sep + l)
                
    def do_deploy(self, args):
        """Deploys files and directories in args to all hosts in the hosts list"""
        for host in self.hosts:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())
            client.connect(host[0], 
                username=host[1], 
                password=host[2])
            ftp = client.open_sftp()
            for d in args.split():
                print 'copying %s' % d
                self.do_deep_copy(host[0], ftp, "." + os.sep + os.path.normpath(d), "." + os.sep + os.path.normpath(d))
            ftp.close()

    def do_close(self, args):
        for conn in self.connections:
            conn.close()

    def do_clear(self, args):
        self.hosts[:] = []
        
    def do_list(self, args):
        for host in self.hosts:
            print host[0], host[1], host[2]
                        
    def do_quit(self, args):
        sys.exit()

def parse_list_line(line):
    splitter = shlex.shlex(line, posix=True)
    splitter.whitespace += ','
    splitter.whitespace_split = True
    return list(splitter)

['foo', 'bar', 'one, two', 'three', 'four']    
if __name__ == '__main__':
    p = optparse.OptionParser(description='SSH based remote controller',
                              prog='console.py',
                              version='SSH RCtrl',
                              usage='%prog [-l file_name, where each entry has a format host,uname,passwd]')
    p.add_option('-l', '--list', dest='list', help='list of hostnames with unames/passwds')
    options, arguments = p.parse_args()

    if options.list:
        for line in fileinput.input(options.list):
            if len(line) == 0:
                pass
            else:
                host = parse_list_line(line)
                if len(host) == 3: #simple check for a number of required params
                    g_hosts.append(parse_list_line(line))
        
    RunCommand().cmdloop()
    
