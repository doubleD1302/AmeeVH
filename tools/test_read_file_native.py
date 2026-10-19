import os
import ctypes
from pathlib import Path

GAME_DIR = Path(r'c:\YostarGames\StellaSora_EN')
os.chdir(str(GAME_DIR))
dll = ctypes.CDLL(str(GAME_DIR / 'GameAssembly.dll'))
dll.il2cpp_set_data_dir.argtypes = [ctypes.c_char_p]
dll.il2cpp_set_data_dir.restype = None
dll.il2cpp_set_data_dir(str(GAME_DIR / 'StellaSora_Data' / 'il2cpp_data').encode('utf-8'))

dll.il2cpp_add_internal_call.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
dll.il2cpp_add_internal_call.restype = None

@ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
def dummy_log(logType, logOption, msg_str, obj):
    pass

dll.dummy_log_ref = dummy_log
dummy_func_ptr = ctypes.cast(dummy_log, ctypes.c_void_p)

log_icalls = [
    b"UnityEngine.DebugLogHandler::Internal_Log(UnityEngine.LogType,UnityEngine.LogOption,System.String,UnityEngine.Object)",
    b"UnityEngine.DebugLogHandler::Internal_LogException(System.Exception,UnityEngine.Object)",
    b"UnityEngine.Debug::Log(System.Object)",
    b"UnityEngine.Debug::LogError(System.Object)",
    b"UnityEngine.Debug::LogWarning(System.Object)",
]
for icall in log_icalls:
    dll.il2cpp_add_internal_call(icall, dummy_func_ptr)

dll.il2cpp_init.argtypes = [ctypes.c_char_p]
dll.il2cpp_init.restype = ctypes.c_void_p
domain = dll.il2cpp_init(b'StellaSora')

for icall in log_icalls:
    dll.il2cpp_add_internal_call(icall, dummy_func_ptr)

dll.il2cpp_domain_get_assemblies.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t)]
dll.il2cpp_domain_get_assemblies.restype = ctypes.POINTER(ctypes.c_void_p)
dll.il2cpp_assembly_get_image.argtypes = [ctypes.c_void_p]
dll.il2cpp_assembly_get_image.restype = ctypes.c_void_p
dll.il2cpp_image_get_name.argtypes = [ctypes.c_void_p]
dll.il2cpp_image_get_name.restype = ctypes.c_char_p
dll.il2cpp_image_get_class_count.argtypes = [ctypes.c_void_p]
dll.il2cpp_image_get_class_count.restype = ctypes.c_size_t
dll.il2cpp_image_get_class.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
dll.il2cpp_image_get_class.restype = ctypes.c_void_p
dll.il2cpp_class_get_name.argtypes = [ctypes.c_void_p]
dll.il2cpp_class_get_name.restype = ctypes.c_char_p
dll.il2cpp_class_get_methods.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
dll.il2cpp_class_get_methods.restype = ctypes.c_void_p
dll.il2cpp_method_get_name.argtypes = [ctypes.c_void_p]
dll.il2cpp_method_get_name.restype = ctypes.c_char_p
dll.il2cpp_method_get_param_count.argtypes = [ctypes.c_void_p]
dll.il2cpp_method_get_param_count.restype = ctypes.c_uint32
dll.il2cpp_method_get_param_name.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
dll.il2cpp_method_get_param_name.restype = ctypes.c_char_p
dll.il2cpp_runtime_invoke.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p)]
dll.il2cpp_runtime_invoke.restype = ctypes.c_void_p
dll.il2cpp_string_new.argtypes = [ctypes.c_char_p]
dll.il2cpp_string_new.restype = ctypes.c_void_p
dll.il2cpp_array_length.argtypes = [ctypes.c_void_p]
dll.il2cpp_array_length.restype = ctypes.c_uint32

size = ctypes.c_size_t(0)
assemblies = dll.il2cpp_domain_get_assemblies(domain, ctypes.byref(size))
archive_cls = None
for i in range(size.value):
    asm = assemblies[i]
    img = dll.il2cpp_assembly_get_image(asm)
    if dll.il2cpp_image_get_name(img).decode('utf-8') == 'GameFramework.dll':
        for c in range(dll.il2cpp_image_get_class_count(img)):
            cls = dll.il2cpp_image_get_class(img, c)
            if dll.il2cpp_class_get_name(cls).decode('utf-8') == 'Archive':
                archive_cls = cls

it = ctypes.c_void_p(0)
open_mth = None
read_file_hash_mth = None
get_hashs_mth = None

while True:
    m = dll.il2cpp_class_get_methods(archive_cls, ctypes.byref(it))
    if not m:
        break
    mname = dll.il2cpp_method_get_name(m).decode('utf-8')
    if mname == 'Open':
        open_mth = m
    elif mname == 'get_Hashs':
        get_hashs_mth = m
    elif mname == 'ReadFile':
        pname = dll.il2cpp_method_get_param_name(m, 0).decode('utf-8')
        if pname == 'hash':
            read_file_hash_mth = m

arc_path = r'c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx'
s_arg = dll.il2cpp_string_new(arc_path.encode('utf-8'))
args = (ctypes.c_void_p * 1)(s_arg)
exc = ctypes.c_void_p(0)
arc_obj = dll.il2cpp_runtime_invoke(open_mth, None, args, ctypes.byref(exc))

hashs_arr = dll.il2cpp_runtime_invoke(get_hashs_mth, arc_obj, None, ctypes.byref(exc))
hash_count = dll.il2cpp_array_length(hashs_arr)
hash_ptr = hashs_arr + 0x20

for i in range(10):
    h = ctypes.c_uint64.from_address(hash_ptr + i*8).value
    h_val = ctypes.c_uint64(h)
    args = (ctypes.c_void_p * 1)(ctypes.cast(ctypes.byref(h_val), ctypes.c_void_p))
    exc = ctypes.c_void_p(0)
    data_arr = dll.il2cpp_runtime_invoke(read_file_hash_mth, arc_obj, args, ctypes.byref(exc))
    if data_arr:
        dlen = dll.il2cpp_array_length(data_arr)
        data = ctypes.string_at(data_arr + 0x20, dlen)
        hex_rep = data[:16].hex(' ')
        print(f"[{i}] Hash: 0x{h:016x} | Len: {dlen} | Hex: {hex_rep}")
        # Compare with unpacked file
        unpacked_path = Path(f'work/research/unpacked_data/entries/{i:05d}_0x{h:016x}.bin')
        if unpacked_path.exists():
            u_data = unpacked_path.read_bytes()
            match = (data == u_data)
            print(f"      Matches our adapter unpacked: {match} (Adapter len: {len(u_data)})")
    else:
        print(f"[{i}] Hash: 0x{h:016x} | data_arr is None! Exc: {exc.value}")
