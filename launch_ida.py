import sys
import subprocess
import os

CONNECTION_ARG = '-Snothing.idc -f {file}'

def launch_ida():
    print sys.argv
    print str(os.getpid())
    conn = CONNECTION_ARG.format(file=sys.argv[1])
    ida_location=sys.argv[2]
    ida_process = subprocess.Popen(
        [ida_location, conn],
         env=dict(
             PARENT_PROCESS_PID=str(os.getpid()),
              **os.environ
              )
        )
    ida_process.wait()

if __name__ == '__main__':
    launch_ida()
