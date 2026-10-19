import os
import sys
import ctypes
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
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
dll.il2cpp_class_get_methods.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
dll.il2cpp_class_get_methods.restype = ctypes.c_void_p
dll.il2cpp_method_get_name.argtypes = [ctypes.c_void_p]
dll.il2cpp_method_get_name.restype = ctypes.c_char_p
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
    for c in range(dll.il2cpp_image_get_class_count(img)):
        cls = dll.il2cpp_image_get_class(img, c)
        if dll.il2cpp_class_get_name(cls).decode('utf-8') == 'Archive':
            archive_cls = cls

it = ctypes.c_void_p(0)
open_mth = None
read_file_name_mth = None
while True:
    m = dll.il2cpp_class_get_methods(archive_cls, ctypes.byref(it))
    if not m:
        break
    mname = dll.il2cpp_method_get_name(m).decode('utf-8')
    if mname == 'Open':
        open_mth = m
    elif mname == 'ReadFile':
        pname = dll.il2cpp_method_get_param_name(m, 0).decode('utf-8')
        if pname == 'fileName':
            read_file_name_mth = m

repack_path = r'C:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\data_repacked_test.arcx'
s_arg = dll.il2cpp_string_new(repack_path.encode('utf-8'))
args = (ctypes.c_void_p * 1)(s_arg)
exc = ctypes.c_void_p(0)
arc_obj = dll.il2cpp_runtime_invoke(open_mth, None, args, ctypes.byref(exc))
print('Native Archive.Open:', hex(arc_obj) if arc_obj else 'NULL')

fname_arg = dll.il2cpp_string_new(b'bin/Skill.bytes')
args2 = (ctypes.c_void_p * 1)(fname_arg)
data_arr = dll.il2cpp_runtime_invoke(read_file_name_mth, arc_obj, args2, ctypes.byref(exc))
print('Native Archive.ReadFile:', hex(data_arr) if data_arr else 'NULL', 'Exc:', hex(exc.value) if exc.value else 'None')

if data_arr:
    dlen = dll.il2cpp_array_length(data_arr)
    data = ctypes.string_at(data_arr + 0x20, dlen)
    print(f'SUCCESS! Read {dlen} bytes for bin/Skill.bytes from repacked archive!')
    
    from tools.test_pure_xxtea import xxtea_decrypt
    KEY = bytes.fromhex('a9 21 a4 67 c7 d7 df 39 6e 60 90 9c 31 22 5b d2')
    dec = xxtea_decrypt(data, KEY)
    print(f'Decrypted length: {len(dec)} bytes')
    print('Payload text preview:', dec[:80])
    if b'Skill' in dec:
        print('VERIFIED! Native engine loaded bin/Skill.bytes successfully!')
