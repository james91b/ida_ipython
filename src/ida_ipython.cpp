#include "ipythonEmbed.h"

#include "pro.h"
#include "ida.hpp"

//Return the arguments in passed via IDC script arguments as a
//python list
PyObject* idc_script_args()
{
  PyObject *py_args = PyList_New(0);
	int nArgs = 0;
	LPWSTR *szArglist = CommandLineToArgvW(GetCommandLineW(), &nArgs);

	if (szArglist == NULL) {
		wprintf(L"CommandLineToArgvW failed\n");
	} else {
		for (int i = 0; i < nArgs; i++) {
			LPWSTR warg = szArglist[i];
			if (warg[0] != '-' || warg[1] != 'S')
				continue;

			char carg[512];
			wcstombs(carg, warg + 2, 512);

			qstrvec_t out_args;
			parse_command_line(carg, &out_args);

			for (unsigned int j = 0; j < out_args.size(); j++) {
        PyList_Insert(py_args, j, PyString_FromString(out_args[j].c_str()));
			}
		}
	}

	LocalFree(szArglist);
	return py_args;
}

int idaapi init(void)
{
    PyObject* idc_args = idc_script_args();

    IPYTHONEMBED_STATUS status = ipython_embed_start(idc_args);
    if (status != IPYTHONEMBED_OK) {
        switch (status) {
            case IPYTHONEMBED_MINHOOK_INIT_FAILED:
                warning("Failed to initialize MinHook");
                break;
            case IPYTHONEMBED_CREATE_HOOK_FAILED:
                warning("Failed to create the QT hook");
                break;
            case IPYTHONEMBED_ENABLE_HOOK_FAILED:
                warning("Failed to enable the QT hook");
                break;
            default:
                warning("Failed to start ipython kernel");
        }
        return PLUGIN_SKIP;
    }
    return PLUGIN_KEEP;
}

void idaapi term(void)
{
    ipython_embed_term();
}

//--------------------------------------------------------------------------
//
//      PLUGIN DESCRIPTION BLOCK
//
//--------------------------------------------------------------------------
static char wanted_name[] = "IDA IPython Kernel";
static char comment[] = "Runs an IPython Kernel within IDA";
static char help[] = "This plugin allows the user to run an IPython kernel within IDA\n";

plugin_t PLUGIN =
{
  IDP_INTERFACE_VERSION,
  PLUGIN_FIX | PLUGIN_HIDE,           // plugin flags
  init,                 // initialize
  term,                 // terminate. this pointer may be NULL.
  NULL,                 // invoke plugin
  comment,              // long comment about the plugin
                        // it could appear in the status line
                        // or as a hint
  help,                 // multiline help about the plugin
  wanted_name,          // the preferred short name of the plugin
  NULL                  // the preferred hotkey to run the plugin
};
