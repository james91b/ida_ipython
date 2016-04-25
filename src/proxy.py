import win32process
import win32event
import sys

args = '"{idaq_path}" "-Snothing.idc -f {connection_file}"'

if __name__ == '__main__':
    hProcess, hThread, dwProcessId, dwThreadId = win32process.CreateProcess(None,
                                                                            args.format(idaq_path=sys.argv[1],
                                                                                        connection_file=sys.argv[2]),
                                                                            None,
                                                                            None,
                                                                            0,
                                                                            0,
                                                                            None,
                                                                            None,
                                                                            win32process.STARTUPINFO())
    while win32event.WAIT_OBJECT_0 != win32event.WaitForSingleObject(hProcess, win32event.INFINITE):
        pass
