import psutil, ctypes as ct, time
from dw1_addresses import ADDRESSES

WATCH_KEYS = {
    "Care Mistakes": '"Condition"/"Care Mistakes"',
    "IsHungry": '"Condition Flag"/"Hungry"',
    "NeedsPoop": '"Condition Flag"/"Poop"',
    "Sleepy": '"Condition Flag"/"Sleepy"',
    "Tiredness": '"Condition"/"Tiredness (0-100)"',
    "Happiness": '"Condition"/"Happiness"',
    "Energy Level": '"Condition"/"Energy Level"',
    "Weight": '"Condition"/"Weight"',
    "Lifespan": '"Condition"/"Remaining Lifetime (Hours)"',
    "Age since Digivolution": '"Condition"/"Age in hours (for evolve)"',

    "Hungry": '"Condition"/"Hungry Timer"',
    "Pooping": '"Condition"/"Pooping Timer"',
    "Sickness": '"Condition"/"SicknessTimer"',
    "Starvation": '"Condition"/"Starvation Timer"',
    "Tiredness Hunger": '"Condition"/"Tiredness Hunger Timer"',
    "Tiredness Sleep": '"Condition"/"Sleep"/"Tiredness Sleep Timer"',
    "Training Boost": '"Condition"/"Training Boost"/"Training Boost Timer"',

    "Off": '"Parameter"/"Off"',
    "Def": '"Def"',
    "Speed": '"Parameter"/"Speed"',
    "Brains": '"Parameter"/"Brains"',
    "HP": '"Parameter"/"HP"',
    "MP": '"Parameter"/"MP"',

    "Bits": '"Parameter"/"Bits"',
    "Tournaments won": '"Tournaments won"',
    "Tamer Level": '"Tamer Values"/"Parameter"/"Tamer Level"',

    "Year": '"Time"/"Year"',
    "Day": '"Time"/"Day"',
    "Hour": '"Time"/"Hour"',
    "Minute": '"Time"/"Minute"',

    "Took Meat": '"Took Meat"',
    "Drimogemon Days passed": '"Drimogemon Days passed"',
    "Drimogemon": '" 30 - Drimogemon/Treasure Hunt Timer"',
    "Back Dimension": '" 28 - Back Dimension Timer"',

    "Inventory Pointer": '"Inventory Pointer"',
    "Inventory Size": '"Inventory Size"',
    "Slot1/Item Amount": '"Tamer Values"/"Inventory"/"Default"/"Slot 1"/"Item Amount"',
    "Slot1/Item Name": '"Tamer Values"/"Inventory"/"Default"/"Slot 1"/"Item Name"',
    "Slot1/Item Type": '"Tamer Values"/"Inventory"/"Default"/"Slot 1"/"Item Type"',

    "Current Screen ID": '"Technical Values"/"Current Screen ID"',
    "Location X": '"Tamer Values"/"Parameter"/"Location X"',
    "Location Y": '"Tamer Values"/"Parameter"/"Location Y"',
    "Location Z": '"Tamer Values"/"Parameter"/"Location Z"',
}

def psx_offset(address_str):
    prefix = "PSXBaseAddress+"
    if not address_str.startswith(prefix):
        raise ValueError(f"Unsupported address format: {address_str}")
    return int(address_str[len(prefix):], 16)

WATCH_OFFSETS = {
    label: psx_offset(ADDRESSES[key]["address"])
    for label, key in WATCH_KEYS.items()
}



def main():
    lifetime_key = find_address_key(["lifespan", "remaining lifetime (hours)", "remaining lifetime"])
    address_value = get_address_value(lifetime_key, verbose=False)
    print(f"{lifetime_key} -> {address_value}")

# =========================================================

def get_address_value(address_name, process=None, psx_base=None, target="psxfin.exe", verbose=False):
    address_key = WATCH_KEYS.get(address_name, address_name)
    entry = ADDRESSES.get(address_key)
    if not entry:
        raise KeyError(f"Unknown address name: {address_name}")
    off = psx_offset(entry["address"])
    close_process = False
    if process is None:
        process, psx_base = attach_process(target=target, verbose=verbose)
        close_process = True
    try:
        addr = psx_base + off
        if verbose:
            print(f"{address_name}: base 0x{psx_base:08X} + off 0x{off:08X} = 0x{addr:08X}")
        return read_value_by_type(process, addr, entry.get("type"))
    finally:
        if close_process and process:
            K.CloseHandle(process)

def get_psx_base(process, delta=0x90800, verbose=False):
    pat = bytes.fromhex(
        "a0 00 0a 24 08 00 40 01 44 00 09 24 00 00 00 00 "
        "a0 00 0a 24 08 00 40 01 49 00 09 24 00 00 00 00 "
        "a0 00 0a 24 08 00 40 01 70 00 09 24 00 00 00 00 "
        "a0 00 0a 24 08 00 40 01 72 00 09 24 00 00 00 00"
    )
    code_start = aob_scan_first(process, pat, max_scan_seconds=15, verbose=verbose)
    return code_start - delta

def attach_process(target="psxfin.exe", verbose=False):
    pid = pid_by_name(target)
    if pid is None:
        raise RuntimeError(f"Process not found: {target}")
    if verbose:
        print(f"Found {target} with PID {pid}")
    process = open_process(pid)
    psx_base = get_psx_base(process, verbose=verbose)
    if verbose:
        print(f"PSX base: 0x{psx_base:08X}")
    return process, psx_base

def read_mem(h, addr, size):
    buf, rd = (ct.c_ubyte * size)(), ct.c_size_t()
    if not (K.ReadProcessMemory(h, ct.c_void_p(addr), ct.byref(buf), size, ct.byref(rd)) and rd.value == size):
        raise ct.WinError(ct.get_last_error())
    return int.from_bytes(bytes(buf), byteorder="little", signed=False)

def read_value_by_type(h, addr, value_type):
    vt = (value_type or "").lower()
    if "4 bytes" in vt:
        return read_mem(h, addr, 4)
    if "2 bytes" in vt:
        return read_mem(h, addr, 2)
    # Byte and Binary default to 1 byte
    return read_mem(h, addr, 1)

def find_address_key(keywords):
    for keyword in keywords:
        keyword_lower = keyword.lower()
        for key in ADDRESSES:
            if keyword_lower in key.lower():
                return key
    raise KeyError(f"No address key found for keywords: {keywords}")

def print_watch_values(target="psxfin.exe", verbose=False):
    pid = pid_by_name(target)
    if pid is None:
        raise RuntimeError(f"Process not found: {target}")
    if verbose:
        print(f"Found {target} with PID {pid}")
    process = open_process(pid)
    try:
        psx_base = get_psx_base(process, verbose=verbose)
        if verbose:
            print(f"PSX base: 0x{psx_base:08X}")
        for label, key in WATCH_KEYS.items():
            entry = ADDRESSES.get(key)
            if not entry:
                print(f"{label}: missing key {key}")
                continue
            addr = psx_base + psx_offset(entry["address"])
            value = read_value_by_type(process, addr, entry.get("type"))
            print(f"{label}: {value}")
    finally:
        K.CloseHandle(process)

K = ct.windll.kernel32

class MBI(ct.Structure):
    _fields_ = [("BaseAddress", ct.c_void_p), ("AllocationBase", ct.c_void_p),
                ("AllocationProtect", ct.c_uint32), ("RegionSize", ct.c_size_t),
                ("State", ct.c_uint32), ("Protect", ct.c_uint32), ("Type", ct.c_uint32)]

def pid_by_name(name):
    name = name.lower()
    return next(
        (p.pid for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower() == name),
        None,
    )

def open_process(pid):
    h = K.OpenProcess(0x0400 | 0x0010, 0, pid)  # QUERY_INFORMATION | VM_READ
    if not h: raise ct.WinError(ct.get_last_error())
    return h

def aob_scan_first(h, pat, chunk=8*1024*1024, max_scan_seconds=15, verbose=False):
    mbi, a = MBI(), 0
    deadline = time.monotonic() + max_scan_seconds if max_scan_seconds else None
    ov = len(pat) - 1 if len(pat) > 1 else 0
    READABLE = (2, 4, 8, 0x20, 0x40, 0x80)  # R/RW/WC + exec variants
    regions_scanned = 0
    last_report = time.monotonic()
    while K.VirtualQueryEx(h, ct.c_void_p(a), ct.byref(mbi), ct.sizeof(mbi)):
        if deadline and time.monotonic() > deadline:
            raise RuntimeError(f"AOB scan timed out after {max_scan_seconds}s")
        b, sz, pr, st = int(mbi.BaseAddress or 0), int(mbi.RegionSize), int(mbi.Protect), int(mbi.State)
        if sz <= 0:
            a = b + 0x1000
            continue
        regions_scanned += 1
        now = time.monotonic()
        if verbose and (now - last_report) >= 1.0:
            print(f"Scanning... regions={regions_scanned} at 0x{b:08X} (size 0x{sz:X})")
            last_report = now
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
                if deadline and time.monotonic() > deadline:
                    raise RuntimeError(f"AOB scan timed out after {max_scan_seconds}s")
        a = b + sz
    raise RuntimeError("AOB not found")

def read_u16(h, addr):
    v, rd = ct.c_ushort(), ct.c_size_t()
    if not (K.ReadProcessMemory(h, ct.c_void_p(addr), ct.byref(v), 2, ct.byref(rd)) and rd.value == 2):
        raise ct.WinError(ct.get_last_error())
    return v.value



if __name__ == "__main__":
    main()
