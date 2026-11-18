'use strict';
// Read-only decoders for offline resource export. Never loads or executes game code.
const fs = require('node:fs');
const crypto = require('node:crypto');
const decoder = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true });
const sha256 = b => crypto.createHash('sha256').update(b).digest('hex');
const utf8 = b => decoder.decode(b);

function lz4Block(src, expected) {
  const out = Buffer.alloc(expected); let i = 0, j = 0;
  function length(n) { if (n === 15) { let x; do { if (i >= src.length) throw Error('LZ4 length truncated'); x=src[i++]; n+=x; } while(x===255); } return n; }
  while (i < src.length) {
    const token=src[i++], literals=length(token>>>4);
    if (i+literals>src.length || j+literals>expected) throw Error('LZ4 literal overflow');
    src.copy(out,j,i,i+literals); i+=literals; j+=literals;
    if(i===src.length) break;
    if(i+2>src.length) throw Error('LZ4 offset truncated');
    const offset=src.readUInt16LE(i); i+=2;
    if(!offset || offset>j) throw Error('LZ4 invalid offset');
    const match=length(token&15)+4;
    if(j+match>expected) throw Error('LZ4 match overflow');
    for(let k=0;k<match;k++) { out[j]=out[j-offset]; j++; }
  }
  if(j!==expected) throw Error(`LZ4 size mismatch ${j}/${expected}`);
  return out;
}
const XOR_KEY=Buffer.from('&^^%#$#_$!@![]<_>?GHBFR_7481SDR_');
function xor(b) { const out=Buffer.from(b); for(let i=0;i<out.length;i++) out[i]^=XOR_KEY[i%XOR_KEY.length]; return out; }
function xxteaDecrypt(data) {
  if(!data.length) return data;
  if(data.length%4) throw Error('XXTEA non-word-aligned payload');
  const n=data.length/4; if(n<=1) return Buffer.from(data);
  const v=new Uint32Array(n); for(let i=0;i<n;i++) v[i]=data.readUInt32LE(i*4);
  const keyBytes=Buffer.from('a921a467c7d7df396e60909c31225bd2','hex');
  const key=Array.from({length:4},(_,i)=>keyBytes.readUInt32LE(i*4));
  let sum=Math.imul(6+Math.floor(52/n),0x9e3779b9)>>>0, y=v[0];
  function mx(z,y,p,e) { return (((((z>>>5)^(y<<2))+((y>>>3)^(z<<4)))>>>0)^(((sum^y)+(key[(p&3)^e]^z))>>>0))>>>0; }
  while(sum!==0) {
    const e=(sum>>>2)&3;
    for(let p=n-1;p>0;p--) { v[p]=(v[p]-mx(v[p-1],y,p,e))>>>0; y=v[p]; }
    v[0]=(v[0]-mx(v[n-1],y,0,e))>>>0; y=v[0]; sum=(sum-0x9e3779b9)>>>0;
  }
  const out=Buffer.alloc(n*4); for(let i=0;i<n;i++) out.writeUInt32LE(v[i],i*4);
  const len=v[n-1]; return len>=(n-1)*4-3 && len<=(n-1)*4 ? out.subarray(0,len) : out;
}
function readArchive(file) {
  const raw=fs.readFileSync(file);
  if(!raw.subarray(0,4).equals(Buffer.from([0x1a,0x42,0x41,0x52]))) throw Error('Invalid BAR magic');
  const version=raw.readUInt32LE(4),flags=raw.readUInt32LE(8),original=raw.readUInt32LE(12),compressed=raw.readUInt32LE(16),count=raw.readUInt32LE(20);
  if(version!==102 || original!==count*20 || compressed>raw.length-24) throw Error('Invalid BAR header');
  let directory=raw.subarray(24,24+compressed);
  if(flags&0x10) directory=xor(directory);
  if(flags&1) directory=lz4Block(directory,original);
  if(directory.length!==original) throw Error('Invalid BAR directory length');
  const entries=[];
  for(let i=0;i<count;i++) { const o=i*20; entries.push({index:i,hash_hex:'0x'+directory.readBigUInt64LE(o).toString(16).padStart(16,'0'),offset:directory.readUInt32LE(o+8),origin_size:directory.readUInt32LE(o+12),size:directory.readUInt32LE(o+16)}); }
  const base=entries.length && entries[0].offset<24+compressed ? 24+compressed : 0;
  for(const e of entries) if(base+e.offset+e.size>raw.length) throw Error('BAR entry outside archive');
  return {file,sha256:sha256(raw),version,flags,entries,extract(e) { let b=raw.subarray(base+e.offset,base+e.offset+e.size); if(flags&0x1000)b=xor(b); if(flags&0x100)b=lz4Block(b,e.origin_size); if(b.length!==e.origin_size)throw Error('BAR payload size mismatch'); return b; }};
}

function parseLua53(data) {
  let pos=0; const stringRecords=[],functions=[];
  function bytes(n) { if(!Number.isSafeInteger(n)||n<0||pos+n>data.length)throw Error(`Lua truncated at ${pos} (+${n})`); const b=data.subarray(pos,pos+n); pos+=n;return b; }
  const byte=()=>bytes(1)[0], int=()=>bytes(4).readInt32LE();
  if(!bytes(4).equals(Buffer.from([27,76,117,97])) || byte()!==0x53 || byte()!==0)throw Error('Expected Lua 5.3 binary chunk');
  if(!bytes(6).equals(Buffer.from([0x19,0x93,13,10,26,10])))throw Error('Invalid Lua signature');
  const sizes=Array.from(bytes(5)); if(sizes.join()!=='4,8,4,8,8')throw Error('Unsupported Lua ABI '+sizes);
  if(bytes(8).readBigInt64LE()!==0x5678n || bytes(8).readDoubleLE()!==370.5)throw Error('Unsupported Lua endianness');
  const mainUpvalues=byte();
  function str() { let n=byte(); if(n===255){const b=bytes(8).readBigUInt64LE();if(b>BigInt(data.length))throw Error('Lua string overflow');n=Number(b);} if(!n)return null; const b=bytes(n-1); try{return utf8(b);}catch{return {encoding:"base64",data:b.toString("base64")};} }
  function count() { const n=int();if(n<0||n>data.length)throw Error('Invalid Lua count');return n; }
  function proto(id,parentSource) {
    const source=str()??parentSource, lineDefined=int(),lastLineDefined=int(),params=byte(),vararg=byte(),maxStack=byte();
    const fn={id,source,lineDefined,lastLineDefined,params,vararg,maxStack,code:[],constants:[],children:[]}; functions.push(fn);
    for(let n=count();n>0;n--)fn.code.push(bytes(4).readUInt32LE());
    for(let n=count(),i=0;i<n;i++) {
      const offset=pos,type=byte();let value;
      if(type===0)value=null;else if(type===1)value=!!byte();else if(type===3)value=bytes(8).readDoubleLE();else if(type===0x13)value=bytes(8).readBigInt64LE().toString();else if(type===4||type===0x14)value=str();else throw Error('Invalid Lua constant type '+type);
      fn.constants.push({type,value});
      if((type===4||type===0x14)&&typeof value==="string")stringRecords.push({id:`${id}:K${i}`,function:id,constant:i,offset,text:value});
    }
    bytes(count()*2);
    for(let n=count(),i=0;i<n;i++)fn.children.push(proto(`${id}/${i}`,source));
    bytes(count()*4);
    for(let n=count();n>0;n--){str();int();int();}
    for(let n=count();n>0;n--)str();
    return fn;
  }
  const main=proto('0',null);
  if(pos!==data.length)throw Error(`Trailing Lua bytes ${data.length-pos}`);
  return {source:main.source,mainUpvalues,functions,stringRecords};
}


// Decode only literal table constructors. Unsupported instructions fail closed.
function literalLuaTable(parsed) {
  if(parsed.functions.length!==1)throw Error('Nested functions in literal scene');
  const fn=parsed.functions[0],regs=[];
  const k=i=>{const c=fn.constants[i];if(!c)throw Error('Lua constant out of range');if(c.type===19){const v=BigInt(c.value);if(v>BigInt(Number.MAX_SAFE_INTEGER)||v<BigInt(Number.MIN_SAFE_INTEGER))throw Error('Integer out of safe range');return Number(v);}return c.value;};
  const rk=x=>x&256?k(x&255):regs[x];
  function set(t,key,value){if(!(t instanceof Map)||key==null||value===undefined)throw Error('Invalid literal table assignment');t.set(key,value);}
  function plain(t){if(!(t instanceof Map))return t;const keys=[...t.keys()];if(keys.length&&keys.every(x=>Number.isInteger(x)&&x>=1)&&Math.max(...keys)===keys.length)return Array.from({length:keys.length},(_,i)=>plain(t.get(i+1)));const o={};for(const [key,v]of t)o[String(key)]=plain(v);return o;}
  for(let pc=0;pc<fn.code.length;pc++) {
    const i=fn.code[pc],op=i&63,a=(i>>>6)&255,b=i>>>23,c=(i>>>14)&511,bx=i>>>14;
    switch(op){
      case 0:regs[a]=regs[b];break;
      case 1:regs[a]=k(bx);break;
      case 2:if((fn.code[++pc]&63)!==46)throw Error('LOADKX without EXTRAARG');regs[a]=k(fn.code[pc]>>>6);break;
      case 3:regs[a]=!!b;if(c)pc++;break;
      case 4:for(let j=a;j<=a+b;j++)regs[j]=null;break;
      case 10:set(regs[a],rk(b),rk(c));break;
      case 11:regs[a]=new Map();break;
      case 25:if(typeof regs[b]!=="number")throw Error("Non-numeric unary minus");regs[a]=-regs[b];break;
      case 38:if(b!==2)throw Error('Expected single literal table return');return plain(regs[a]);
      case 43:{if(!b)throw Error('Dynamic SETLIST');let block=c;if(!block){if((fn.code[++pc]&63)!==46)throw Error('SETLIST without EXTRAARG');block=fn.code[pc]>>>6;}for(let j=1;j<=b;j++)set(regs[a],(block-1)*50+j,regs[a+j]);break;}
      default:throw Error('Not a literal table constructor: opcode '+op+' at '+pc);
    }
  }
  throw Error('Missing literal table return');
}
module.exports={sha256,utf8,lz4Block,xxteaDecrypt,readArchive,parseLua53,literalLuaTable};

