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

dll_base = ctypes.cast(dll.il2cpp_init, ctypes.c_void_p).value - 0x60ff20

# Call 0x1068290: returns uint32[] or byte[] or string?
KEY_FN = ctypes.CFUNCTYPE(ctypes.c_void_p)
get_key_fn = KEY_FN(dll_base + 0x1068290)

key_obj = get_key_fn()
print(f'Key object pointer: 0x{key_obj:x}')

dll.il2cpp_array_length.argtypes = [ctypes.c_void_p]
dll.il2cpp_array_length.restype = ctypes.c_uint32

try:
    alen = dll.il2cpp_array_length(key_obj)
    raw_data = ctypes.string_at(key_obj + 0x20, alen)
    print(f'Array length: {alen}')
    print(f'Raw bytes: {raw_data}')
    print(f'Hex: {raw_data.hex(" ")}')
except Exception as e:
    print('Error reading as array:', e)

try:
    dll.il2cpp_string_chars.argtypes = [ctypes.c_void_p]
    dll.il2cpp_string_chars.restype = ctypes.c_void_p
    dll.il2cpp_string_length.argtypes = [ctypes.c_void_p]
    dll.il2cpp_string_length.restype = ctypes.c_int32
    slen = dll.il2cpp_string_length(key_obj)
    chars = dll.il2cpp_string_chars(key_obj)
    sval = ctypes.string_at(chars, slen * 2).decode('utf-16')
    print(f'String val: {sval}')
except Exception as e:
    print('Error reading as string:', e)
