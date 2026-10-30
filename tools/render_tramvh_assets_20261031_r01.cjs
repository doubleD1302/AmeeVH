const fs=require('node:fs/promises');
const path=require('node:path');
const {spawn}=require('node:child_process');
const {pathToFileURL}=require('node:url');
const root=path.resolve('StellaSora_VietHoa/web/story_translator/assets/tramvh-icons-r01');
const profile=path.resolve('StellaSora_VietHoa/work/tramvh_icons_20261031_r01_chrome_'+Date.now());
const delay=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 await fs.mkdir(profile,{recursive:true});
 const proc=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless','--disable-gpu','--disable-extensions','--disable-background-networking','--no-first-run','--remote-debugging-port=0','--remote-allow-origins=*',`--user-data-dir=${profile}`,'about:blank'],{windowsHide:true,stdio:'ignore'});
 let ws;
 try{
 let port;
 for(let n=0;n<100;n++){try{port=(await fs.readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];break}catch{await delay(100)}}
 if(!port)throw Error('Chrome did not expose DevToolsActivePort');
 let targets=await(await fetch(`http://127.0.0.1:${port}/json`)).json();
 let page=targets.find(x=>x.type==='page');
 ws=new WebSocket(page.webSocketDebuggerUrl);
 await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});
 let id=0;const pending=new Map();ws.onmessage=e=>{let m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result)}};
 const call=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}))});
 const evaluate=async expression=>{let r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
 await call('Page.enable');
 const renderJobs=[];
 const manifest=JSON.parse(await fs.readFile(path.join(root,'manifest.json'),'utf8'));
 for(const variant of ['light','dark'])for(const icon of manifest.icons)for(const size of [64,128]){
 const svg=await fs.readFile(path.join(root,icon.files[variant]),'utf8');renderJobs.push({svg,width:size,height:size,out:`png/${variant}/${size}/${icon.id}.png`});}
 for(const variant of ['light','dark']){
 const svg=await fs.readFile(path.join(root,`brand/tramvh-mark-${variant}.svg`),'utf8');renderJobs.push({svg,width:512,height:416,out:`brand/tramvh-mark-${variant}.png`});
 const app=await fs.readFile(path.join(root,`brand/tramvh-app-${variant}.svg`),'utf8');
 for(const size of [16,32,48,180,192,512])renderJobs.push({svg:app,width:size,height:size,out:`brand/tramvh-app-${variant}-${size}.png`});
 for(const badge of manifest.badges){const svg=await fs.readFile(path.join(root,`badges/${badge.id}-${variant}.svg`),'utf8');renderJobs.push({svg,width:192,height:208,out:`badges/${badge.id}-${variant}.png`});}
 }
 let written=0;
 for(let offset=0;offset<renderJobs.length;offset+=24){
 const jobs=renderJobs.slice(offset,offset+24);
 const images=await evaluate(`(async()=>{const jobs=${JSON.stringify(jobs)};const output=[];for(const job of jobs){const img=new Image();img.src='data:image/svg+xml;base64,'+btoa(unescape(encodeURIComponent(job.svg)));await img.decode();const c=document.createElement('canvas');c.width=job.width;c.height=job.height;c.getContext('2d').drawImage(img,0,0,c.width,c.height);output.push({out:job.out,png:c.toDataURL('image/png').split(',')[1]});}return output})()`);
 for(const img of images){const dest=path.join(root,img.out);await fs.mkdir(path.dirname(dest),{recursive:true});await fs.writeFile(dest,Buffer.from(img.png,'base64'));written++;}
 }
 console.log('PNG assets exported:',written);
 const preview=pathToFileURL(path.join(root,'preview.html')).href;
 const qa={icon_count:manifest.icon_count,png_count:written,checks:{},viewports:[],browser:'Chrome headless desktop; mobile emulation only',deployment:'not_performed',independent_review:'not_performed',real_device:'not_tested'};
 for(const [label,width,height,mobile,dark]of [['desktop',1440,1050,false,false],['dark',1440,1050,false,true],['mobile',390,844,true,false]]){
 await call('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile});
 await call('Page.navigate',{url:preview});
 await evaluate(`new Promise(r=>{if(document.readyState==='complete')r();else addEventListener('load',r,{once:true})})`);
 if(dark)await evaluate(`document.querySelector('#theme').click()`);
 await evaluate(`document.fonts.ready`);
 await delay(250);
 const stats=await evaluate(`({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,overflow:document.documentElement.scrollWidth>innerWidth,images:[...document.images].length,broken:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.getAttribute('src')),theme:document.documentElement.dataset.theme||'light',height:document.documentElement.scrollHeight})`);
 const screenshot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width,height:stats.height,scale:1}});
 await fs.writeFile(path.join(root,`preview-${label}.png`),Buffer.from(screenshot.data,'base64'));
 qa.viewports.push({label,...stats});
 if(label==='desktop'){
 qa.checks.search=await evaluate(`(()=>{const s=document.querySelector('#search');s.value='tu dien';s.dispatchEvent(new Event('input'));const ids=[...document.querySelectorAll('.tile')].filter(t=>!t.hidden).map(t=>t.dataset.id);s.value='';s.dispatchEvent(new Event('input'));return {query:'tu dien',ids,passed:ids.length===1&&ids[0]==='glossary'}})()`);
 qa.checks.size=await evaluate(`(()=>{document.querySelector('[data-size="20"]').click();const width=getComputedStyle(document.querySelector('.sample img')).width;document.querySelector('[data-size="32"]').click();return {width,passed:width==='20px'}})()`);
 qa.checks.theme=await evaluate(`(()=>{document.querySelector('#theme').click();const dark=document.documentElement.dataset.theme==='dark';document.querySelector('#theme').click();return {passed:dark&&document.documentElement.dataset.theme==='light'}})()`);
 }
 }
 await fs.writeFile(path.join(root,'QA.json'),JSON.stringify(qa,null,2));
 console.log(JSON.stringify(qa));
 await call('Browser.close').catch(()=>{});
 }finally{if(ws)ws.close();proc.kill();}
})().catch(e=>{console.error(e);process.exitCode=1});
