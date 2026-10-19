import struct
from pathlib import Path

DELTA = 0x9E3779B9

def _to_uint32_array(data: bytes, include_length: bool = False) -> list[int]:
    length = len(data)
    n = (length + 3) // 4
    if include_length:
        arr = list(struct.unpack(f"<{n}I", data.ljust(n * 4, b"\x00")))
        arr.append(length)
        return arr
    else:
        return list(struct.unpack(f"<{n}I", data.ljust(n * 4, b"\x00")))

def _to_byte_array(v: list[int], include_length: bool = False) -> bytes:
    n = len(v)
    if include_length:
        length = v[-1]
        raw = struct.pack(f"<{n-1}I", *v[:-1])
        return raw[:length]
    else:
        return struct.pack(f"<{n}I", *v)

def _mx(z: int, y: int, sum_val: int, p: int, e: int, k: list[int]) -> int:
    term1 = (((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) & 0xFFFFFFFF
    term2 = ((sum_val ^ y) + (k[(p & 3) ^ e] ^ z)) & 0xFFFFFFFF
    return (term1 ^ term2) & 0xFFFFFFFF

def xxtea_decrypt(data: bytes, key: bytes) -> bytes:
    if not data:
        return b""
    k = list(struct.unpack("<4I", key))
    v = _to_uint32_array(data, include_length=False)
    n = len(v)
    if n <= 1:
        return data

    rounds = 6 + 52 // n
    sum_val = (rounds * DELTA) & 0xFFFFFFFF
    y = v[0]

    while sum_val != 0:
        e = (sum_val >> 2) & 3
        for p in range(n - 1, 0, -1):
            z = v[p - 1]
            v[p] = (v[p] - _mx(z, y, sum_val, p, e, k)) & 0xFFFFFFFF
            y = v[p]
        z = v[n - 1]
        v[0] = (v[0] - _mx(z, y, sum_val, 0, e, k)) & 0xFFFFFFFF
        y = v[0]
        sum_val = (sum_val - DELTA) & 0xFFFFFFFF

    # In Stella Sora AC.DA:
    # Look at how the original length is stored in the decrypted array:
    # Last word v[-1] contains the length of the payload!
    orig_len = v[-1]
    if (len(v) - 1) * 4 - 3 <= orig_len <= (len(v) - 1) * 4:
        raw = struct.pack(f"<{n-1}I", *v[:-1])
        return raw[:orig_len]
    return _to_byte_array(v, include_length=False)

def xxtea_encrypt(data: bytes, key: bytes) -> bytes:
    if not data:
        return b""
    k = list(struct.unpack("<4I", key))
    v = _to_uint32_array(data, include_length=True)
    n = len(v)
    if n <= 1:
        return data

    rounds = 6 + 52 // n
    sum_val = 0
    z = v[n - 1]

    for _ in range(rounds):
        sum_val = (sum_val + DELTA) & 0xFFFFFFFF
        e = (sum_val >> 2) & 3
        for p in range(n - 1):
            y = v[p + 1]
            v[p] = (v[p] + _mx(z, y, sum_val, p, e, k)) & 0xFFFFFFFF
            z = v[p]
        y = v[0]
        v[n - 1] = (v[n - 1] + _mx(z, y, sum_val, n - 1, e, k)) & 0xFFFFFFFF
        z = v[n - 1]

    return _to_byte_array(v, include_length=False)

def main():
    KEY = bytes.fromhex("a9 21 a4 67 c7 d7 df 39 6e 60 90 9c 31 22 5b d2")
    raw_lua = Path(r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\unpacked_lua\entries\00007_0x6d619c846dc084c6.bin").read_bytes()
    dec = xxtea_decrypt(raw_lua, KEY)
    print("Pure Python XXTEA Decrypt on main.lua:")
    print("  Decrypted length:", len(dec))
    print("  First 16 bytes hex:", dec[:16].hex(" "))
    print("  First 128 bytes text:", dec[:128])
    if dec.startswith(b"\x1bLua"):
        print("  VERIFIED! Valid Lua bytecode magic '\\x1bLua' detected!")

    enc = xxtea_encrypt(dec, KEY)
    print("Roundtrip Encrypt:")
    print("  Re-encrypted length:", len(enc), "Original length:", len(raw_lua))
    print("  Byte identical:", enc == raw_lua)

if __name__ == "__main__":
    main()
