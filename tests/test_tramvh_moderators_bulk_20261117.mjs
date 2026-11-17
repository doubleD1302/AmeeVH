// Tests for the per-person Moderator system and the Admin bulk approve endpoint.
import test from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {handleCollaboration} from '../web/story_translator/worker/collaboration.mjs';

class Bound {
 constructor(owner,sql,args=[]){Object.assign(this,{owner,sql,args});}
 bind(...args){return new Bound(this.owner,this.sql,args);}
 exec(){const results=this.owner.db.prepare(this.sql).all(...this.args);return {success:true,results,meta:{changes:Number(this.owner.db.prepare('SELECT changes() n').get().n)}};}
 async first(){return this.owner.db.prepare(this.sql).get(...this.args)||null;}
 async all(){return this.exec();}
 async run(){return this.exec();}
}
class D1 {
 constructor(){this.db=new DatabaseSync(':memory:');this.db.exec(readFileSync(new URL('../web/story_translator/worker/schema.sql',import.meta.url),'utf8'));}
 prepare(sql){return new Bound(this,sql);}
 async batch(statements){this.db.exec('BEGIN IMMEDIATE');try{const result=statements.map(s=>s.exec());this.db.exec('COMMIT');return result;}catch(e){this.db.exec('ROLLBACK');throw e;}}
 close(){this.db.close();}
}

const CH = 'Chuong_3_MainStory';
const KEY = 'private-review-code';
function makeEnv(scenes){
 const DB = new D1();
 const chapter = {chapter_id: CH, title: 'Test chapter', scenes};
 const env = {DB, REVIEWER_KEY: KEY, ASSETS: {async fetch(request){
  const path = new URL(request.url).pathname;
  if (path.endsWith('/chapters.json')) return new Response(JSON.stringify([{id: CH, total_lines: 1}]), {headers: {'Content-Type': 'application/json'}});
  return new Response(JSON.stringify(chapter), {headers: {'Content-Type': 'application/json'}});
 }}};
 return {env, chapter, close: () => DB.close()};
}
const oneLine = (extra = {}) => [{scene_id: 'S1', title: 'Scene 1', lines: [{line_id: 'line-1', en: 'Hello {0}', old_vi: '', new_vi: '', translator: '', status: 'Chờ dịch', notes: '', ...extra}]}];

async function api(env, method, path, {body, cookie, key, ip} = {}){
 const headers = {'Content-Type': 'application/json'};
 if (cookie) headers.Cookie = cookie;
 if (key) headers['X-Reviewer-Key'] = key;
 if (ip) headers['CF-Connecting-IP'] = ip;
 const response = await handleCollaboration(new Request('https://tramvh.test' + path, {method, headers, ...(body ? {body: JSON.stringify(body)} : {})}), env);
 return {status: response.status, body: await response.json(), setCookie: response.headers.get('Set-Cookie')};
}
async function newUser(env, name){
 const me = await api(env, 'GET', '/api/collab/me');
 assert.equal(me.status, 200);
 const cookie = me.setCookie.split(';')[0];
 if (name) {
  const profile = await api(env, 'POST', '/api/collab/profile', {body: {display_name: name}, cookie});
  assert.equal(profile.status, 200, JSON.stringify(profile.body));
 }
 return cookie;
}
const lineOf = async (env, cookie, id = 'line-1') => (await api(env, 'GET', `/api/collab/line?chapter_id=${CH}&line_id=${id}`, {cookie})).body.line;
const guarded = (line, extra = {}) => ({chapter_id: CH, line_id: line.line_id, base_revision: line.revision, base_source_hash: line.source_hash, base_dataset_version: line.dataset_version, request_id: crypto.randomUUID(), ...extra});
const submitBody = (line, text, extra = {}) => guarded(line, {text_vi: text, origin: 'human', notes: '', ...extra});
const createCode = async (env, label = 'Minh Trần') => {
 const created = await api(env, 'POST', '/api/admin/moderators', {body: {action: 'create', label}, key: KEY, cookie: await newUser(env, 'Admin')});
 assert.equal(created.status, 201, JSON.stringify(created.body));
 return created.body.data;
};
const adminCookie = async env => newUser(env, 'Admin');

test('Moderator code lifecycle: create, activate, bind to name, rename, deactivate', async () => {
 const f = makeEnv(oneLine());
 try {
  const {code, id, label} = await createCode(f.env);
  assert.match(code, /^[A-Z2-9]{5}(-[A-Z2-9]{5}){3}$/);
  assert.equal(label, 'Minh Trần');

  const admin = await adminCookie(f.env);
  const listed = await api(f.env, 'GET', '/api/admin/moderators', {key: KEY, cookie: admin});
  assert.equal(listed.status, 200);
  assert.equal(listed.body.data.items.length, 1);
  assert.equal(listed.body.data.items[0].code, code, 'admin can view the stored code');
  assert.equal(listed.body.data.items[0].devices, 0);
  assert.equal(listed.body.data.items[0].bound_name, null);
  assert.equal('code_cipher' in listed.body.data.items[0], false);

  const minh = await newUser(f.env, 'Minh');
  const before = await api(f.env, 'GET', '/api/collab/me', {cookie: minh});
  assert.equal(before.body.user.is_moderator, false);
  assert.equal('moderator_code_hash' in before.body.user, false);

  // wrong code
  const wrong = await api(f.env, 'POST', '/api/collab/moderator', {body: {action: 'activate', code: 'AAAAA-AAAAA-AAAAA-AAAAA'}, cookie: minh});
  assert.equal(wrong.status, 403);
  assert.equal(wrong.body.code, 'moderator_invalid');

  // typing the code in lower case without dashes still works
  const ok = await api(f.env, 'POST', '/api/collab/moderator', {body: {action: 'activate', code: code.replace(/-/g, ' ').toLowerCase()}, cookie: minh});
  assert.equal(ok.status, 200, JSON.stringify(ok.body));
  assert.equal(ok.body.user.is_moderator, true);
  assert.equal('moderator_code_hash' in ok.body.user, false);
  assert.equal((await api(f.env, 'GET', '/api/collab/me', {cookie: minh})).body.user.is_moderator, true);

  const bound = (await api(f.env, 'GET', '/api/admin/moderators', {key: KEY, cookie: admin})).body.data.items[0];
  assert.equal(bound.bound_name, 'Minh');
  assert.equal(bound.devices, 1);
  assert.ok(bound.claimed_at);
  assert.equal(bound.id, id);

  // another translator cannot use the same code under a different name
  const other = await newUser(f.env, 'Lan');
  const mismatch = await api(f.env, 'POST', '/api/collab/moderator', {body: {action: 'activate', code}, cookie: other});
  assert.equal(mismatch.status, 403);
  assert.equal(mismatch.body.code, 'moderator_name_mismatch');
  assert.equal((await api(f.env, 'GET', '/api/collab/me', {cookie: other})).body.user.is_moderator, false);

  // a second device with the same name works
  const phone = await newUser(f.env, ' MINH ');
  const second = await api(f.env, 'POST', '/api/collab/moderator', {body: {action: 'activate', code}, cookie: phone});
  assert.equal(second.status, 200, JSON.stringify(second.body));
  assert.equal((await api(f.env, 'GET', '/api/admin/moderators', {key: KEY, cookie: admin})).body.data.items[0].devices, 2);

  // renaming switches Moderator off; restoring the name switches it back on
  const renamed = await api(f.env, 'POST', '/api/collab/profile', {body: {display_name: 'Minh Khác'}, cookie: minh});
  assert.equal(renamed.body.user.is_moderator, false);
  const restored = await api(f.env, 'POST', '/api/collab/profile', {body: {display_name: 'minh'}, cookie: minh});
  assert.equal(restored.body.user.is_moderator, true);

  // deactivate affects only this device
  const off = await api(f.env, 'POST', '/api/collab/moderator', {body: {action: 'deactivate'}, cookie: minh});
  assert.equal(off.body.user.is_moderator, false);
  assert.equal((await api(f.env, 'GET', '/api/collab/me', {cookie: phone})).body.user.is_moderator, true);
 } finally { f.close(); }
});

test('Moderator activation refuses the default display name and unknown actions', async () => {
 const f = makeEnv(oneLine());
 try {
  const {code} = await createCode(f.env);
  const anonymous = await newUser(f.env);
  const refused = await api(f.env, 'POST', '/api/collab/moderator', {body: {action: 'activate', code}, cookie: anonymous});
  assert.equal(refused.status, 400);
  assert.equal(refused.body.code, 'name_required');
  const unknown = await api(f.env, 'POST', '/api/collab/moderator', {body: {action: 'promote'}, cookie: anonymous});
  assert.equal(unknown.status, 400);
 } finally { f.close(); }
});

test('Moderator code activation is throttled after repeated wrong codes', async () => {
 const f = makeEnv(oneLine());
 try {
  const {code} = await createCode(f.env);
  const minh = await newUser(f.env, 'Minh');
  for (let attempt = 0; attempt < 10; attempt++) {
   const wrong = await api(f.env, 'POST', '/api/collab/moderator', {body: {action: 'activate', code: 'WRONG-WRONG-WRONG-' + attempt}, cookie: minh, ip: '203.0.113.9'});
   assert.equal(wrong.status, 403);
  }
  const locked = await api(f.env, 'POST', '/api/collab/moderator', {body: {action: 'activate', code}, cookie: minh, ip: '203.0.113.9'});
  assert.equal(locked.status, 429);
  const elsewhere = await api(f.env, 'POST', '/api/collab/moderator', {body: {action: 'activate', code}, cookie: minh, ip: '203.0.113.10'});
  assert.equal(elsewhere.status, 200);
 } finally { f.close(); }
});

test('revoke and unlink remove access; an unlinked code can be claimed by another name', async () => {
 const f = makeEnv(oneLine());
 try {
  const {code, id} = await createCode(f.env);
  const admin = await adminCookie(f.env);
  const minh = await newUser(f.env, 'Minh');
  await api(f.env, 'POST', '/api/collab/moderator', {body: {action: 'activate', code}, cookie: minh});
  assert.equal((await api(f.env, 'GET', '/api/collab/me', {cookie: minh})).body.user.is_moderator, true);

  const unlinked = await api(f.env, 'POST', '/api/admin/moderators', {body: {action: 'unlink', id}, key: KEY, cookie: admin});
  assert.equal(unlinked.status, 200, JSON.stringify(unlinked.body));
  assert.equal((await api(f.env, 'GET', '/api/collab/me', {cookie: minh})).body.user.is_moderator, false);
  const item = (await api(f.env, 'GET', '/api/admin/moderators', {key: KEY, cookie: admin})).body.data.items[0];
  assert.equal(item.bound_name, null);
  assert.equal(item.devices, 0);

  const lan = await newUser(f.env, 'Lan');
  assert.equal((await api(f.env, 'POST', '/api/collab/moderator', {body: {action: 'activate', code}, cookie: lan})).status, 200);

  const revoked = await api(f.env, 'POST', '/api/admin/moderators', {body: {action: 'revoke', id}, key: KEY, cookie: admin});
  assert.equal(revoked.status, 200);
  assert.equal((await api(f.env, 'GET', '/api/collab/me', {cookie: lan})).body.user.is_moderator, false);
  const after = (await api(f.env, 'GET', '/api/admin/moderators', {key: KEY, cookie: admin})).body.data.items[0];
  assert.ok(after.revoked_at);
  assert.equal('code' in after, false, 'a revoked code is no longer shown');
  const reuse = await api(f.env, 'POST', '/api/collab/moderator', {body: {action: 'activate', code}, cookie: lan});
  assert.equal(reuse.status, 403);
  const unlinkRevoked = await api(f.env, 'POST', '/api/admin/moderators', {body: {action: 'unlink', id}, key: KEY, cookie: admin});
  assert.equal(unlinkRevoked.status, 409);
  const missing = await api(f.env, 'POST', '/api/admin/moderators', {body: {action: 'revoke', id: 'does-not-exist'}, key: KEY, cookie: admin});
  assert.equal(missing.status, 404);
 } finally { f.close(); }
});

test('Moderator admin endpoints and bulk approve require the reviewer key', async () => {
 const f = makeEnv(oneLine({new_vi: 'Xin chào {0}'}));
 try {
  const cookie = await newUser(f.env, 'Minh');
  assert.equal((await api(f.env, 'GET', '/api/admin/moderators', {cookie})).status, 403);
  assert.equal((await api(f.env, 'GET', '/api/admin/moderators', {cookie, key: 'wrong-key'})).status, 403);
  assert.equal((await api(f.env, 'POST', '/api/admin/moderators', {body: {action: 'create', label: 'X'}, cookie})).status, 403);
  assert.equal((await api(f.env, 'POST', '/api/admin/bulk_approve', {body: {chapter_id: CH, reason: 'x', dry_run: true}, cookie})).status, 403);
  assert.equal((await api(f.env, 'POST', '/api/admin/bulk_approve', {body: {chapter_id: CH, reason: 'x', dry_run: false}, cookie})).status, 403);
 } finally { f.close(); }
});

test('Moderator submissions are approved immediately and logged; others still queue', async () => {
 const f = makeEnv(oneLine());
 try {
  const {code} = await createCode(f.env);
  const minh = await newUser(f.env, 'Minh');
  const lan = await newUser(f.env, 'Lan');
  await api(f.env, 'POST', '/api/collab/moderator', {body: {action: 'activate', code}, cookie: minh});

  // first translation by a Moderator
  let line = await lineOf(f.env, minh);
  const saved = await api(f.env, 'POST', '/api/collab/submit', {body: submitBody(line, 'Xin chào {0}', {expect_moderator: true}), cookie: minh});
  assert.equal(saved.status, 200, JSON.stringify(saved.body));
  assert.equal(saved.body.result, 'moderator_saved');
  assert.equal(saved.body.line.status, 'approved');
  assert.equal(saved.body.line.provenance, 'moderator');
  assert.equal(saved.body.line.approved_by, 'Minh (Moderator)');
  assert.equal(saved.body.line.translator, 'Minh');

  // a normal contributor proposes an edit: it stays pending
  line = await lineOf(f.env, lan);
  const proposed = await api(f.env, 'POST', '/api/collab/submit', {body: submitBody(line, 'Chào bạn {0}', {reason: 'naturalness'}), cookie: lan});
  assert.equal(proposed.status, 200, JSON.stringify(proposed.body));
  assert.equal(proposed.body.result, 'proposed');
  assert.equal(proposed.body.line.status, 'approved');
  assert.equal(proposed.body.line.new_vi, 'Xin chào {0}');

  // the Moderator edits an existing translation: applied at once, no pending proposal left behind
  line = await lineOf(f.env, minh);
  const edited = await api(f.env, 'POST', '/api/collab/submit', {body: submitBody(line, 'Xin chào nhé {0}', {reason: 'meaning', expect_moderator: true}), cookie: minh});
  assert.equal(edited.status, 200, JSON.stringify(edited.body));
  assert.equal(edited.body.result, 'moderator_saved');
  assert.equal(edited.body.line.new_vi, 'Xin chào nhé {0}');
  assert.equal(edited.body.line.status, 'approved');
  const mine = f.env.DB.db.prepare("SELECT state,reviewed_by FROM proposals WHERE translator='Minh'").all();
  assert.deepEqual(mine.map(row => row.state), ['accepted']);
  assert.equal(mine[0].reviewed_by, 'Minh (Moderator)');
  const types = f.env.DB.db.prepare('SELECT event_type FROM history ORDER BY revision').all().map(row => row.event_type);
  assert.ok(types.includes('translation_saved') && types.includes('moderator_approved'), types.join(','));
 } finally { f.close(); }
});

test('a client that expects Moderator after the code was revoked fails loudly instead of queuing', async () => {
 const f = makeEnv(oneLine());
 try {
  const {code, id} = await createCode(f.env);
  const minh = await newUser(f.env, 'Minh');
  await api(f.env, 'POST', '/api/collab/moderator', {body: {action: 'activate', code}, cookie: minh});
  await api(f.env, 'POST', '/api/admin/moderators', {body: {action: 'revoke', id}, key: KEY, cookie: await adminCookie(f.env)});
  const line = await lineOf(f.env, minh);
  const refused = await api(f.env, 'POST', '/api/collab/submit', {body: submitBody(line, 'Xin chào {0}', {expect_moderator: true}), cookie: minh});
  assert.equal(refused.status, 403);
  assert.equal(refused.body.code, 'moderator_invalid');
  const queued = await api(f.env, 'POST', '/api/collab/submit', {body: submitBody(line, 'Xin chào {0}'), cookie: minh});
  assert.equal(queued.status, 200);
  assert.equal(queued.body.line.status, 'pending');
 } finally { f.close(); }
});

test('Chuong_10_MainStory is an accepted chapter', async () => {
 const f = makeEnv(oneLine());
 try {
  const cookie = await newUser(f.env, 'Minh');
  const response = await api(f.env, 'GET', '/api/collab/line?chapter_id=Chuong_10_MainStory&line_id=line-1', {cookie});
  assert.equal(response.status, 200, JSON.stringify(response.body));
 } finally { f.close(); }
});

// ---- bulk approve ------------------------------------------------------------------------
function bulkScenes() {
 const base = {old_vi: '', translator: 'Dịch giả', notes: ''};
 return [
  {scene_id: 'S1', title: 'Scene 1', lines: [
   {line_id: 'ok-1', en: 'Hello {0}', new_vi: 'Xin chào {0}', status: 'Chờ duyệt', ...base},
   {line_id: 'ok-2', en: 'Good night', new_vi: 'Chúc ngủ ngon', status: 'Chờ duyệt', ...base},
   {line_id: 'same-en', en: 'Keep me', new_vi: 'Keep me', status: 'Chờ duyệt', ...base},
   {line_id: 'bad-token', en: 'Hello {0}', new_vi: 'Xin chào', status: 'Chờ duyệt', ...base},
   {line_id: 'has-proposal', en: 'Wait', new_vi: 'Chờ đã', status: 'Chờ duyệt', ...base},
   {line_id: 'approved', en: 'Done', new_vi: 'Xong', status: 'Đã duyệt', ...base},
   {line_id: 'untranslated', en: 'Not yet', new_vi: '', status: 'Chờ dịch', ...base},
  ]},
  {scene_id: 'S2', title: 'Scene 2', lines: [
   {line_id: 's2-ok', en: 'Second scene', new_vi: 'Cảnh hai', status: 'Chờ duyệt', ...base},
   {line_id: 'never-opened', en: 'Never opened', new_vi: 'Chưa mở', status: 'Chờ duyệt', ...base},
  ]},
 ];
}
async function seedBulk(f) {
 const user = await newUser(f.env, 'Minh');
 for (const id of ['ok-1', 'ok-2', 'same-en', 'bad-token', 'has-proposal', 'approved', 'untranslated', 's2-ok']) await lineOf(f.env, user, id); // creates the baseline rows
 const line = await lineOf(f.env, user, 'has-proposal');
 const proposal = await api(f.env, 'POST', '/api/collab/submit', {body: submitBody(line, 'Đợi chút', {reason: 'naturalness'}), cookie: user});
 assert.equal(proposal.status, 200, JSON.stringify(proposal.body));
 return user;
}
const bulk = (f, body, cookie) => api(f.env, 'POST', '/api/admin/bulk_approve', {body: {chapter_id: CH, reason: 'Chủ dự án đã duyệt', ...body}, key: KEY, cookie});

test('bulk approve dry run reports the plan and writes nothing', async () => {
 const f = makeEnv(bulkScenes());
 try {
  await seedBulk(f);
  const admin = await adminCookie(f.env);
  const plan = await bulk(f, {dry_run: true, scene_id: ''}, admin);
  assert.equal(plan.status, 200, JSON.stringify(plan.body));
  const data = plan.body.data;
  assert.equal(data.dry_run, true);
  assert.equal(data.candidates, 3, JSON.stringify(data)); // ok-1, ok-2, s2-ok
  assert.equal(data.skipped.con_nguyen_tieng_anh, 1);
  assert.equal(data.skipped.loi_ma_dinh_dang, 1);
  assert.equal(data.skipped.co_de_xuat_cho, 1);
  assert.equal(data.skipped.chua_co_ban_dich, 0);
  assert.equal(data.not_in_database, 1); // never-opened
  assert.equal(f.env.DB.db.prepare("SELECT count(*) n FROM lines WHERE status='approved' AND approved_by IS NOT NULL").get().n, 0);
  // omitting dry_run is also a dry run
  const implicit = await api(f.env, 'POST', '/api/admin/bulk_approve', {body: {chapter_id: CH, scene_id: '', reason: 'x'}, key: KEY, cookie: admin});
  assert.equal(implicit.body.data.dry_run, true);
  assert.equal(f.env.DB.db.prepare("SELECT count(*) n FROM lines WHERE status='pending'").get().n, 6);
 } finally { f.close(); }
});

test('bulk approve approves only eligible lines, one history entry each, and can be limited to a scene', async () => {
 const f = makeEnv(bulkScenes());
 try {
  await seedBulk(f);
  const admin = await adminCookie(f.env);

  const scoped = await bulk(f, {dry_run: false, scene_id: 'S2'}, admin);
  assert.equal(scoped.status, 200, JSON.stringify(scoped.body));
  assert.equal(scoped.body.data.approved, 1);
  assert.equal(scoped.body.data.remaining, 0);
  assert.equal(f.env.DB.db.prepare("SELECT status FROM lines WHERE line_id='s2-ok'").get().status, 'approved');
  assert.equal(f.env.DB.db.prepare("SELECT status FROM lines WHERE line_id='ok-1'").get().status, 'pending');

  const all = await bulk(f, {dry_run: false, scene_id: ''}, admin);
  assert.equal(all.body.data.approved, 2, JSON.stringify(all.body));
  assert.equal(all.body.data.remaining, 0);
  const status = id => f.env.DB.db.prepare('SELECT status,revision,approved_by,approved_at FROM lines WHERE line_id=?').get(id);
  assert.equal(status('ok-1').status, 'approved');
  assert.equal(status('ok-1').approved_by, 'Admin');
  assert.ok(status('ok-1').approved_at);
  assert.equal(status('ok-1').revision, 1); // a baseline row starts at revision 0; approving adds exactly one revision
  for (const id of ['same-en', 'bad-token', 'has-proposal']) assert.equal(status(id).status === 'approved', false, id + ' must not be approved');
  assert.equal(status('approved').status, 'approved');
  assert.equal(status('untranslated').status, 'untranslated');

  const history = f.env.DB.db.prepare("SELECT line_id,event_type,actor,reason,old_status,new_status,revision,snapshot_json FROM history WHERE reason LIKE 'Duyệt hàng loạt:%' ORDER BY line_id").all();
  assert.deepEqual(history.map(row => row.line_id), ['ok-1', 'ok-2', 's2-ok']);
  for (const row of history) {
   assert.equal(row.event_type, 'approved');
   assert.equal(row.actor, 'Admin');
   assert.equal(row.old_status, 'pending');
   assert.equal(row.new_status, 'approved');
   assert.equal(row.reason, 'Duyệt hàng loạt: Chủ dự án đã duyệt');
   const snapshot = JSON.parse(row.snapshot_json);
   assert.equal(snapshot.status, 'approved');
   assert.equal('pending_proposals' in snapshot, false);
  }
  // repeating approves nothing
  const again = await bulk(f, {dry_run: false, scene_id: ''}, admin);
  assert.equal(again.body.data.approved, 0);
  assert.equal(again.body.data.candidates, 0);
 } finally { f.close(); }
});

test('bulk approve handles at most 200 lines per request and reports what remains', async () => {
 const base = {old_vi: '', translator: 'Dịch giả', notes: '', status: 'Chờ duyệt'};
 const lines = Array.from({length: 205}, (_, index) => ({line_id: 'bulk-' + String(index).padStart(3, '0'), en: 'Line ' + index, new_vi: 'Dòng ' + index, ...base}));
 const f = makeEnv([{scene_id: 'S1', title: 'Many', lines}]);
 try {
  const user = await newUser(f.env, 'Minh');
  for (const line of lines) await lineOf(f.env, user, line.line_id);
  const admin = await adminCookie(f.env);
  const first = await bulk(f, {dry_run: false, scene_id: ''}, admin);
  assert.equal(first.status, 200, JSON.stringify(first.body));
  assert.equal(first.body.data.candidates, 205);
  assert.equal(first.body.data.approved, 200);
  assert.equal(first.body.data.remaining, 5);
  const second = await bulk(f, {dry_run: false, scene_id: ''}, admin);
  assert.equal(second.body.data.approved, 5);
  assert.equal(second.body.data.remaining, 0);
  assert.equal(f.env.DB.db.prepare("SELECT count(*) n FROM lines WHERE status='approved'").get().n, 205);
  assert.equal(f.env.DB.db.prepare("SELECT count(*) n FROM history WHERE reason LIKE 'Duyệt hàng loạt:%'").get().n, 205);
 } finally { f.close(); }
});

test('bulk approve validates its input and refuses while publishing', async () => {
 const f = makeEnv(bulkScenes());
 try {
  await seedBulk(f);
  const admin = await adminCookie(f.env);
  assert.equal((await bulk(f, {dry_run: true, scene_id: 'nope'}, admin)).status, 400);
  assert.equal((await bulk(f, {dry_run: true, reason: ''}, admin)).status, 400);
  assert.equal((await bulk(f, {dry_run: true, chapter_id: 'Chuong_999_Fake'}, admin)).status, 400);
  assert.equal((await bulk(f, {dry_run: true, chapter_id: '../etc'}, admin)).status, 400);
  f.env.DB.db.prepare("UPDATE dataset_state SET phase='publishing' WHERE id=1").run();
  const blocked = await bulk(f, {dry_run: false, scene_id: ''}, admin);
  assert.equal(blocked.status, 423);
  assert.equal(f.env.DB.db.prepare("SELECT count(*) n FROM lines WHERE status='approved' AND approved_by IS NOT NULL").get().n, 0);
  f.env.DB.db.prepare("UPDATE dataset_state SET phase='locked' WHERE id=1").run();
  const locked = await bulk(f, {dry_run: false, scene_id: 'S2'}, admin);
  assert.equal(locked.status, 200, JSON.stringify(locked.body)); // review is allowed while the dataset is locked
 } finally { f.close(); }
});

test('bulk approve never overwrites a line that changed after the plan was made', async () => {
 const f = makeEnv(bulkScenes());
 try {
  const user = await seedBulk(f);
  const admin = await adminCookie(f.env);
  const plan = await bulk(f, {dry_run: true, scene_id: 'S1'}, admin);
  assert.equal(plan.body.data.candidates, 2);
  // someone edits ok-1 after the plan (revision changes, status goes back to pending with new text)
  const line = await lineOf(f.env, user, 'ok-1');
  f.env.DB.db.prepare("UPDATE lines SET revision=revision+5 WHERE line_id='ok-1'").run();
  const run = await bulk(f, {dry_run: false, scene_id: 'S1'}, admin);
  assert.equal(run.status, 200, JSON.stringify(run.body));
  // the second run re-reads the database, so the bumped line is still approved correctly at its own revision
  assert.equal(run.body.data.approved, 2);
  assert.equal(f.env.DB.db.prepare("SELECT revision FROM lines WHERE line_id='ok-1'").get().revision, line.revision + 5 + 1);
 } finally { f.close(); }
});
