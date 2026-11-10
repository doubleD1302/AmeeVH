// Create an uncompressed ZIP from the exact bytes returned by the server.
const encoder = new TextEncoder();
function crc32(bytes) {
    let crc = 0xffffffff;
    for (const byte of bytes) {
        crc ^= byte;
        for (let bit = 0; bit < 8; bit++) crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
    }
    return (crc ^ 0xffffffff) >>> 0;
}
export function isSafeArchivePath(name) {
    return typeof name === 'string' && name.length > 0 && name.length <= 240 && name.split('/').every(part => /^[A-Za-z0-9._-]+$/.test(part) && part !== '.' && part !== '..');
}
export function createZip(files) {
    const local = [], central = []; let offset = 0;
    for (const { name, bytes } of files) {
        if (!isSafeArchivePath(name) || !(bytes instanceof Uint8Array)) throw new Error('Tên hoặc dữ liệu tệp không hợp lệ.');
        const encoded = encoder.encode(name), crc = crc32(bytes);
        const head = new Uint8Array(30 + encoded.length), h = new DataView(head.buffer);
        h.setUint32(0, 0x04034b50, true); h.setUint16(4, 20, true); h.setUint16(6, 0x0800, true);
        h.setUint32(14, crc, true); h.setUint32(18, bytes.length, true); h.setUint32(22, bytes.length, true); h.setUint16(26, encoded.length, true); head.set(encoded, 30);
        const entry = new Uint8Array(46 + encoded.length), e = new DataView(entry.buffer);
        e.setUint32(0, 0x02014b50, true); e.setUint16(4, 20, true); e.setUint16(6, 20, true); e.setUint16(8, 0x0800, true);
        e.setUint32(16, crc, true); e.setUint32(20, bytes.length, true); e.setUint32(24, bytes.length, true); e.setUint16(28, encoded.length, true); e.setUint32(42, offset, true); entry.set(encoded, 46);
        local.push(head, bytes); central.push(entry); offset += head.length + bytes.length;
    }
    const centralSize = central.reduce((total, entry) => total + entry.length, 0), end = new Uint8Array(22), e = new DataView(end.buffer);
    e.setUint32(0, 0x06054b50, true); e.setUint16(8, files.length, true); e.setUint16(10, files.length, true); e.setUint32(12, centralSize, true); e.setUint32(16, offset, true);
    return new Blob([...local, ...central, end], { type: 'application/zip' });
}
