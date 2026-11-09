import test from 'node:test';
import assert from 'node:assert/strict';
import {parseGviz,parseGlossary,parseMerge,overlayReferences,overlayMergeReferences,getMerge} from '../web/story_translator/worker/sheets-source.mjs';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const row=(...values)=>({c:values.map(v=>v===null?null:{v})});
const cols=labels=>labels.map(label=>({label}));
test('only accepts the expected Google response wrapper',()=>{
 assert.equal(parseGviz('/*O_o*/\ngoogle.visualization.Query.setResponse({"status":"ok","table":{"cols":[],"rows":[]}});').rows.length,0);
 assert.throws(()=>parseGviz('alert(1)'));
});
test('glossary retains separate IDs and review status',()=>{
 const table={cols:[],rows:[row('title'),row('link'),row('Danh từ gốc (EN)','Bản dịch Tiếng Việt chuẩn','Phân loại nhóm','notes','Trạng thái'),row('Same','Một','term','','review','','','term-key'),row('Same','Hai','character_name','','pending','','','id-key')]};
 const data=parseGlossary(table);assert.equal(data.length,2);assert.deepEqual(data.map(x=>x.status),['review','pending']);assert.notEqual(data[0].id,data[1].id);
});
test('Merge rejects wrong schema and duplicate order',()=>{
 const headers=['file_id','block_order','kind','speaker_en','speaker_jp','speaker_cn','speaker_vi','text_vi','text_cn','text_jp','text_en','source_refs_json'];
 const table={cols:cols(headers),rows:[row('s',1,'','','','','','vi','cn','jp','en','')]};assert.equal(parseMerge(table,'g').files[0].blocks[0].jp,'jp');
 assert.throws(()=>parseMerge({...table,rows:[...table.rows,...table.rows]},'g'));
 assert.throws(()=>parseMerge({...table,cols:cols(['wrong'])},'g'));
});
test('Sheet references attach only to unique IDs with exact EN; VI remains D1',()=>{
 const headers=['scene','Mã câu (ID) [Khóa]','speaker','Nguồn EN','Nguồn CN (r03)','Nguồn JP (r03)'];
 const chapter={scenes:[{lines:[{line_id:'a',en:'One',new_vi:'D1'},{line_id:'b',en:'Original',new_vi:'Keep'},{line_id:'c',en:'Same',new_vi:'Keep'}]}]};
 const table={cols:cols(headers),rows:[row('s','a','','One','中','日','old','sheet'),row('s','b','','Changed','错','違'),row('s','c','','Same','一','一'),row('s','c','','Same','二','二')]};
 const out=overlayReferences(chapter,table);assert.equal(out.sheet_sync.matched,1);assert.equal(out.scenes[0].lines[0].new_vi,'D1');assert.equal(out.scenes[0].lines[0].sheet_vi,'sheet');assert.equal(out.scenes[0].lines[1].cn,undefined);assert.equal(out.scenes[0].lines[2].cn,undefined);
});
test('Chương 0 Merge references join by file and unique EN, never by row order',()=>{
 const chapter={scenes:[{scene_id:'STm00_01',lines:[
  {line_id:'STm00_01.1',en:'command-only',new_vi:'D1'},
  {line_id:'STm00_01.2',en:'Hello',new_vi:'Keep'},
  {line_id:'STm00_01.3',en:'Duplicate',new_vi:'Keep'}
 ]}]};
 const merge={group:'Chuong_STm00',files:[{file_id:'STm00_01',blocks:[
  {order:1,en:'Hello',vi:'Sheet VI',cn:'中',jp:'日'},
  {order:2,en:'Duplicate',vi:'A',cn:'一',jp:'一'},
  {order:3,en:'Duplicate',vi:'B',cn:'二',jp:'二'}
 ]}]};
 const out=overlayMergeReferences(chapter,merge);
 assert.equal(out.sheet_sync.matched,1);
 assert.equal(out.scenes[0].lines[1].sheet_vi,'Sheet VI');
 assert.equal(out.scenes[0].lines[1].new_vi,'Keep');
 assert.equal(out.scenes[0].lines[2].sheet_vi,undefined);
});
test('unknown group never triggers a network request',async()=>{let called=false;await assert.rejects(()=>getMerge('other',()=>{called=true;}));assert.equal(called,false);});
test('glossary UI keeps entries that share EN but have different source IDs',()=>{
 const code=readFileSync(new URL('../web/story_translator/js/models/GlossaryModel.js',import.meta.url),'utf8');
 const context=vm.createContext({localStorage:{getItem:()=>null},console});vm.runInContext(code,context);
 const out=context.normalizeLoadedGlossaryTerms([{id:'term',en:'Boss',vi:'Boss'},{id:'character',en:'Boss',vi:'Sếp'}]);assert.equal(out.length,2);
});
test('story UI skips code-only sources but keeps formatted prose',()=>{
 const code=readFileSync(new URL('../web/story_translator/js/models/StoryModel.js',import.meta.url),'utf8');
 const context=vm.createContext({localStorage:{getItem:()=>null},console});vm.runInContext(code,context);
 assert.equal(context.isCodeOnlySource('ep_mainline_001'),true);
 assert.equal(context.isCodeOnlySource('SetChoiceBegin'),true);
 assert.equal(context.isCodeOnlySource('story_main_00_007'),true);
 assert.equal(context.isCodeOnlySource('<size=47>==RT==A bright future awaits.</size>'),false);
 assert.equal(context.isCodeOnlySource('The Beginning'),false);
});
test('leaderboard UI accepts the Worker envelope and normalizes levels',()=>{
 const code=readFileSync(new URL('../web/story_translator/js/views/LeaderboardView.js',import.meta.url),'utf8');
 const context=vm.createContext({console});vm.runInContext(code,context);
 assert.equal(context.normalizeLeaderboardPayload({success:true,leaders:[{name:'A'}]}).length,1);
 assert.equal(context.formatLeaderboardLevel('Cấp 2'),'Lv. 2');
 assert.equal(context.formatLeaderboardLevel(3),'Lv. 3');
});
test('glossary local edits override the matching Sheet term',()=>{
 const store={ss_custom_glossary:JSON.stringify([{id:'term-id',en:'Boss',vi:'Trùm sửa',category:'Nhân Vật & Đại Từ',notes:'local'}])};
 const code=readFileSync(new URL('../web/story_translator/js/models/GlossaryModel.js',import.meta.url),'utf8');
 const context=vm.createContext({localStorage:{getItem:key=>store[key]||null},console});vm.runInContext(code,context);
 const out=context.normalizeLoadedGlossaryTerms([{id:'term-id',en:'Boss',vi:'Boss',category:'General'}]);
 assert.equal(out.length,1);assert.equal(out[0].vi,'Trùm sửa');assert.equal(out[0].notes,'local');
});
