#include "ipythonEmbed.h"
#include <windows.h>
#include <tlhelp32.h>
#include <Psapi.h>

static const char IPYTHON_EMBED_MODULE[] = "ipythonEmbed";
static const char IPYTHON_EMBED_START_METHOD_NAME[] = "start";
static const char IPYTHON_EMBED_START_QTCONSOLE_METHOD_NAME[] = "start_qtconsole";
static const char QT4_MODULE_NAME[] = "QtCore4.dll";
static const char QT5_MODULE_NAME[] = "Qt5Core.dll";
static const char EVENT_LOOP_FUNC_NAME[] = "?processEvents@QEventDispatcherWin32@QT@@UAE_NV?$QFlags@W4ProcessEventsFlag@QEventLoop@QT@@@2@@Z";
static const char PARENT_PID_ENV_NAME[] = "PARENT_PROCESS_PID";
static const char IDA_PYTHON_PLUGIN[] = "python";

static PyObject* kernel_do_one_iteration = NULL;
static PyObject* commandline_args = NULL;
static bool attempted_start_kernel = false;
static bool python_loaded = false;

typedef int (__fastcall *tQEventDispatcherWin32)(void*, void*, int);
tQEventDispatcherWin32 pQEventDispatcherWin32 = NULL;

PyObject* start_ipython_kernel(PyObject* cmdline)
{
    PyObject *ipython_embed_module = NULL,
             *ipython_start_func = NULL,
             *ipython_kernel = NULL,
             *arglist = NULL;

    ipython_embed_module = PyImport_ImportModule(IPYTHON_EMBED_MODULE);
    if (ipython_embed_module == NULL) {
        goto error;
    }

    ipython_start_func = PyObject_GetAttrString(ipython_embed_module, IPYTHON_EMBED_START_METHOD_NAME);
    if (ipython_start_func == NULL) {
        goto error;
    }

    if (PyCallable_Check(ipython_start_func)) {
        if (cmdline != NULL) {
            arglist = Py_BuildValue("(O)", cmdline);
            ipython_kernel = PyObject_CallObject(ipython_start_func, arglist);
        } else {
            ipython_kernel = PyObject_CallObject(ipython_start_func, NULL);
        }
    }

    if (ipython_kernel == NULL || !PyCallable_Check(ipython_kernel)) {
        goto error;
    }

    goto cleanup;
error:
    ipython_kernel = NULL;
cleanup:
    Py_XDECREF(arglist);
    Py_XDECREF(ipython_embed_module);
    Py_XDECREF(ipython_start_func);
    return ipython_kernel;
}

void init_python(void)
{
    // Make sure the python is initialized
    if (!Py_IsInitialized()) {
        Py_Initialize();
    }
}

void init_ipython_kernel(void)
{
    init_python();
    kernel_do_one_iteration = start_ipython_kernel(commandline_args);
}

DWORD get_parent_pid()
 {
	static BOOL already_check_environment = FALSE;
	static DWORD ppid = 0;

	if (TRUE == already_check_environment) {
		return ppid;
	}

	/* Get the environment variable for the parent pid */
	char pszPidString[30];
	DWORD ret = GetEnvironmentVariableA(PARENT_PID_ENV_NAME, pszPidString, sizeof(pszPidString));

	already_check_environment = TRUE;

	if ((0 == ret) || (sizeof(pszPidString) == ret)) {
		msg("No parent PID provided.\n");
		return 0;
	}

	/* Parse it into a number and return it.*/
	OutputDebugStringA("Found parent PID");
	ppid = strtoul(pszPidString, NULL, 10);
}

HANDLE get_parent_handle()
 {
	DWORD ppid = get_parent_pid();

	if (0 == ppid) {
		return NULL;
	}

	HANDLE hParentProcess = OpenProcess(SYNCHRONIZE, FALSE, get_parent_pid());
	return hParentProcess;
}

BOOL is_parent_dead()
 {
	int nArgs = 0;

	qstrvec_t out_args;
	nArgs = parse_command_line3(GetCommandLineA(), &out_args, NULL, 0);


	static HANDLE hParentProcess = NULL;
	DWORD dwResult;

	if (NULL == hParentProcess) {
		hParentProcess = get_parent_handle();
	}

	/* Still no parent handle? Well, it can't be dead then! */
	if (NULL == hParentProcess) {
		return FALSE;
	}

	dwResult = WaitForSingleObject(hParentProcess, 0);
	if (WAIT_OBJECT_0 == dwResult) {
		return TRUE;
	}

	return FALSE;
}

void ipython_embed_iteration()
{
	if (TRUE == is_parent_dead()) {
		OutputDebugStringA("[IDA-IPython] Parent is dead. Terminating.");
		ipython_embed_term();
		qexit(0);
	}

    PyGILState_STATE state = PyGILState_Ensure();

    if (kernel_do_one_iteration == NULL && !attempted_start_kernel) {
        attempted_start_kernel = true;
        init_ipython_kernel();
        //TODO: Report the error, call stack etc.
        if ( PyErr_Occurred() ) {
            msg("A Python Error Occurred trying to start the kernel!\n");
        }
    } else if (kernel_do_one_iteration != NULL) {
        PyObject_CallObject(kernel_do_one_iteration, NULL);
    }

    PyGILState_Release(state);

}

FARPROC eventloop_address()
{
    HMODULE qtmodule = GetModuleHandleA(QT4_MODULE_NAME);

    if (NULL == qtmodule) {
        qtmodule = GetModuleHandleA(QT5_MODULE_NAME);
    }

    FARPROC src = GetProcAddress(qtmodule, EVENT_LOOP_FUNC_NAME);
    return src;
}

int __fastcall DetourQEventDispatcherWin32(void* ecx, void* edx, int i)
{
    try {
        ipython_embed_iteration();
        return pQEventDispatcherWin32(ecx, edx, i);
    } catch (const std::exception& ex) {
        std::string error = ex.what();
        const char *cstr = error.c_str();
        warning(cstr);
    } catch (...) {
        warning("Something went wrong in the detour!");
    }

    return 0;
}

void ipython_start_qtconsole()
{
    PyGILState_STATE state = PyGILState_Ensure();

    PyObject *ipython_embed_module = NULL,
             *ipython_qtconsole_func = NULL;

    ipython_embed_module = PyImport_ImportModule(IPYTHON_EMBED_MODULE);
    if (ipython_embed_module == NULL) {
        warning("could not import ipythonEmbed module");
        goto cleanup;
    }

    ipython_qtconsole_func = PyObject_GetAttrString(ipython_embed_module, IPYTHON_EMBED_START_QTCONSOLE_METHOD_NAME);
    if (ipython_qtconsole_func == NULL) {
        warning("could not find start_qtconsole function");
        goto cleanup;
    }

    if (!PyCallable_Check(ipython_qtconsole_func)) {
        warning("ipython start_qtconsole function is not callable");
        goto cleanup;
    }

    PyObject_CallObject(ipython_qtconsole_func, NULL);

cleanup:
    Py_XDECREF(ipython_embed_module);
    Py_XDECREF(ipython_qtconsole_func);

    PyGILState_Release(state);
}

IPYTHONEMBED_STATUS ipython_embed_start(PyObject* cmdline)
{
    commandline_args = cmdline;

    if (MH_Initialize() != MH_OK) {
        return IPYTHONEMBED_MINHOOK_INIT_FAILED;
    }

    void* qt_eventloop = (void*)eventloop_address();
    if (MH_CreateHook(qt_eventloop,
                     &DetourQEventDispatcherWin32,
                     (LPVOID*)&pQEventDispatcherWin32) != MH_OK) {
        return IPYTHONEMBED_CREATE_HOOK_FAILED;
    }

    if (MH_EnableHook(qt_eventloop) != MH_OK) {
        return IPYTHONEMBED_ENABLE_HOOK_FAILED;
    }

    return IPYTHONEMBED_OK;
}

void ipython_embed_term()
{
    MH_DisableHook(MH_ALL_HOOKS);
    MH_Uninitialize();
    Py_XDECREF(kernel_do_one_iteration);
    Py_XDECREF(commandline_args);
}
