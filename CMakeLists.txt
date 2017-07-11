cmake_minimum_required(VERSION 2.8)
project(ida_ipython)

cmake_policy(SET CMP0015 NEW)

set(CMAKE_BUILD_TYPE Release)

#Read the launch script and escape chars
file(READ "launch_ida.py" LAUNCH_IDA_PY)
string(REPLACE "\"" "\\\"" LAUNCH_IDA_PY "${LAUNCH_IDA_PY}")
string(REPLACE "\n" "\\n" LAUNCH_IDA_PY "${LAUNCH_IDA_PY}")
string(REPLACE "\r" "\\r" LAUNCH_IDA_PY "${LAUNCH_IDA_PY}")

#Read the template replace script placeholder
file(READ "kernel.json.template" KERNEL_TEMPLATE)
string(REPLACE
    "{{LAUNCH_SCRIPT}}"
    ${LAUNCH_IDA_PY}
    IDA_KERNEL
    ${KERNEL_TEMPLATE}
)


#Create the IDA32 kernel
string(REPLACE
    "{{DISPLAY_NAME}}"
    "IDA32"
    IDA_32_KERNEL
    ${IDA_KERNEL}
)
string(REPLACE
    "{{EXE_NAME}}"
    "idaq.exe"
    IDA_32_KERNEL
    ${IDA_32_KERNEL}
)
#Create the IDA64 kernel
string(REPLACE
    "{{DISPLAY_NAME}}"
    "IDA64"
    IDA_64_KERNEL
    ${IDA_KERNEL}
)
string(REPLACE
    "{{EXE_NAME}}"
    "idaq64.exe"
    IDA_64_KERNEL
    ${IDA_64_KERNEL}
)

file(WRITE notebook/kernels/ida32/kernel.json ${IDA_32_KERNEL})
file(WRITE notebook/kernels/ida64/kernel.json ${IDA_64_KERNEL})

#install(TARGETS ida32_ipython DESTINATION ${IDA_DIR}/plugins)
#install(TARGETS ida64_ipython DESTINATION ${IDA_DIR}/plugins)
#install(FILES python/ipythonEmbed.py DESTINATION ${IDA_DIR}/python)
#install(FILES idc/nothing.idc DESTINATION ${IDA_DIR}/idc)
