'use strict';
const fs=require('node:fs'),path=require('node:path');
const io=require('./language_resource_io_20261031.cjs');
const ROOT=path.resolve(__dirname,'..');
const RUN='language_export_20261031_r01';
const taskDir=path.join(ROOT,'work/subagents',RUN);
const natural=(a,b)=>a.localeCompare(b,'en',{numeric:true});
const safe=s=>String(s).replace(/[<>:"/\\|?*\x00-\x1f]/g,'_').replace(/[. ]+$/g,'').slice(0,100);
const json=b=>JSON.parse(io.utf8(b).replace(/^\uFEFF/,''));
const rel=p=>path.relative(ROOT,p).replaceAll('\\','/');
function main(){
  const outArg=process.argv.indexOf('--out');
  if(outArg<0||!process.argv[outArg+1])throw Error('Usage: node tools/export_language_resources_en_20261031.cjs --out dist/NEW_FOLDER');
  const OUT=path.resolve(ROOT,process.argv[outArg+1]);
  if(!OUT.startsWith(ROOT+path.sep)||OUT===ROOT)throw Error('Output must be a new directory under project root');
  if(fs.existsSync(OUT))throw Error('Output already exists; choose a new revision');
  const sourceFiles=new Map(),outputFiles=[],items=[],counts={};
  function source(p,expected){const absolute=path.resolve(ROOT,p),raw=fs.readFileSync(absolute),hash=io.sha256(raw);if(expected&&expected!==hash)throw Error('Source hash mismatch '+p);sourceFiles.set(rel(absolute),{path:rel(absolute),sha256:hash,bytes:raw.length});return raw;}
  const map=json(source('work/subagents/'+RUN+'/scene_mapping/SCENE_CHARACTER_MAP.json'));
  const owners=json(source('work/subagents/'+RUN+'/scene_mapping/TABLE_OWNER_MAP.json')).records;
  const tableRegistry=json(source('work/subagents/'+RUN+'/locale_inventory/EN_CN_TABLES.json'));
  const subtitles=json(source('work/subagents/'+RUN+'/scene_mapping/SUBTITLES_EN.json'));
  const luaPath='dist/vanilla/lua_original_en.arcx';
  source(luaPath,'c3ad12de988a609a3c99be79ed8dfc69b54ba3d8082170a25e1f4851b1419b49');
  const arc=io.readArchive(path.join(ROOT,luaPath));
  const characterMap={...map.characters,...map.npcs};
  const decoded=[],presets={},luaStrings=[];
  for(const entry of arc.entries){
    const payload=io.xxteaDecrypt(arc.extract(entry));
    if(!payload.subarray(0,4).equals(Buffer.from([27,76,117,97])))continue;
    const parsed=io.parseLua53(payload),normalized=parsed.source?.replaceAll('\\','/'),logical=normalized?.split('/Lua/').at(-1);
    const strings=parsed.stringRecords;
    luaStrings.push({source_path:logical,source_archive:luaPath,entry_hash:entry.hash_hex,payload_sha256:io.sha256(payload),strings});
    if(normalized?.includes('/Avg/_en/Config/')){
      const commands=io.literalLuaTable(parsed);
      if(!Array.isArray(commands))throw Error('Scene did not return command list '+logical);
      decoded.push({scene_id:path.basename(logical,'.lua'),source_path:logical,archive_entry_hash:entry.hash_hex,payload_sha256:io.sha256(payload),strings,commands});
    }else if(normalized?.includes('/Avg/_en/Preset/'))presets[path.basename(logical,'.lua')]={source_path:logical,entry_hash:entry.hash_hex,data:io.literalLuaTable(parsed)};
  }
  if(decoded.length!==626)throw Error('Unexpected scene count '+decoded.length);
  const actors={};for(const a of presets.AvgCharacter?.data??[])actors[a.id]=a;
  function charFolder(id){const c=characterMap[id];return '02_NhanVat/'+safe(id+'_'+(c?.name_en||'ChuaRangBuocTen'));}
  function sceneFolder(id){let m;
    if(m=/^STm(\d+(?:x\d+)?)_/.exec(id))return ['main_story','01_CotTruyen/01_Chinh/Chuong_STm'+m[1],null];
    if(m=/^STev_(\d+)_/.exec(id))return ['event_story','01_CotTruyen/02_SuKien/Chuong_STev_'+m[1],null];
    if(m=/^STsp_(\d+)_/.exec(id))return ['side_story','01_CotTruyen/03_NgoaiTruyen/Chuong_STsp_'+m[1],null];
    if(m=/^BBm(\d+)_/.exec(id))return ['bulletin_board','01_CotTruyen/04_BangUyThac/Chuong_BBm'+m[1],null];
    if(/^BBm_Dorm(?:Approach|Indoor|Outdoor)$/.test(id))return ['dorm_interaction','01_CotTruyen/08_KyTucXa/Chuong_BBm_Dorm',null];
    if(m=/^CG_(\d+)_/.exec(id))return ['character_story',charFolder(m[1])+'/Story/Chuong_CG_'+m[1],m[1]];
    if(m=/^CG_npc(\d+)_/.exec(id)){const cid='9'+m[1];return ['npc_story',charFolder(cid)+'/Story/Chuong_CG_npc'+m[1],cid];}
    if(/^CG_disc\d+$/.test(id))return ['disc_story','01_CotTruyen/05_DiaNhac/Chuong_CG_disc',null];
    if(m=/^PM(\d{3})\d+$/.exec(id))return ['phone_messages',charFolder(m[1])+'/TinNhan/Chuong_PM'+m[1],m[1]];
    if((m=/^DP_single(\d{3})$/.exec(id))&&characterMap[m[1]])return ['character_dating',charFolder(m[1])+'/HenHo/Chuong_DP_single'+m[1],m[1]];
    if(/^DP_(single|multi)\d+$/.test(id))return ['shared_dating','01_CotTruyen/06_HenHoChung/Chuong_DP',null];
    if(id==='GD_gacha')return ['tutorial','01_CotTruyen/07_HuongDan/Chuong_GD',null];
    if(/^ST_sys_/.test(id))return ['system_story','01_CotTruyen/07_HuongDan/Chuong_ST_sys',null];
    return ['unclassified','01_CotTruyen/99_ChuaPhanLoai/Chuong_'+safe(id.split('_')[0]),null];
  }
  fs.mkdirSync(OUT,{recursive:false});
  function write(p,data,kind){const dst=path.resolve(OUT,p);if(!dst.startsWith(OUT+path.sep))throw Error('Unsafe output path');fs.mkdirSync(path.dirname(dst),{recursive:true});fs.writeFileSync(dst,data,{flag:'wx'});outputFiles.push({path:p,sha256:io.sha256(Buffer.from(data)),bytes:Buffer.byteLength(data),kind});return p;}
  const writeJSON=(p,d,kind)=>write(p,JSON.stringify(d,null,2)+'\n',kind);
  function textFile(p,title,sourceInfo,records,kind){let body=`${title}\nNgon ngu chu: EN\nNguon: ${sourceInfo}\nSo muc: ${records.length}\n\n`;for(const x of records)body+=`[${x.id}]${x.speaker?' '+x.speaker:''}\n${x.text}${x.text===''?' [EMPTY_SOURCE]':''}\n\n`;write(p,body,kind);items.push({kind,path:p,records:records.length});}
  const textPositions={SetTalk:[2,6,7,8],SetBubble:[2,5,6,8,9],SetPhoneMsg:[7,8],SetIntro:[1,2,3],SetSceneHeading:[0,1,2,3,4],SetChoiceBegin:[3,8,9,10,11,12,13],SetPhoneMsgChoiceBegin:[1,2,3,4,5,6],SetMajorChoice:[3,4,5,10,11,12,17,18,19,25,26,29,30],SetPersonalityChoice:[2,3,4,8,9],SetPhoneThinking:[3],SetWordTrans:[0],NewCharIntro:[1,2]};
  const controls=new Set(['SetChoiceJumpTo','SetChoiceEnd','SetPhoneMsgChoiceJumpTo','SetPhoneMsgChoiceEnd','SetMajorChoiceJumpTo','SetMajorChoiceRollover','SetMajorChoiceEnd','SetPersonalityChoiceJumpTo','SetPersonalityChoiceRollover','SetPersonalityChoiceEnd','JUMP_AVG_ID','Jump','IfTrue','EndIf','IfUnlock','IfUnlockElse','IfUnlockEnd','CheckBE','CheckBECase','CheckBEEnd']);
  const storyRaw=[],sceneIndex=[];let narrativeStrings=0,commandCount=0;
  for(const scene of decoded.sort((a,b)=>natural(a.scene_id,b.scene_id))){
    const [category,folder,cid]=sceneFolder(scene.scene_id),records=[],allText=[];
    function leaf(v,prefix,command,speaker){if(typeof v==='string'&&v!==''){const x={id:scene.scene_id+'::command/'+command+prefix,text:v,speaker};records.push(x);allText.push(x);}else if(Array.isArray(v))v.forEach((x,i)=>leaf(x,prefix+'/'+i,command,speaker));}
    scene.commands.forEach((cmd,i)=>{const p=cmd.param??[],actorId=cmd.cmd==='SetBubble'?p[0]:p[1],speaker=['SetTalk','SetBubble','SetPhoneMsg'].includes(cmd.cmd)?(cmd.cmd==='SetBubble'&&p[6]?p[6]:(actors[actorId]?.name||actorId||'')):'';
      if(textPositions[cmd.cmd])for(const pos of textPositions[cmd.cmd])leaf(p[pos],'/param/'+pos,i,speaker);
      if(controls.has(cmd.cmd))records.push({id:scene.scene_id+'::command/'+i+' '+cmd.cmd,text:JSON.stringify(p),speaker:''});
    });
    const file=folder+'/'+safe(scene.scene_id)+'_EN.txt';
    textFile(file,scene.scene_id+' | '+category,luaPath+'#'+scene.archive_entry_hash+' | Thu tu lenh trong nguon; bao gom cac nhanh lua chon.',records,'scene');
    const index={scene_id:scene.scene_id,category,chapter_folder:folder,character_id:cid,path:file,commands:scene.commands.length,text_fields:allText.length,source_path:scene.source_path,archive_entry_hash:scene.archive_entry_hash,payload_sha256:scene.payload_sha256};
    storyRaw.push({...index,strings:scene.strings,commands_data:scene.commands,text_records:allText});sceneIndex.push(index);narrativeStrings+=allText.length;commandCount+=scene.commands.length;
  }
  write('99_DuLieuGoc_EN/Scenes_EN.jsonl',storyRaw.map(x=>JSON.stringify(x)).join('\n')+'\n','raw_scenes');
  write('99_DuLieuGoc_EN/Lua_Strings_ClientEN.jsonl',luaStrings.map(x=>JSON.stringify(x)).join('\n')+'\n','client_lua_reference');
  writeJSON('99_DuLieuGoc_EN/Presets_EN.json',presets,'raw_presets');
  for(const [name,pr]of Object.entries(presets)){
    const records=[];function leaves(v,prefix){if(typeof v==='string')records.push({id:prefix,text:v});else if(v&&typeof v==='object')for(const [k,x]of Object.entries(v))leaves(x,prefix+'/'+k);}
    leaves(pr.data,'');textFile('03_BangText_UI_KyNang/Preset/'+name+'_EN.txt',name,pr.source_path,records,'preset');
  }
  const tableIndex=[];let tableStrings=0,emptyStrings=0;
  for(const table of tableRegistry){
    const raw=source(table.en.path,table.en.sha256),data=json(raw),keys=Object.keys(data);
    if(keys.length!==table.en.strings||keys.some(k=>typeof data[k]!=='string'))throw Error('Invalid EN table '+table.table);
    writeJSON('99_DuLieuGoc_EN/Tables/'+safe(table.table)+'_EN.json',data,'raw_table');
    const groups=new Map();
    for(const key of keys.sort(natural)){
      const recordId=key.split('.').slice(0,-1).join('.'),owner=owners[recordId],cid=owner?.character_id;
      let folder='03_BangText_UI_KyNang/'+safe(table.table);
      if(cid){const type=/^CharacterArchive|^CharacterDes$|^Character$/.test(table.table)?'HoSo':/Plot|CharacterCG|Dating|NPC/.test(table.table)?'Story/ThongTin':'DuLieu';folder=charFolder(cid)+'/'+type;}
      const filename=folder+'/'+safe(table.table)+'_EN.txt';const list=groups.get(filename)??[];list.push({id:key,text:data[key]});groups.set(filename,list);
      tableStrings++;if(data[key]==='')emptyStrings++;
    }
    for(const [p,records]of groups)textFile(p,table.table,table.en.path,records,'table');
    tableIndex.push({table:table.table,source_path:table.en.path,source_sha256:table.en.sha256,keys:keys.length,readable_paths:[...groups.keys()],raw_path:'99_DuLieuGoc_EN/Tables/'+safe(table.table)+'_EN.json'});
  }
  const voiceManifest=json(source('work/research/data_200_pristine_en/manifest.json'));
  const voiceEntry=voiceManifest.entries.find(x=>x.hash_hex==='0x80911df3a563e0f3');
  const voicePath='work/research/data_200_pristine_en/entries/'+voiceEntry.filename,voice=json(source(voicePath)),voiceGroups=new Map();let voiceSegments=0;
  for(const [key,v]of Object.entries(voice)){
    const m=/^vo_(\d{3})(?:_|\d)/.exec(key),cid=m?.[1],folder=cid?charFolder(cid)+'/LoiThoai':'03_BangText_UI_KyNang/BubbleVoice';const file=folder+'/BubbleVoice_EN.txt',records=voiceGroups.get(file)??[];
    for(const [track,lines]of Object.entries(v.text??{}))lines.forEach((text,i)=>{if(typeof text!=='string')throw Error('Invalid voice text');if(text!==''){records.push({id:key+'::'+track+'/'+i,text});voiceSegments++;}});
    voiceGroups.set(file,records);
  }
  for(const [file,records]of voiceGroups)textFile(file,'BubbleVoice (JP/CN suffixes indicate audio tracks; all exported text belongs to EN client)',voicePath,records,'voice');
  writeJSON('99_DuLieuGoc_EN/BubbleVoice_EN.json',voice,'raw_voice');
  const subFiles=Array.isArray(subtitles)?subtitles:subtitles.files;
  if(!Array.isArray(subFiles))throw Error('Unsupported subtitle catalog shape');
  let subCount=0;
  for(const sub of subFiles){
    const name=sub.filename??sub.file_name??path.basename(sub.source_path??sub.file??''),chapter=name.split('-')[0],cues=sub.cues;
    if(!name||!Array.isArray(cues))throw Error('Malformed subtitle input');
    const records=cues.map(x=>({id:String(x.cue??x.index??x.id)+' | '+x.timestamp,text:x.text??x.source_text}));
    if(records.some(x=>typeof x.text!=='string'||x.id.includes('undefined')))throw Error('Incomplete subtitle cue');
    textFile('04_PhuDeVideo/Chuong_'+safe(chapter)+'/'+safe(name.replace(/\.srt$/i,''))+'.txt',name,sub.source_path??'Recovered from preserved original source records; see raw subtitle catalog',records,'subtitle');write('99_DuLieuGoc_EN/SRT/'+safe(name),sub.srt_text,'raw_srt');subCount+=cues.length;
  }
  writeJSON('99_DuLieuGoc_EN/Subtitles_EN.json',subtitles,'raw_subtitles');
  counts.localization_tables=tableIndex.length;counts.localization_strings=tableStrings;counts.empty_original_strings=emptyStrings;counts.scenes=decoded.length;counts.scene_commands=commandCount;counts.narrative_text_fields=narrativeStrings;counts.lua_chunks_reference=luaStrings.length;counts.voice_records=Object.keys(voice).length;counts.voice_nonempty_segments=voiceSegments;counts.subtitle_files=subFiles.length;counts.subtitle_cues=subCount;
  writeJSON('DANH_MUC_SCENE_EN.json',sceneIndex,'scene_index');writeJSON('DANH_MUC_TABLE_EN.json',tableIndex,'table_index');writeJSON('NHAN_VAT_EN.json',characterMap,'character_index');
  const csv=x=>'"'+String(x??'').replaceAll('"','""')+'"';
  write('DANH_MUC_EN.csv','\uFEFFLoai,Duong_dan,So_muc\r\n'+items.map(x=>[x.kind,x.path,x.records].map(csv).join(',')).join('\r\n')+'\r\n','index');
  const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
  write('MO_DAU.html','<!doctype html><html lang="vi"><meta charset="utf-8"><title>Stella Sora EN</title><style>body{font:16px system-ui;max-width:1100px;margin:32px auto;padding:0 20px;background:#faf9f6;color:#202b3a}input{padding:10px;width:80%}li{margin:8px 0}a{color:#174775}</style><h1>Stella Sora — Tài nguyên chữ EN</h1><p>'+counts.scenes+' màn · '+counts.localization_tables+' bảng · '+counts.localization_strings+' chuỗi bảng · '+counts.subtitle_cues+' cue phụ đề.</p><p>Đọc README trước khi dùng. Nhập tên nhân vật, mã màn, bảng hoặc đường dẫn để tìm.</p><input id="q" placeholder="Amber, STm01, PM, CharacterArchive..."><ul>'+items.map(x=>'<li><a href="'+encodeURI(x.path).replaceAll('#','%23')+'">'+esc(x.path)+'</a> <small>('+x.records+')</small></li>').join('')+'</ul><script>document.getElementById("q").addEventListener("input",e=>{let q=e.target.value.toLowerCase();document.querySelectorAll("li").forEach(x=>x.hidden=!x.textContent.toLowerCase().includes(q))})</script></html>\n','html_index');
  const readme=`# Stella Sora — tài nguyên chữ tiếng Anh\n\nĐây là bản xuất offline từ các nguồn gốc còn lưu trong dự án, không phải bản dịch. Chỉ có EN; CN/JP sẽ bổ sung sau vào cùng cấu trúc tên file.\n\nMở MO_DAU.html để tìm và mở file, hoặc dùng DANH_MUC_EN.csv. Mọi file đọc được là UTF-8, hậu tố _EN.\n\n- 01_CotTruyen: chapter là folder, mỗi màn là một file _EN.txt; gồm truyện chính, sự kiện, ngoại truyện, ủy thác, đĩa nhạc và hướng dẫn.\n- 02_NhanVat: folder theo ID + tên nguồn; bên trong Story, TinNhan, HoSo, HenHo, LoiThoai và dữ liệu liên quan. Truyện tập thể giữ nguyên cả màn để không cắt mất lời của nhân vật khác.\n- 03_BangText_UI_KyNang: toàn bộ phần bảng còn lại, UI, kỹ năng, vật phẩm, mô tả và preset.\n- 04_PhuDeVideo: phân chapter/video; giữ cue, timestamp và các biến thể giọng riêng.\n- 99_DuLieuGoc_EN: JSON/JSONL để đối chiếu chính xác toàn bộ khóa, text, lệnh, hằng chuỗi, dữ liệu giọng và nguồn phụ đề.\n\n## Phạm vi đã trích\n\n${JSON.stringify(counts,null,2)}\n\nCác file màn sắp theo thứ tự lệnh của dữ liệu gốc và bao gồm các nhánh lựa chọn. Không mô phỏng lượt chơi hay tự chọn nhánh. Các mục command/N/param/M chỉ rõ chỉ số lệnh và vị trí tham số từ 0. Giữ nguyên token, rich text, dấu, xuống dòng và lời trùng ở các vị trí khác nhau. Các dòng điều khiển nhánh được đánh dấu riêng. Raw Scenes_EN.jsonl lưu toàn bộ lệnh/tham số và hằng chuỗi, kể cả tham số không phải thoại.\n\nBảng có ${emptyStrings} giá trị nguồn rỗng; bản TXT ghi EMPTY_SOURCE, JSON vẫn là chuỗi rỗng. Các track female_jp/female_cn/male_jp/male_cn trong BubbleVoice đều là chữ của client EN, hậu tố chỉ là giọng đọc. Các track giữ riêng, không khử trùng.\n\n## Nguồn và giới hạn\n\nNguồn bảng: work/research/data_200_pristine_en, 247 bảng EN đã đối chiếu khóa. Không dùng dist/vanilla/data_original_en.arcx vì đọc lại thực tế cho thấy phần bảng EN trong file đó đã bị Việt hóa.\nNguồn kịch bản: dist/vanilla/lua_original_en.arcx, ${decoded.length} màn Config; đã đọc cấu trúc Lua 5.3 bằng parser và dựng bảng literal, không chạy Lua/DLL. Bản lua_tree cũ chỉ có 596 màn nên không dùng làm nguồn chính.\nSnapshot gốc còn có được xác định thuộc tài nguyên 2.0.0; không coi đây là toàn bộ bản cập nhật 2.0.1. Metadata manifest hiện tại không khớp snapshot gốc. Không lấy bản đã Việt hóa hoặc dịch ngược để điền nguồn thiếu.\nPhụ đề: khôi phục chữ và timestamp gốc từ catalog/báo cáo đã lưu; không khẳng định byte-identical với SRT gốc vì BOM/line ending không còn đủ bằng chứng. Giữ lỗi nguồn dffd ở Prologue CNVA.\nLua_Strings_ClientEN.jsonl là tham chiếu toàn bộ hằng chuỗi trong ${luaStrings.length} Lua chunk của client EN; có tên asset, mã kỹ thuật và ghi chú nội bộ bằng ngôn ngữ khác. Đây không phải corpus thoại CN/JP. Preset có cả khóa/ghi chú nội bộ, giữ để không mất dữ liệu.\nKhông xuất âm thanh/video, executable, DLL, font hoặc tài nguyên chỉ tải từ server chưa có trong các snapshot. Ảnh có chữ nếu được kèm là bộ EN đã xuất trước đó; xem danh mục/provenance riêng, không coi số ảnh đó chứng minh bao phủ mọi tài nguyên Unity hiện tại.\n\nMANIFEST.json ghi hash từng nguồn và file output. Game không bị triển khai hay ghi đè; runtime/gameplay: not_tested vì đây là công việc trích xuất offline.\n`;
  write('README.md',readme,'readme');
  const manifest={schema:1,run_id:RUN,locale:'EN',snapshot:'original resources available locally; 2.0.0, not verified 2.0.1',counts,source_files:[...sourceFiles.values()],tools:['tools/language_resource_io_20261031.cjs','tools/export_language_resources_en_20261031.cjs'].map(p=>({path:p,sha256:io.sha256(fs.readFileSync(path.join(ROOT,p)))})),files:outputFiles,missing_locales_deferred:['CN','JP'],game_modified:false,runtime:'not_tested',gameplay:'not_tested'};
  fs.writeFileSync(path.join(OUT,'MANIFEST.json'),JSON.stringify(manifest,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({output:OUT,counts,files:outputFiles.length+1},null,2));
}
if(require.main===module)main();
