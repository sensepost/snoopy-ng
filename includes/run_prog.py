from subprocess import Popen, call, PIPE
import errno
from types import *
import logging
import sys

def run_program(executable,executable_options=[]):
    """
    Runs a program 'executable' with list of paramters 'executable_options'. Returns True if program ran successfully.
    """
    assert type(executable_options) is ListType, "executable_options should be of type list (not %s)" % type(executable_options)
    try:
        proc  = Popen(([executable] + executable_options), stdout=PIPE, stderr=PIPE)
        response = proc.communicate()
        response_stdout, response_stderr = response[0].split('\n')[0], response[1].split('\n')[0]
    except OSError, e:
        if e.errno == errno.ENOENT:
            logging.error( "Unable to locate '%s' program. Is it in your path?" % executable )
        else:
            logging.error( "O/S error occured when trying to run '%s': \"%s\"" % (executable, str(e)) )
    except ValueError, e:
        logging.error( "Value error occured. Check your parameters." )
    else:
        if proc.wait() != 0:    
            logging.error( "Executable '%s' returned with the error: \"%s\"" %(executable,response_stderr) )
        else:
            logging.debug( "Executable '%s' returned successfully. First line of response was \"%s\"" %(executable, response_stdout) )
            return True

if __name__ == "__main__":
    options = sys.argv[2:]
    run_program(sys.argv[1],sys.argv[2:])
