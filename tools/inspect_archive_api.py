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
dll.il2cpp_method_get_param_count.argtypes = [ctypes.c_void_p]
dll.il2cpp_method_get_param_count.restype = ctypes.c_uint32
dll.il2cpp_method_get_param_name.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
dll.il2cpp_method_get_param_name.restype = ctypes.c_char_p

size = ctypes.c_size_t(0)
assemblies = dll.il2cpp_domain_get_assemblies(domain, ctypes.byref(size))
for i in range(size.value):
    asm = assemblies[i]
    img = dll.il2cpp_assembly_get_image(asm)
    if dll.il2cpp_image_get_name(img).decode('utf-8') == 'GameFramework.dll':
        for c in range(dll.il2cpp_image_get_class_count(img)):
            cls = dll.il2cpp_image_get_class(img, c)
            cname = dll.il2cpp_class_get_name(cls).decode('utf-8')
            if cname in ('Archive', 'ArchiveEntry', 'ArchiveUtil', 'ArchiveHeader'):
                print(f'=== Class: {cname} ===')
                it = ctypes.c_void_p(0)
                while True:
                    m = dll.il2cpp_class_get_methods(cls, ctypes.byref(it))
                    if not m:
                        break
                    mname = dll.il2cpp_method_get_name(m).decode('utf-8')
                    pcount = dll.il2cpp_method_get_param_count(m)
                    pnames = [dll.il2cpp_method_get_param_name(m, p).decode('utf-8') for p in range(pcount)]
                    param_str = ', '.join(pnames)
                    print(f'  {mname}({param_str})')
