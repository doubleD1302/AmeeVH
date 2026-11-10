import test from 'node:test';
import {runInNewContext} from 'node:vm';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
const source = await readFile(new URL('../web/story_translator/js/handoff-zip.js', import.meta.url), 'utf8');
const { createZip, isSafeArchivePath } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
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

const portal=await readFile(new URL('../web/story_translator/js/admin-portal.js',import.meta.url),'utf8');
test('creating a saved export automatically starts its ZIP download',async()=>{
 const state={exportType:'snapshot',chapterId:'chapter',agentInstructions:'',exportRecords:[]};let downloaded=null;
 const ctx={state,previewMode:false,render(){},async request(){return {data:{export_id:'new-export',manifest:{files:{}}}};},async downloadHandoffZip(id){downloaded=id;}};
 const start=portal.indexOf('async function createHandoff()'),end=portal.indexOf('async function manageRelease()',start);
 runInNewContext(portal.slice(start,end)+';globalThis.create=createHandoff;',ctx);
 await ctx.create();assert.equal(downloaded,'new-export');assert.equal(state.view,'history');assert.equal(state.loading,false);
});
test('ZIP auto-download verifies bytes and provides a reusable download URL',async()=>{
 const bytes=new TextEncoder().encode('Nội dung gói');
 const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
 const manifest={export_id:'test-export',files:{'TASK.json':{bytes:bytes.length,sha256:hash}}};let clicks=0,createdBlob;
 const ctx={state:{lastDownload:null},TextDecoder,Uint8Array,crypto,JSON,createZip,isSafeArchivePath,render(){},URL:{createObjectURL(blob){createdBlob=blob;return 'blob:test';},revokeObjectURL(){}},document:{body:{append(){}},createElement(){return {click(){clicks++;},remove(){}};}},async request(path){return new Response(path.endsWith('manifest.json')?JSON.stringify(manifest):bytes);},async openModal(){throw Error('unexpected error');}};
 const start=portal.indexOf('async function downloadHandoffZip('),end=portal.indexOf('async function createHandoff()',start);
 runInNewContext(portal.slice(start,end)+';globalThis.download=downloadHandoffZip;',ctx);
 await ctx.download('test-export');assert.equal(clicks,1);assert.equal(ctx.state.lastDownload.url,'blob:test');assert.equal(ctx.state.lastDownload.name,'test-export.zip');assert.equal(createdBlob.type,'application/zip');
});

test('ZIP accepts document and skill folders but rejects traversal and absolute paths',async()=>{
 for(const name of ['docs/HACHIMINH_WORKFLOW_INTEGRATION.md','skills/stella-github-translation-sync/references/git-workflow.md']){
  assert.equal(isSafeArchivePath(name),true);assert.ok((await createZip([{name,bytes:new Uint8Array([1,2,3])}]).arrayBuffer()).byteLength>0);
 }
 for(const name of ['../file','docs/../file','/absolute','C:/file','docs//file','docs/./file','docs\\file'])assert.equal(isSafeArchivePath(name),false,name);
});
