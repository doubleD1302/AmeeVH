import {createHash} from 'node:crypto';
import {readFile, writeFile} from 'node:fs/promises';
import {join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const root = resolve(fileURLToPath(new URL('../web/story_translator/data/', import.meta.url)));
const output = join(root, 'dataset-manifest.json');
const args = process.argv.slice(2);
const mode = args[0];
const version = args[1];
if (!['--write', '--check'].includes(mode) || !version || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$/.test(version)) {
    console.error('Usage: node tools/build_tramvh_dataset_manifest.mjs --write|--check <dataset-version>');
    process.exit(2);
}
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const indexBytes = await readFile(join(root, 'chapters.json'));
const chapters = JSON.parse(indexBytes.toString('utf8'));
if (!Array.isArray(chapters) || !chapters.length) throw Error('Danh sách chương trống.');
const files = [{path:'chapters.json',bytes:indexBytes.length,sha256:digest(indexBytes)}];
const chapterIds = new Set();
let totalLines = 0;
for (const entry of chapters) {
    const id = entry?.id;
    if (typeof id !== 'string' || !/^[A-Za-z0-9_]+$/.test(id) || chapterIds.has(id)) throw Error('ID chương trùng hoặc không hợp lệ: ' + id);
    chapterIds.add(id);
    const path = `chapters/${id}.json`;
    const bytes = await readFile(join(root, path));
    const chapter = JSON.parse(bytes.toString('utf8'));
    if (chapter.chapter_id !== id || !Array.isArray(chapter.scenes)) throw Error('Cấu trúc chương không khớp: ' + id);
    const lineIds = new Set();
    let lineCount = 0;
    for (const scene of chapter.scenes) {
        if (!Array.isArray(scene.lines)) throw Error('Màn không có danh sách câu: ' + id);
        for (const line of scene.lines) {
            const lineId = String(line.line_id || '');
            if (!lineId || lineIds.has(lineId) || typeof line.en !== 'string') throw Error('Câu trùng ID, thiếu ID hoặc thiếu EN: ' + id + '/' + lineId);
            lineIds.add(lineId);
            lineCount++;
        }
    }
    if (entry.total_lines !== lineCount) throw Error('Tổng số câu trong chỉ mục không khớp: ' + id);
    files.push({path,bytes:bytes.length,sha256:digest(bytes),lines:lineCount});
    totalLines += lineCount;
}
const payload = {schema:1,version,files};
const manifest = {...payload,hash:digest(JSON.stringify(payload)),chapters:chapters.length,lines:totalLines};
const serialized = JSON.stringify(manifest,null,2) + '\n';
if (mode === '--write') {
    await writeFile(output, serialized);
    console.log(`Đã ghi ${output}: ${version}, ${chapters.length} chương, ${totalLines} câu, SHA-256 ${manifest.hash}`);
} else {
    const existing = await readFile(output,'utf8');
    if (existing !== serialized) throw Error('Manifest không khớp dữ liệu nguồn hoặc phiên yêu cầu.');
    console.log(`Manifest hợp lệ: ${version}, ${chapters.length} chương, ${totalLines} câu, SHA-256 ${manifest.hash}`);
}
