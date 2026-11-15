'use strict';
// Trích văn bản tiếng Việt đang dùng trong game từ dist/lua_patched_vi.arcx và dist/data_patched_vi.arcx
// của dự án patch AmeeVH. Dùng module đọc arcx/Lua 5.3 có sẵn của dự án đó.
//
//   node extract_patched_vi.cjs <patch-root> <out-dir>
//
// Ghi vào <out-dir>: scenes.jsonl (cảnh AVG), presets.json (tên người nói, danh bạ), tables.jsonl (bảng text), meta.json (hash gói).
// Chỉ đọc gói, không sửa gì trong dự án patch.
const fs = require('node:fs');
const path = require('node:path');

const [patchRoot, outDir] = process.argv.slice(2).map(p => p && path.resolve(p));
if (!patchRoot || !outDir) { console.error('Dùng: node extract_patched_vi.cjs <patch-root> <out-dir>'); process.exit(2); }
const io = require(path.join(patchRoot, 'tools', 'language_resource_io_20261031.cjs'));
const TEXT_CMDS = new Set(['SetIntro', 'SetTalk', 'SetPhoneMsg', 'SetBubble', 'SetSceneHeading', 'SetChoiceBegin',
  'SetPhoneMsgChoiceBegin', 'SetPersonalityChoice', 'SetTrans']);

fs.mkdirSync(outDir, { recursive: true });
const meta = { archives: {} };

function openArchive(name) {
  const file = path.join(patchRoot, 'dist', name);
  if (!fs.existsSync(file)) return null;
  const archive = io.readArchive(file);
  meta.archives[name] = { sha256: archive.sha256, entries: archive.entries.length };
  return archive;
}

// --- Lua: cảnh AVG
const lua = openArchive('lua_patched_vi.arcx');
const scenes = fs.createWriteStream(path.join(outDir, 'scenes.jsonl'));
let sceneCount = 0, sceneSkipped = 0;
const presets = {};
if (lua) {
  for (const entry of lua.entries) {
    const bytes = io.xxteaDecrypt(lua.extract(entry));
    if (!bytes.subarray(0, 4).equals(Buffer.from([27, 76, 117, 97]))) continue;
    let parsed;
    try { parsed = io.parseLua53(bytes); } catch { continue; }
    const source = String(parsed.source ?? '').replaceAll('\\', '/');
    const preset = /\/Avg\/(?:_[^/]+\/)?Preset\/(AvgCharacter|AvgContacts)\.lua$/i.exec(source);
    if (preset) {
      try { presets[preset[1]] = io.literalLuaTable(parsed); } catch { /* bỏ qua preset không đọc được */ }
      continue;
    }
    if (!/\/Avg\/(?:_[^/]+\/)?Config\//i.test(source)) continue;
    let table;
    try { table = io.literalLuaTable(parsed); } catch { sceneSkipped++; continue; }
    const commands = (table && table.commands) || (Array.isArray(table) ? table : []);
    const kept = [];
    commands.forEach((c, i) => { if (c && TEXT_CMDS.has(c.cmd)) kept.push([i, c.cmd, c.param]); });
    const scene = path.posix.basename(source, '.lua');
    scenes.write(JSON.stringify({ scene, hash: entry.hash_hex, source, commands: kept }) + '\n');
    sceneCount++;
  }
}
scenes.end();
fs.writeFileSync(path.join(outDir, 'presets.json'), JSON.stringify(presets));

// --- Data: bảng text (JSON)
const data = openArchive('data_patched_vi.arcx');
const tables = fs.createWriteStream(path.join(outDir, 'tables.jsonl'));
let tableCount = 0;
if (data) {
  for (const entry of data.entries) {
    const bytes = io.xxteaDecrypt(data.extract(entry));
    let value;
    try { value = JSON.parse(io.utf8(bytes).replace(/^﻿/, '')); } catch { continue; }
    if (!value || typeof value !== 'object' || Array.isArray(value)) continue;
    const keys = Object.keys(value);
    if (!keys.length) continue;
    const first = keys[0];
    const name = first.includes('.') ? first.split('.')[0] : null;
    tables.write(JSON.stringify({ hash: entry.hash_hex, name, data: value }) + '\n');
    tableCount++;
  }
}
tables.end();

meta.scenes = sceneCount; meta.scenes_skipped = sceneSkipped; meta.tables = tableCount;
fs.writeFileSync(path.join(outDir, 'meta.json'), JSON.stringify(meta, null, 2));
console.log(`scenes=${sceneCount} (bỏ ${sceneSkipped}) tables=${tableCount}`);
