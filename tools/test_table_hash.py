import json
import ctypes
from pathlib import Path

GAME_DIR = Path(r'c:\YostarGames\StellaSora_EN')
dll = ctypes.CDLL(str(GAME_DIR / 'GameAssembly.dll'))
dll.il2cpp_set_data_dir(str(GAME_DIR / 'StellaSora_Data' / 'il2cpp_data').encode('utf-8'))
domain = dll.il2cpp_init(b'StellaSora')

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
util_cls = None
for i in range(size.value):
    asm = assemblies[i]
    img = dll.il2cpp_assembly_get_image(asm)
    if dll.il2cpp_image_get_name(img).decode('utf-8') == 'GameFramework.dll':
        for c in range(dll.il2cpp_image_get_class_count(img)):
            cls = dll.il2cpp_image_get_class(img, c)
            if dll.il2cpp_class_get_name(cls).decode('utf-8') == 'ArchiveUtil':
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

manifest = json.load(open('work/research/unpacked_data/manifest.json'))
data_hashes = {e['hash']: e['filename'] for e in manifest['entries']}

candidates = [
    'bin/Skill.bytes',
    'bin/skill.bytes',
    'Skill.bytes',
    'Skill',
    'skill',
    'Tables/bin/Skill.bytes',
    'tables/bin/skill.bytes',
]

for c in candidates:
    h = hash_str(c)
    found = c in data_hashes or h in data_hashes
    print(f'{c:<30} -> 0x{h:016x} | Match: {found}')
    if found:
        print(f'   MATCH: {data_hashes.get(h)}')
