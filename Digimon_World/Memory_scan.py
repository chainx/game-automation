import psutil, ctypes as ct

def main():
    address_value = get_address_values(0x90800, 0x1384A8)
    print(address_value)

# =========================================================

def get_address_values(DELTA, OFF, TARGET="psxfin.exe"):
    PAT = bytes.fromhex(
        "a0 00 0a 24 08 00 40 01 44 00 09 24 00 00 00 00 "
        "a0 00 0a 24 08 00 40 01 49 00 09 24 00 00 00 00 "
        "a0 00 0a 24 08 00 40 01 70 00 09 24 00 00 00 00 "
        "a0 00 0a 24 08 00 40 01 72 00 09 24 00 00 00 00"
    )
    pid = pid_by_name(TARGET)
    process = open_process(pid)
    try:
        code_start = aob_scan_first(process, PAT)
        psx_base = code_start - DELTA
        return read_u16(process, psx_base + OFF)
    finally:
        K.CloseHandle(process)

# =========================================================

K = ct.windll.kernel32

class MBI(ct.Structure):
    _fields_ = [("BaseAddress", ct.c_void_p), ("AllocationBase", ct.c_void_p),
                ("AllocationProtect", ct.c_uint32), ("RegionSize", ct.c_size_t),
                ("State", ct.c_uint32), ("Protect", ct.c_uint32), ("Type", ct.c_uint32)]

def pid_by_name(name):
    name = name.lower()
    return next(p.pid for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower() == name)

def open_process(pid):
    h = K.OpenProcess(0x0400 | 0x0010, 0, pid)  # QUERY_INFORMATION | VM_READ
    if not h: raise ct.WinError(ct.get_last_error())
    return h

def aob_scan_first(h, pat, chunk=8*1024*1024):
    mbi, a = MBI(), 0
    ov = len(pat) - 1 if len(pat) > 1 else 0
    READABLE = (2, 4, 8, 0x20, 0x40, 0x80)  # R/RW/WC + exec variants
    while K.VirtualQueryEx(h, ct.c_void_p(a), ct.byref(mbi), ct.sizeof(mbi)):
        b, sz, pr, st = int(mbi.BaseAddress or 0), int(mbi.RegionSize), int(mbi.Protect), int(mbi.State)
        if st == 0x1000 and (pr & 0xFF) in READABLE and not (pr & 0x100) and not (pr & 1) and sz:
            end, p, tail = b + sz, b, b""
            while p < end:
                to = min(chunk, end - p)
                buf, rd = (ct.c_ubyte * to)(), ct.c_size_t()
                if K.ReadProcessMemory(h, ct.c_void_p(p), ct.byref(buf), to, ct.byref(rd)) and rd.value:
                    data = tail + bytes(buf[:rd.value])
                    i = data.find(pat)
                    if i != -1: return (p - len(tail)) + i
                    tail = data[-ov:] if ov else b""
                else:
                    tail = b""
                p += to
        a = b + sz
    raise RuntimeError("AOB not found")

def read_u16(h, addr):
    v, rd = ct.c_ushort(), ct.c_size_t()
    if not (K.ReadProcessMemory(h, ct.c_void_p(addr), ct.byref(v), 2, ct.byref(rd)) and rd.value == 2):
        raise ct.WinError(ct.get_last_error())
    return v.value



if __name__ == "__main__":
    main()