import struct
from pathlib import Path

class Lua53Chunk:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def read_bytes(self, n: int) -> bytes:
        res = self.data[self.pos : self.pos + n]
        self.pos += n
        return res
    def read_byte(self) -> int: return self.read_bytes(1)[0]
    def read_int(self) -> int: return struct.unpack('<i', self.read_bytes(4))[0]
    def read_size_t(self) -> int: return struct.unpack('<Q', self.read_bytes(8))[0]
    def read_string(self) -> tuple[int, bytes]:
        size = self.read_byte()
        if size == 0: return (0, b'')
        str_len = self.read_size_t() if size == 0xFF else size
        return (size, self.read_bytes(str_len - 1))

    def parse_proto(self):
        src = self.read_string()
        linedefined = self.read_int()
        lastlinedefined = self.read_int()
        numparams = self.read_byte()
        is_vararg = self.read_byte()
        maxstacksize = self.read_byte()
        sizecode = self.read_int()
        code = self.read_bytes(sizecode * 4)
        sizek = self.read_int()
        constants = []
        for i in range(sizek):
            ktype = self.read_byte()
            if ktype == 0: val = None
            elif ktype == 1: val = self.read_byte()
            elif ktype in (3, 19): val = self.read_bytes(8)
            elif ktype in (4, 20): val = self.read_string()
            constants.append((ktype, val))
        sizeup = self.read_int()
        upvals = self.read_bytes(sizeup * 2)
        sizep = self.read_int()
        protos = [self.parse_proto() for _ in range(sizep)]
        sizeline = self.read_int()
        lineinfo = self.read_bytes(sizeline * 4)
        sizeloc = self.read_int()
        locvars = []
        for _ in range(sizeloc):
            vname = self.read_string()
            spc = self.read_int()
            epc = self.read_int()
            locvars.append((vname, spc, epc))
        sizeupvalnames = self.read_int()
        upvalnames = [self.read_string() for _ in range(sizeupvalnames)]
        return {
            'src': src, 'linedefined': linedefined, 'lastlinedefined': lastlinedefined,
            'numparams': numparams, 'is_vararg': is_vararg, 'maxstacksize': maxstacksize,
            'sizecode': sizecode, 'code': code, 'constants': constants,
            'sizeup': sizeup, 'upvals': upvals, 'protos': protos,
            'sizeline': sizeline, 'lineinfo': lineinfo,
            'locvars': locvars, 'upvalnames': upvalnames
        }

def serialize_string(tag: int, s_bytes: bytes) -> bytes:
    if tag == 0:
        return b'\x00'
    if not s_bytes and tag == 1:
        return b'\x01'
    slen = len(s_bytes) + 1
    if tag == 0xFF or slen >= 0xFF:
        return b'\xFF' + struct.pack('<Q', slen) + s_bytes
    else:
        return bytes([slen]) + s_bytes

def serialize_proto(proto: dict) -> bytes:
    out = bytearray()
    out += serialize_string(*proto['src'])
    out += struct.pack('<iiBBB', proto['linedefined'], proto['lastlinedefined'],
                       proto['numparams'], proto['is_vararg'], proto['maxstacksize'])
    out += struct.pack('<i', proto['sizecode'])
    out += proto['code']
    out += struct.pack('<i', len(proto['constants']))
    for ktype, val in proto['constants']:
        out.append(ktype)
        if ktype == 0: pass
        elif ktype == 1: out.append(val)
        elif ktype in (3, 19): out += val
        elif ktype in (4, 20): out += serialize_string(*val)
    out += struct.pack('<i', proto['sizeup'])
    out += proto['upvals']
    out += struct.pack('<i', len(proto['protos']))
    for p in proto['protos']:
        out += serialize_proto(p)
    out += struct.pack('<i', proto['sizeline'])
    out += proto['lineinfo']
    out += struct.pack('<i', len(proto['locvars']))
    for vname, spc, epc in proto['locvars']:
        out += serialize_string(*vname)
        out += struct.pack('<ii', spc, epc)
    out += struct.pack('<i', len(proto['upvalnames']))
    for uname in proto['upvalnames']:
        out += serialize_string(*uname)
    return bytes(out)

def test_file(p_path):
    raw_orig = p_path.read_bytes()
    p = Lua53Chunk(raw_orig)
    hdr = p.read_bytes(33)
    size_up = p.read_byte()
    proto = p.parse_proto()
    raw_rebuilt = hdr + bytes([size_up]) + serialize_proto(proto)
    if raw_orig == raw_rebuilt:
        return True
    diffs = [i for i in range(min(len(raw_orig), len(raw_rebuilt))) if raw_orig[i] != raw_rebuilt[i]]
    print(f"Diff in {p_path.name}: len_orig={len(raw_orig)}, len_rebuilt={len(raw_rebuilt)}, diff_count={len(diffs)}")
    for d in diffs[:3]:
        print(f"  Pos {d}: orig={hex(raw_orig[d])}, rebuilt={hex(raw_rebuilt[d])}")
    return False

if __name__ == '__main__':
    root = Path(r'c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\lua_tree\Game\UI\Avg\_en\Config')
    samples = ['BBm00_01.lua', 'PM10301.lua', 'STm01_01.lua']
    for s in samples:
        res = test_file(root / s)
        print(f"{s}: 100% exact match = {res}")
