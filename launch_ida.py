import sys
import subprocess
import os


def launch_ida():
    print sys.argv
    print str(os.getpid())
    connection_file = sys.argv[1]
    ida_location = sys.argv[2]
    ida_process = subprocess.Popen(
        [ida_location],
        env=dict(
            PARENT_PROCESS_PID=str(os.getpid()),
            JUPYTER_CONNECTION=connection_file,
            **os.environ
        )
    )
    ida_process.wait()


if __name__ == '__main__':
    launch_ida()
