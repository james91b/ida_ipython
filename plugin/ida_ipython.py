import traceback
import os
import sys
import platform
import subprocess
import idaapi
import contextlib

# This is a hack to get zmq to work with the Anaconda distribution and IDA.
try:
    platform.python_implementation()
except ValueError:
    sys.version = '2.7.5 |Anaconda 2.1.0 (32-bit)| (default, May 31 2013, 10:43:53) [MSC v.1500 32 bit (Intel)]'

import __main__
from ipykernel.kernelapp import IPKernelApp
from IPython.utils.frame import extract_module_locals


class IDAIPython(idaapi.plugin_t):
    wanted_name = "IDA IPython"
    wanted_hotkey = ""
    flags = idaapi.PLUGIN_FIX
    comment = ""
    help = ""

    def init(self):

        self.kernel_app = None
        self.menu_items = []
        self.qtconsole_processes = []

        argv = None
        connection_file = os.environ.get("JUPYTER_CONNECTION", None)
        if connection_file:
            argv = ['-f', connection_file]

        kernel_iteration = self.start(argv)

        def timer_callback():
            kernel_iteration()
            return int(1000 * self.kernel_app.kernel._poll_interval)

        self.timer = idaapi.register_timer(int(1000 * self.kernel_app.kernel._poll_interval), timer_callback)

        return idaapi.PLUGIN_KEEP

    def run(self, args):
        pass

    def term(self):
        idaapi.unregister_timer(self.timer)
        self.kill_qtconsoles()
        self.remove_menus()

    def embed_kernel(self, module=None, local_ns=None, **kwargs):
        """Embed and start an IPython kernel in a given scope.

        Parameters
        ----------
        module : ModuleType, optional
            The module to load into IPython globals (default: caller)
        local_ns : dict, optional
            The namespace to load into IPython user namespace (default: caller)

        kwargs : various, optional
            Further keyword args are relayed to the IPKernelApp constructor,
            allowing configuration of the Kernel.  Will only have an effect
            on the first embed_kernel call for a given process.

        """
        # get the app if it exists, or set it up if it doesn't
        if IPKernelApp.initialized():
            app = IPKernelApp.instance()
        else:
            app = IPKernelApp.instance(**kwargs)
            app.initialize(sys.argv)
            # Undo unnecessary sys module mangling from init_sys_modules.
            # This would not be necessary if we could prevent it
            # in the first place by using a different InteractiveShell
            # subclass, as in the regular embed case.
            main = app.kernel.shell._orig_sys_modules_main_mod
            if main is not None:
                sys.modules[app.kernel.shell._orig_sys_modules_main_name] = main

        # load the calling scope if not given
        (caller_module, caller_locals) = extract_module_locals(1)
        if module is None:
            module = caller_module
        if local_ns is None:
            local_ns = caller_locals

        app.kernel.user_module = None
        app.kernel.user_ns = None
        app.shell.set_completer_frame()

        if app.poller is not None:
            app.poller.start()

        app.kernel.start()
        return app

    @contextlib.contextmanager
    def capture_output_streams(self):
        self._capture_output_streams()
        try:
            yield
        finally:
            self._release_output_streams()

    def _capture_output_streams(self):
        sys.__stdout__, sys.__stderr__, sys.stdout, sys.stderr = sys.stdout, sys.stderr, sys.__stdout__, sys.__stderr__

    def _release_output_streams(self):
        sys.stdout, sys.stderr, sys.__stdout__, sys.__stderr__ = sys.__stdout__, sys.__stderr__, sys.stdout, sys.stderr

    def find_python_dir(self):
        # We need to get the python directory like this, because
        # sys.executable will return idaq.exe. This just goes two
        # directories up from os.py location
        return os.path.dirname(os.path.dirname(os.__file__))

    def start_qtconsole(self):
        try:
            if self.kernel_app:
                python_directory = self.find_python_dir()
                cmd_line = [
                    "{}/pythonw".format(python_directory),
                    "-m", "qtconsole",
                    "--existing", self.kernel_app.connection_file
                ]
                process = subprocess.Popen(cmd_line,
                                           stdin=None,
                                           stdout=None,
                                           stderr=None,
                                           close_fds=True)
                self.qtconsole_processes.append(process)
            else:
                print "Error: No kernel defined!"
        except Exception, e:
            traceback.print_exc()

    def kill_qtconsoles(self):
        for process in self.qtconsole_processes:
            process.kill()

    def remove_menus(self):
        for menu_item in self.menu_items:
            idaapi.del_menu_item(menu_item)

    def add_idaipython_menu(self):
        menu_item = idaapi.add_menu_item('View/', 'IDAIPython QtConsole', '', 0, self.start_qtconsole, tuple())
        self.menu_items.append(menu_item)

    def start(self, argv=None):
        try:
            with self.capture_output_streams():
                if argv:
                    sys.argv = argv

                self.kernel_app = self.embed_kernel(module=__main__, local_ns={})
                """
                 Starting with  ipython 4.2.0 whenever certain exceptions are thrown, there is a call to get_terminal_size().
                 in that function , in case environment variables for "COLUMNS" and "LINES" are not defined there is a call
                 to sys.__stdout__.fileno()   in order to get a handle to the current terminal. IDAPythonStdOut doesn't have an attribute fileno
                 so the call fails , and the kernel dies. the right way to solve it, is add AttributeError to the try/except in get_terminal_size.
                 a work around is to add this 2 environment variables
                """
                os.environ["COLUMNS"] = "80"
                os.environ["LINES"] = "24"

                def kernel_iteration():
                    with self.capture_output_streams():
                        self.kernel_app.kernel.do_one_iteration()

                self.add_idaipython_menu()

                return kernel_iteration
        except Exception, e:
            traceback.print_exc()
            raise


def PLUGIN_ENTRY():
    return IDAIPython()
