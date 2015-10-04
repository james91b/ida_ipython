try:
    import sys
    import platform

    #This is a hack to get zmq to work with the Anaconda distribution and IDA.
    try:
        platform.python_implementation()
    except ValueError:
        sys.version = '2.7.5 |Anaconda 2.1.0 (32-bit)| (default, May 31 2013, 10:43:53) [MSC v.1500 32 bit (Intel)]'

    import __main__
    from ipykernel.kernelapp import IPKernelApp
    from IPython.utils.frame import extract_module_locals

    sys.__stdout__ = sys.__stderr__ =  sys.stdout

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

    def start(argv=None):
        if argv:
            sys.argv = argv
        kapp = embed_kernel(module=__main__, local_ns={})
        return kapp.kernel.do_one_iteration

except Exception, e:
    import traceback
    traceback.print_exc()
