import os
import ctypes
import json
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
dll.il2cpp_array_length.argtypes = [ctypes.c_void_p]
dll.il2cpp_array_length.restype = ctypes.c_uint32
dll.il2cpp_array_new.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
dll.il2cpp_array_new.restype = ctypes.c_void_p

# Find byte class in mscorlib
dll.il2cpp_domain_get_assemblies.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t)]
dll.il2cpp_domain_get_assemblies.restype = ctypes.POINTER(ctypes.c_void_p)
dll.il2cpp_assembly_get_image.argtypes = [ctypes.c_void_p]
dll.il2cpp_assembly_get_image.restype = ctypes.c_void_p
dll.il2cpp_image_get_class_count.argtypes = [ctypes.c_void_p]
dll.il2cpp_image_get_class_count.restype = ctypes.c_size_t
dll.il2cpp_image_get_class.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
dll.il2cpp_image_get_class.restype = ctypes.c_void_p
dll.il2cpp_class_get_name.argtypes = [ctypes.c_void_p]
dll.il2cpp_class_get_name.restype = ctypes.c_char_p
dll.il2cpp_image_get_name.argtypes = [ctypes.c_void_p]
dll.il2cpp_image_get_name.restype = ctypes.c_char_p

size = ctypes.c_size_t(0)
assemblies = dll.il2cpp_domain_get_assemblies(domain, ctypes.byref(size))
byte_cls = None
for i in range(size.value):
    asm = assemblies[i]
    img = dll.il2cpp_assembly_get_image(asm)
    if dll.il2cpp_image_get_name(img).decode('utf-8') == 'mscorlib.dll':
        for c in range(dll.il2cpp_image_get_class_count(img)):
            cls = dll.il2cpp_image_get_class(img, c)
            if dll.il2cpp_class_get_name(cls).decode('utf-8') == 'Byte':
                byte_cls = cls

mit = ctypes.c_void_p(0)
dt_mth = None
da_mth = None
while True:
    m = dll.il2cpp_class_get_methods(class_ptr, ctypes.byref(mit))
    if not m:
        break
    mname = dll.il2cpp_method_get_name(m).decode('utf-8')
    if mname == 'DT':
        dt_mth = m
    elif mname == 'DA':
        da_mth = m

# Read unpacked bin/Skill.bytes (00322_0x3bbee732bf6a65f9.bin)
skill_path = Path(r'C:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\unpacked_data\entries\00322_0x3bbee732bf6a65f9.bin')
raw_skill = skill_path.read_bytes()
print(f'Encrypted Skill.bytes length: {len(raw_skill)}')

# Create C# byte array
arr = dll.il2cpp_array_new(byte_cls, len(raw_skill))
ctypes.memmove(arr + 0x20, raw_skill, len(raw_skill))

dll.il2cpp_string_chars.argtypes = [ctypes.c_void_p]
dll.il2cpp_string_chars.restype = ctypes.c_void_p
dll.il2cpp_string_length.argtypes = [ctypes.c_void_p]
dll.il2cpp_string_length.restype = ctypes.c_int32

# Test DT (Decrypt to String)
args = (ctypes.c_void_p * 1)(arr)
exc = ctypes.c_void_p(0)
res_str = dll.il2cpp_runtime_invoke(dt_mth, None, args, ctypes.byref(exc))

if res_str:
    slen = dll.il2cpp_string_length(res_str)
    chars = dll.il2cpp_string_chars(res_str)
    text = ctypes.string_at(chars, slen * 2).decode('utf-16', errors='replace')
    print(f'DT SUCCESS! String length: {slen} characters')
    print(f'Preview (first 200 chars): {text[:200]}')
    out_txt = Path(r'C:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\decrypted_Skill.txt')
    out_txt.write_text(text, encoding='utf-8')
    print(f'Saved to {out_txt}')
else:
    print('DT Failed! Exc:', exc.value)

# Test DA (Decrypt to Byte Array)
arr2 = dll.il2cpp_array_new(byte_cls, len(raw_skill))
ctypes.memmove(arr2 + 0x20, raw_skill, len(raw_skill))
args2 = (ctypes.c_void_p * 1)(arr2)
exc = ctypes.c_void_p(0)
res_bytes = dll.il2cpp_runtime_invoke(da_mth, None, args2, ctypes.byref(exc))

if res_bytes:
    blen = dll.il2cpp_array_length(res_bytes)
    dec_b = ctypes.string_at(res_bytes + 0x20, blen)
    print(f'DA SUCCESS! Byte length: {blen} bytes')
    print(f'Hex preview: {dec_b[:32].hex(" ")}')
    out_bin = Path(r'C:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\decrypted_Skill.bin')
    out_bin.write_bytes(dec_b)
    print(f'Saved to {out_bin}')
else:
    print('DA Failed! Exc:', exc.value)
