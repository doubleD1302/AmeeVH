import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
const source = await readFile(new URL('../web/story_translator/js/handoff-zip.js', import.meta.url), 'utf8');
const { createZip } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
test('ZIP giữ nguyên byte, tên tệp và CRC của từng tệp', async () => {
    const files = [{ name: 'manifest.json', bytes: new TextEncoder().encode('123456789') }, { name: 'changes.jsonl', bytes: new TextEncoder().encode('Tiếng Việt\n') }];
    const data = new Uint8Array(await createZip(files).arrayBuffer());
    const view = new DataView(data.buffer); let offset = 0;
    for (const [index, file] of files.entries()) {
        assert.equal(view.getUint32(offset, true), 0x04034b50);
        const size = view.getUint32(offset + 18, true), nameLen = view.getUint16(offset + 26, true);
        assert.equal(new TextDecoder().decode(data.slice(offset + 30, offset + 30 + nameLen)), file.name);
        assert.deepEqual(data.slice(offset + 30 + nameLen, offset + 30 + nameLen + size), file.bytes);
        if (index === 0) assert.equal(view.getUint32(offset + 14, true), 0xcbf43926);
        offset += 30 + nameLen + size;
    }
    assert.equal(view.getUint32(offset, true), 0x02014b50);
    assert.equal(view.getUint32(data.length - 22, true), 0x06054b50);
    assert.equal(view.getUint16(data.length - 12, true), files.length);
});
test('không cho ghi đường dẫn ra ngoài gói', () => {
    assert.throws(() => createZip([{ name: '../file', bytes: new Uint8Array() }]));
});
