import os
import ctypes
from pathlib import Path

GAME_DIR = Path(r'c:\YostarGames\StellaSora_EN')
os.chdir(str(GAME_DIR))
dll = ctypes.CDLL(str(GAME_DIR / 'GameAssembly.dll'))
dll.il2cpp_set_data_dir(str(GAME_DIR / 'StellaSora_Data' / 'il2cpp_data').encode('utf-8'))

dll.il2cpp_add_internal_call.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
dll.il2cpp_add_internal_call.restype = None

@ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
def dummy_log(logType, logOption, msg_str, obj):
    pass
dll.dummy_log_ref = dummy_log
dummy_func_ptr = ctypes.cast(dummy_log, ctypes.c_void_p)
log_icalls = [
    b'UnityEngine.DebugLogHandler::Internal_Log(UnityEngine.LogType,UnityEngine.LogOption,System.String,UnityEngine.Object)',
    b'UnityEngine.DebugLogHandler::Internal_LogException(System.Exception,UnityEngine.Object)',
    b'UnityEngine.Debug::Log(System.Object)',
    b'UnityEngine.Debug::LogError(System.Object)',
    b'UnityEngine.Debug::LogWarning(System.Object)',
]
for icall in log_icalls:
    dll.il2cpp_add_internal_call(icall, dummy_func_ptr)

domain = dll.il2cpp_init(b'StellaSora')

dll_base = dll._handle

init_cls_fn = ctypes.CFUNCTYPE(None, ctypes.c_void_p)(dll_base + 0x608250)
class_slot = dll_base + 0x71d7238
init_cls_fn(class_slot)
class_ptr = ctypes.c_void_p.from_address(class_slot).value

dll.il2cpp_class_get_methods.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
dll.il2cpp_class_get_methods.restype = ctypes.c_void_p
dll.il2cpp_method_get_name.argtypes = [ctypes.c_void_p]
dll.il2cpp_method_get_name.restype = ctypes.c_char_p
dll.il2cpp_runtime_invoke.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p)]
dll.il2cpp_runtime_invoke.restype = ctypes.c_void_p
dll.il2cpp_string_chars.argtypes = [ctypes.c_void_p]
dll.il2cpp_string_chars.restype = ctypes.c_void_p
dll.il2cpp_string_length.argtypes = [ctypes.c_void_p]
dll.il2cpp_string_length.restype = ctypes.c_int32
dll.il2cpp_array_length.argtypes = [ctypes.c_void_p]
dll.il2cpp_array_length.restype = ctypes.c_uint32

mit = ctypes.c_void_p(0)
get_ck_mth = None
dt_mth = None
while True:
    m = dll.il2cpp_class_get_methods(class_ptr, ctypes.byref(mit))
    if not m:
        break
    mname = dll.il2cpp_method_get_name(m).decode('utf-8')
    if mname == 'get___CK':
        get_ck_mth = m
    elif mname == 'DT':
        dt_mth = m

exc = ctypes.c_void_p(0)
res_obj = dll.il2cpp_runtime_invoke(get_ck_mth, None, None, ctypes.byref(exc))
print('res_obj:', hex(res_obj) if res_obj else 'NULL', 'exc:', hex(exc.value) if exc.value else 'None')

if res_obj:
    try:
        slen = dll.il2cpp_string_length(res_obj)
        chars = dll.il2cpp_string_chars(res_obj)
        sval = ctypes.string_at(chars, slen * 2).decode('utf-16')
        print(f'___CK as String: {sval!r}')
    except Exception as e:
        print('String err:', e)

    try:
        alen = dll.il2cpp_array_length(res_obj)
        raw_b = ctypes.string_at(res_obj + 0x20, alen)
        print(f'___CK as Array ({alen} bytes): {raw_b}')
        print(f'___CK Hex: {raw_b.hex(" ")}')
    except Exception as e:
        print('Array err:', e)
