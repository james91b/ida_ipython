#ifndef IPYTHONEMBED_H
#define IPYTHONEMBED_H

#define _CRT_SECURE_NO_WARNINGS

#include <iostream>
#include <typeinfo>
#include <exception>
#include <string>

#include "Windows.h"
#include "Python.h"
#include "MinHook.h"

#include "pro.h"
#include "ida.hpp"
#include "idp.hpp"
#include "loader.hpp"
#include "expr.hpp"


typedef enum IPYTHONEMBED_STATUS
{
    IPYTHONEMBED_UNKNOWN = -1,
    IPYTHONEMBED_OK = 0,
    IPYTHONEMBED_ERROR,
    IPYTHONEMBED_MINHOOK_INIT_FAILED,
    IPYTHONEMBED_CREATE_HOOK_FAILED,
    IPYTHONEMBED_ENABLE_HOOK_FAILED
} IPYTHONEMBED_STATUS;

IPYTHONEMBED_STATUS ipython_embed_start(PyObject* cmdline);
void ipython_embed_term();

#endif //IPYTHONEMBED_H
