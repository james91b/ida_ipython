cmake_minimum_required(VERSION 2.8)
project(ida_ipython)

cmake_policy(SET CMP0015 NEW)

set(CMAKE_BUILD_TYPE Release)

if (WIN32)
    add_definitions(-D__NT__
                    -DUNICODE
                    -DWIN32
                    -D__IDP__)

    find_library(IDA32_LIB
                 NAMES "ida"
                 PATHS "${IDA_SDK}/lib/x86_win_vc_32")

    find_library(IDA64_LIB
                  NAMES "ida"
                  PATHS "${IDA_SDK}/lib/x86_win_vc_64")

    find_library(MINHOOK_LIB
                 NAMES "libMinHook-x86-v90-md"
                 PATHS "lib/MinHook_13_lib/lib")

    find_library(PYTHON_LIB
                 NAMES "python27"
                 PATHS "${PYTHON_DIR}/libs")

elseif (APPLE)
    add_definitions(-D__MAC__=1)
    find_library (IDA_LIB
                  NAMES "ida"
                  PATHS "${IDA_DIR}")
    #TODO...
elseif (UNIX)
    add_definitions(-D__LINUX__=1)
    #TODO...
endif ( )

set (SOURCES
     src/ida_ipython.cpp
     src/ipythonEmbed.cpp
     src/ipythonEmbed.h
     src/persist.h
     src/persist.cpp)

include_directories(${IDA_SDK}/include
                    ${PYTHON_DIR}/include
                    lib/MinHook_13_lib/include)

add_library(ida32_ipython MODULE ${SOURCES})
add_library(ida64_ipython MODULE ${SOURCES})

if (WIN32)
  set (IDA32_SUFFIX ".plw")
  set (IDA64_SUFFIX ".p64")
elseif (APPLE)
#    set (IDA_SUFFIX ".pmc")
elseif (UNIX)
#    set (IDA_SUFFIX ".plx")
endif ()

set_target_properties (ida32_ipython
                       PROPERTIES
                       SUFFIX ${IDA32_SUFFIX}
                       OUTPUT_NAME ida_ipython)

set_target_properties (ida64_ipython
                       PROPERTIES
                       SUFFIX ${IDA64_SUFFIX}
                       COMPILE_DEFINITIONS __EA64__
                       OUTPUT_NAME ida_ipython)

target_link_libraries (ida32_ipython
                       ${IDA32_LIB}
                       ${MINHOOK_LIB}
                       ${PYTHON_LIB})

target_link_libraries (ida64_ipython
                       ${IDA64_LIB}
                       ${MINHOOK_LIB}
                       ${PYTHON_LIB})

install(TARGETS ida32_ipython DESTINATION ${IDA_DIR}/plugins)
install(TARGETS ida64_ipython DESTINATION ${IDA_DIR}/plugins)
install(FILES python/ipythonEmbed.py DESTINATION ${IDA_DIR}/python)
install(FILES idc/nothing.idc DESTINATION ${IDA_DIR}/idc)
