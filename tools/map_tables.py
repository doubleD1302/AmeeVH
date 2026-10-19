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
dll.il2cpp_runtime_invoke.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p)]
dll.il2cpp_runtime_invoke.restype = ctypes.c_void_p
dll.il2cpp_string_new.argtypes = [ctypes.c_char_p]
dll.il2cpp_string_new.restype = ctypes.c_void_p

size = ctypes.c_size_t(0)
assemblies = dll.il2cpp_domain_get_assemblies(domain, ctypes.byref(size))
gdc_cls = None
util_cls = None
for i in range(size.value):
    asm = assemblies[i]
    img = dll.il2cpp_assembly_get_image(asm)
    iname = dll.il2cpp_image_get_name(img).decode('utf-8')
    ccount = dll.il2cpp_image_get_class_count(img)
    for c in range(ccount):
        cls = dll.il2cpp_image_get_class(img, c)
        cname = dll.il2cpp_class_get_name(cls).decode('utf-8')
        if iname == 'Game.dll' and cname == 'GameDataController':
            gdc_cls = cls
        elif iname == 'GameFramework.dll' and cname == 'ArchiveUtil':
            util_cls = cls

it = ctypes.c_void_p(0)
xxhash_mth = None
norm_mth = None
while True:
    m = dll.il2cpp_class_get_methods(util_cls, ctypes.byref(it))
    if not m:
        break
    mname = dll.il2cpp_method_get_name(m).decode('utf-8')
    if mname == 'XXHash64':
        xxhash_mth = m
    elif mname == 'NormalizeFileName':
        norm_mth = m

def hash_str(s):
    s_obj = dll.il2cpp_string_new(s.encode('utf-8'))
    args = (ctypes.c_void_p * 1)(s_obj)
    exc = ctypes.c_void_p(0)
    norm_obj = dll.il2cpp_runtime_invoke(norm_mth, None, args, ctypes.byref(exc))
    args2 = (ctypes.c_void_p * 1)(norm_obj)
    res_obj = dll.il2cpp_runtime_invoke(xxhash_mth, None, args2, ctypes.byref(exc))
    val = ctypes.c_uint64.from_address(res_obj + 0x10).value if res_obj else 0
    return val

manifest = json.load(open(r'C:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\unpacked_data\manifest.json'))
data_hashes = {e['hash']: e['filename'] for e in manifest['entries']}

# Get all Load*Bin method names from GameDataController
mit = ctypes.c_void_p(0)
bin_methods = []
while True:
    m = dll.il2cpp_class_get_methods(gdc_cls, ctypes.byref(mit))
    if not m:
        break
    mname = dll.il2cpp_method_get_name(m).decode('utf-8')
    if mname.startswith('Load') and mname.endswith('Bin'):
        table_base = mname[4:-3] # e.g. LoadSkillBin -> Skill
        bin_methods.append(table_base)

print(f'Total Load*Bin tables identified in GameDataController: {len(bin_methods)}')

matched = {}
for tname in bin_methods:
    candidates = [
        f'bin/{tname}.bytes',
        f'bin/{tname.lower()}.bytes',
        f'{tname}.bytes',
        f'{tname.lower()}.bytes',
    ]
    for c in candidates:
        h = hash_str(c)
        if h in data_hashes:
            matched[c] = (h, data_hashes[h])
            break

print(f'Successfully mapped {len(matched)} / {len(bin_methods)} tables to entries in data.arcx!')
for name, (h, fname) in sorted(matched.items())[:30]:
    print(f'  {name:<35} -> 0x{h:016x} -> {fname}')

# Save table catalog mapping
catalog = {name: {'hash': h, 'hash_hex': f'0x{h:016x}', 'entry_file': fname} for name, (h, fname) in matched.items()}
cat_path = Path(r'C:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\table_catalog.json')
cat_path.write_text(json.dumps(catalog, indent=2), encoding='utf-8')
print(f'Catalog saved to {cat_path}')
