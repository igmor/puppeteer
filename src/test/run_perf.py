#!/usr/bin/env python

import os,sys,re
import time
import optparse

#pattern = '.*{"lb":"(.*)","msid":(.*),"gid":"(.*)"}.*'

from threading import Thread
from subprocess import PIPE, Popen

ON_POSIX = 'posix' in sys.builtin_module_names
COMMAND='ls'

nviewers = 1

def enqueue_output(out, ip, port, publisher):
    for line in iter(out.readline, ''):
        sys.stdout.write(line)
	if publisher == True:
	    m = re.search(pattern,line);
	    if m != None and m.group(1) != None and m.group(2) != None and m.group(3) != None:
		print m.group(1), m.group(2), m.group(3)
		for i in xrange(1,nviewers+1):
		    run_viewer(ip, port, m.group(1), m.group(2), m.group(3), str(i))
	
    out.close()

def run_async(cmdline,ip, port, publisher):
	p = Popen(cmdline, stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
	    
        t = Thread(target=enqueue_output, args=(p.stdout,ip, port, publisher))
        t.daemon = True # thread dies with the program
        t.start()
	return p
    
def run_viewer(ip, port,lb, msid, gid, uid):
	if os.path.dirname(sys.argv[0]) != '':
		c_dir = os.path.dirname(sys.argv[0])
	else:
		c_dir = "."
		
        cmdline = [c_dir + COMMAND, '-al']	 

	run_async(cmdline, ip, port, False)
                
def run_publisher(ip, port):
	if os.path.dirname(sys.argv[0]) != '':
		c_dir = os.path.dirname(sys.argv[0])
	else:
		c_dir = "."

        cmdline = [c_dir + COMMAND, '-al']	                 
	p = run_async(cmdline, ip, port, True)

	p.wait()
	
def main(ip, port):
 	run_publisher(ip, port)
  
if __name__ == '__main__':
	p = optparse.OptionParser(description='Starts a pair of sessions to Server defined by IP Address',
				  prog='viwer_publisher',
				  version='VP Load Test 0.1',
				  usage='%prog [-a|--ip ip_address -p|--port port]')
	p.add_option('-a', '--ip', dest='ip', help='set server\'s IP address')
	p.add_option('-p', '--port', dest='port', help='set server\'s port')
	p.add_option('-n', '--nviewers', dest='nviewers', help='set number of clients per server')	

	options, arguments = p.parse_args()

	if not options.ip or not options.port:
		p.print_help()
		#		return False

		#main(options.ip, options.port)
	if options.nviewers:
		nviewers = int(options.nviewers)
	main(str(options.ip), str(options.port))		
