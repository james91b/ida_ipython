import win32process
import win32event
import sys

args = 'C:\\Program Files (x86)\\IDA 6.8\\idaq.exe "-Snothing.idc -f {connection_file}"'

if __name__ == '__main__':
    hProcess, hThread, dwProcessId, dwThreadId = win32process.CreateProcess(None,
                                                                            args.format(connection_file=sys.argv[1]),
                                                                            None,
                                                                            None,
                                                                            0,
                                                                            0,
                                                                            None,
                                                                            None,
                                                                            win32process.STARTUPINFO())
    while win32event.WAIT_OBJECT_0 != win32event.WaitForSingleObject(hProcess, win32event.INFINITE):
        pass