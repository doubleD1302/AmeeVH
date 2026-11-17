// Kiểm tra: mã Moderator đang có trong D1 (bản sao lưu) được băm theo cách nào?
//
// Cách dùng (chạy trên máy của bạn, mã không rời khỏi terminal):
//   node tools/verify_tramvh_moderator_hash.mjs "C:\YostarGames\StellaSora_EN\StellaSora_VietHoa\backups\tramvh_pre_95_glossary_20261117\tramvh_d1_backup.sql"
// Rồi dán MỘT mã Moderator còn hiệu lực (xem trong Admin Portal -> Moderator -> Hiện).
//
// Script chỉ in kết quả "khớp / không khớp" và tên cách băm; không in mã, không in mã băm.
// Tùy chọn: đặt biến môi trường TRAMVH_KEY (một REVIEWER_KEY) để thử thêm các cách băm có khóa bí mật.
import {readFileSync} from 'node:fs';
import {createHash, createHmac} from 'node:crypto';
import {createInterface} from 'node:readline/promises';

const file = process.argv[2];
if (!file) { console.error('Thiếu đường dẫn tới tramvh_d1_backup.sql'); process.exit(2); }

const sql = readFileSync(file, 'utf8');
// Mỗi hàng được ghi thành một câu INSERT riêng: quét tất cả, không chỉ câu đầu.
const marker = 'INSERT INTO "moderator_codes"';
const stored = new Set();
let statements = 0;
for (let at = sql.indexOf(marker); at >= 0; at = sql.indexOf(marker, at + marker.length)) {
  statements += 1;
  const next = sql.indexOf('\nINSERT INTO', at + marker.length);
  const section = sql.slice(at, next < 0 ? at + 20000 : next);
  for (const match of section.matchAll(/'([a-f0-9]{64})'/g)) stored.add(match[1]);
}
if (!statements) { console.error('Không thấy dữ liệu moderator_codes trong file.'); process.exit(2); }
console.log(`Tìm thấy ${statements} dòng Moderator, ${stored.size} mã băm 64 ký tự trong bản sao lưu.`);

const rl = createInterface({input: process.stdin, output: process.stdout});
const typed = (await rl.question('Dán một mã Moderator: ')).trim();
rl.close();
if (!typed) { console.error('Chưa nhập mã.'); process.exit(2); }

const sha = text => createHash('sha256').update(text).digest('hex');
const normalized = typed.normalize('NFKC').toUpperCase().replace(/[^A-Z0-9]/g, '');
const raw = typed.normalize('NFKC').trim();
const key = process.env.TRAMVH_KEY || '';

const schemes = {
  'A: sha256(mã chuẩn hóa: chữ hoa, bỏ dấu gạch)  [Worker mới dùng làm chuẩn]': sha(normalized),
  'B: sha256(mã đúng như gõ, đã cắt khoảng trắng)  [Worker mới có hỗ trợ]': sha(raw),
  'C: sha256(mã chữ hoa, giữ dấu gạch)             [Worker mới có hỗ trợ]': sha(raw.toUpperCase()),
};
const keyed = {};
if (key) {
  for (const [name, value] of [['mã chuẩn hóa', normalized], ['mã như gõ', raw], ['mã chữ hoa', raw.toUpperCase()]]) {
    keyed[`D: hmac-sha256(khóa, ${value === normalized ? 'mã chuẩn hóa' : name})  [Worker mới CHƯA hỗ trợ]`] = createHmac('sha256', key).update(value).digest('hex');
    keyed[`E: sha256(khóa + ':' + ${name})  [Worker mới CHƯA hỗ trợ]`] = sha(key + ':' + value);
    keyed[`F: sha256(${name} + ':' + khóa)  [Worker mới CHƯA hỗ trợ]`] = sha(value + ':' + key);
  }
}

let matched = 0;
for (const [name, hash] of Object.entries({...schemes, ...keyed})) {
  if (stored.has(hash)) { matched += 1; console.log('KHỚP  ->', name); }
}
if (!matched) {
  console.log('KHÔNG KHỚP cách băm nào đã thử.');
  console.log('Có thể mã vừa bị thu hồi / gõ sai, hoặc D1 dùng cách băm có khóa bí mật (thử đặt TRAMVH_KEY rồi chạy lại).');
  process.exit(1);
}
