from jupyter_client.ioloop import IOLoopKernelManager
import os
import sys
from subprocess import Popen, PIPE

from IPython.utils.encoding import getdefaultencoding
from IPython.utils.py3compat import cast_bytes_py2

IDA_EXE = r"C:\Program Files (x86)\IDA 6.6\idaq.exe"

def launch_ida_kernel(cmd, stdin=None, stdout=None, stderr=None,
                        independent=False,
                        cwd=None, ipython_kernel=True,
                        env=None,
                        **kw
                        ):
    """ Launches a localhost kernel, binding to the specified ports.

    Parameters
    ----------
    cmd : Popen list,
        A string of Python code that imports and executes a kernel entry point.

    stdin, stdout, stderr : optional (default None)
        Standards streams, as defined in subprocess.Popen.

    independent : bool, optional (default False)
        If set, the kernel process is guaranteed to survive if this process
        dies. If not set, an effort is made to ensure that the kernel is killed
        when this process dies. Note that in this case it is still good practice
        to kill kernels manually before exiting.

    cwd : path, optional
        The working dir of the kernel process (default: cwd of this process).

    ipython_kernel : bool, optional
        Whether the kernel is an official IPython one,
        and should get a bit of special treatment.

    Returns
    -------

    Popen instance for the kernel subprocess
    """

    # Popen will fail (sometimes with a deadlock) if stdin, stdout, and stderr
    # are invalid. Unfortunately, there is in general no way to detect whether
    # they are valid.  The following two blocks redirect them to (temporary)
    # pipes in certain important cases.

    # If this process has been backgrounded, our stdin is invalid. Since there
    # is no compelling reason for the kernel to inherit our stdin anyway, we'll
    # place this one safe and always redirect.
    redirect_in = True
    _stdin = PIPE if stdin is None else stdin

    # If this process in running on pythonw, we know that stdin, stdout, and
    # stderr are all invalid.
    redirect_out = sys.executable.endswith('pythonw.exe')
    if redirect_out:
        _stdout = PIPE if stdout is None else stdout
        _stderr = PIPE if stderr is None else stderr
    else:
        _stdout, _stderr = stdout, stderr

    env = env if (env is not None) else os.environ.copy()

    encoding = getdefaultencoding(prefer_stream=False)

    # Spawn a kernel.
    if sys.platform == 'win32':
        # Popen on Python 2 on Windows cannot handle unicode args or cwd
        cmd = [ cast_bytes_py2(c, encoding) for c in cmd ]
        if cwd:
            cwd = cast_bytes_py2(cwd, sys.getfilesystemencoding() or 'ascii')

        from jupyter_client import win_interrupt
        # Create a Win32 event for interrupting the kernel.
        interrupt_event = win_interrupt.create_interrupt_event()
        # Store this in an environment variable for third party kernels, but at
        # present, our own kernel expects this as a command line argument.
        env["IPY_INTERRUPT_EVENT"] = str(interrupt_event)
        if ipython_kernel:
            #cmd += [ '--interrupt=%i' % interrupt_event ]

            # If the kernel is running on pythonw and stdout/stderr are not been
            # re-directed, it will crash when more than 4KB of data is written to
            # stdout or stderr. This is a bug that has been with Python for a very
            # long time; see http://bugs.python.org/issue706263.
            # A cleaner solution to this problem would be to pass os.devnull to
            # Popen directly. Unfortunately, that does not work.
            if cmd[0].endswith('pythonw.exe'):
                if stdout is None:
                    cmd.append('--no-stdout')
                if stderr is None:
                    cmd.append('--no-stderr')

        # Launch the kernel process.
        if independent:
            cmd = '"{0}" -S" {1}"'.format(cmd[0], " ".join(cmd[1:]))
            proc = Popen(cmd,
                         creationflags=512, # CREATE_NEW_PROCESS_GROUP
                         stdin=_stdin, stdout=_stdout, stderr=_stderr, env=os.environ)
        else:
            if ipython_kernel:
                try:
                    from _winapi import DuplicateHandle, GetCurrentProcess, \
                        DUPLICATE_SAME_ACCESS
                except:
                    from _subprocess import DuplicateHandle, GetCurrentProcess, \
                        DUPLICATE_SAME_ACCESS
                pid = GetCurrentProcess()
                handle = DuplicateHandle(pid, pid, pid, 0,
                                         True, # Inheritable by new processes.
                                         DUPLICATE_SAME_ACCESS)
                #cmd +=[ '--parent=%i' % handle ]

            cmd = '"{0}" -S"nothing.idc {1}"'.format(cmd[0], " ".join(cmd[1:]))
            proc = Popen(cmd,
                         stdin=_stdin, stdout=_stdout, stderr=_stderr, cwd=cwd, env=os.environ)

        # Attach the interrupt event to the Popen objet so it can be used later.
        proc.win32_interrupt_event = interrupt_event

    # Clean up pipes created to work around Popen bug.
    if redirect_in:
        if stdin is None:
            proc.stdin.close()
    if redirect_out:
        if stdout is None:
            proc.stdout.close()
        if stderr is None:
            proc.stderr.close()

    return proc


class IDAKernelManager(IOLoopKernelManager):
    def _launch_kernel(self, kernel_cmd, **kw):
        """actually launch the kernel

        override in a subclass to launch kernel subprocesses differently
        """
        kernel_cmd = [IDA_EXE] + kernel_cmd[3:]
        return launch_ida_kernel(kernel_cmd, **kw)
