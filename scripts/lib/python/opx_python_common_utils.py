#!/usr/bin/python
import subprocess

def run_cmd_get_output(cmdline) :
    """
    Execute any command from python file
    @params[in] cmdline - command line to execute
    @returns Output from the command line execution
    """

    try:
        p = subprocess.Popen(cmdline,stdout=subprocess.PIPE, shell=True)

        result = p.wait();
        details = p.stdout.read()

        if result != 0:
            exit(1)

        return details.split('\n')
    except :
        #print( sys.exc_info())
        pass
    return [""]
