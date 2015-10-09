#include "persist.h"

#include <windows.h>

int persist(void) {

    BOOL bOk;
    HMODULE hModule;

    /* Make sure the module stays in memory until process termination. */
    bOk = GetModuleHandleEx(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN , (LPWSTR)persist, &hModule);

    if (0 == bOk) {
        return -1;
    }

    return 0;
}