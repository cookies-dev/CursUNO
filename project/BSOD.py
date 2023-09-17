import ctypes

"""
send BSOD to the system with the given stop code

no need to run as admin
"""


def BSOD(stop_code=0xDEADDEAD) -> None:
    ntdll = ctypes.windll.ntdll
    if res := ntdll.RtlAdjustPrivilege(19, True, False, ctypes.pointer(ctypes.c_bool())):
        raise ctypes.WinError(ntdll.RtlNtStatusToDosError(res))
    if res := ntdll.NtRaiseHardError(stop_code, 0, 0, 0, 6, ctypes.byref(ctypes.c_ulong())):
        raise ctypes.WinError(ntdll.RtlNtStatusToDosError(res))

if __name__ == "__main__":
    BSOD()
