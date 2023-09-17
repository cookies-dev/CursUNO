import ctypes

"""
send shutdown to the system with the given message and timeout

no need to run as admin
"""


def shutdown(msg: str, timeout: int = 20, force=False, reboot=True):
    advapi32 = ctypes.windll.advapi32
    ntdll = ctypes.windll.ntdll
    if res := ntdll.RtlAdjustPrivilege(19, True, False, ctypes.pointer(ctypes.c_bool())):
        raise ctypes.WinError(ntdll.RtlNtStatusToDosError(res))
    if not advapi32.InitiateSystemShutdownA(None, msg, timeout, force, reboot):
        raise ctypes.WinError(ctypes.get_last_error())
    return True


if __name__ == "__main__":
    shutdown("tets te sye", 20)
