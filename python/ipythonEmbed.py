import traceback

try:
    import os
    import sys
    import platform
    import subprocess
    import idaapi
    import atexit
    import contextlib

    # Remove the un-needed environment variable
    try:
        del os.environ['PARENT_PROCESS_PID']
    except KeyError:
        pass


    # This is a hack to get zmq to work with the Anaconda distribution and IDA.
    try:
        platform.python_implementation()
    except ValueError:
        sys.version = '2.7.5 |Anaconda 2.1.0 (32-bit)| (default, May 31 2013, 10:43:53) [MSC v.1500 32 bit (Intel)]'

    import __main__
    from ipykernel.kernelapp import IPKernelApp
    from IPython.utils.frame import extract_module_locals

    kernel_app = None
    menu_items = []
    qtconsole_processes = []


    def embed_kernel(module=None, local_ns=None, **kwargs):
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
    def capture_output_streams():
        _capture_output_streams()
        try:
            yield
        finally:
            _release_output_streams()


    def _capture_output_streams():
        sys.__stdout__, sys.__stderr__, sys.stdout, sys.stderr = sys.stdout, sys.stderr, sys.__stdout__, sys.__stderr__


    def _release_output_streams():
        sys.stdout, sys.stderr, sys.__stdout__, sys.__stderr__ = sys.__stdout__, sys.__stderr__, sys.stdout, sys.stderr


    def find_python_dir():
        # We need to get the python directory like this, because
        # sys.executable will return idaq.exe. This just goes two
        # directories up from os.py location
        return os.path.dirname(os.path.dirname(os.__file__))


    def start_qtconsole():
        try:
            if kernel_app:
                python_directory = find_python_dir()
                cmd_line = [
                    "{}/pythonw".format(python_directory),
                    "-m", "qtconsole",
                    "--existing", kernel_app.connection_file
                ]
                process = subprocess.Popen(cmd_line,
                    stdin=None,
                    stdout=None,
                    stderr=None,
                    close_fds=True)
                qtconsole_processes.append(process)
            else:
                print "Error: No kernel defined!"
        except Exception, e:
            traceback.print_exc()


    @atexit.register
    def term():
        kill_qtconsoles()
        remove_menus()

    def kill_qtconsoles():
        for process in qtconsole_processes:
            process.kill()


    def remove_menus():
        for menu_item in menu_items:
            idaapi.del_menu_item(menu_item)


    def add_idaipython_menu():
        menu_item = idaapi.add_menu_item('View/', 'IDAIPython QtConsole', '', 0, start_qtconsole, tuple())
        menu_items.append(menu_item)


    def start(argv=None):
        try:
            with capture_output_streams():
                global kernel_app
                if argv:
                    sys.argv = argv

                kernel_app = embed_kernel(module=__main__, local_ns={})

                def kernel_iteration():
                    with capture_output_streams():
                        kernel_app.kernel.do_one_iteration()

                add_idaipython_menu()

                return kernel_iteration
        except Exception, e:
            traceback.print_exc()
            raise

except Exception, e:
    traceback.print_exc()
