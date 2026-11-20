"""Stage all three locales and glossary for the existing collaboration workbook."""
import base64
import csv
import gzip
import hashlib
import json
import pathlib
import sys
from collections import defaultdict
import export_full_sources_sheets_20261103 as export

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'work/runs/sheets_unified_sources_20261103_r04'
GLOSSARY = ROOT / 'dist/StellaSora_Glossary_TongHop_20261101_r06'


def serial(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def encode_requests(sheet_id, start, rows):
    requests = []
    for offset in range(0, len(rows), 200):
        group = rows[offset:offset+200]
        requests.append({'updateCells': {
            'range': {'sheetId': sheet_id, 'startRowIndex': start+offset, 'endRowIndex': start+offset+len(group), 'startColumnIndex': 0, 'endColumnIndex': len(rows[0])},
            'rows': [{'values': [{'userEnteredValue': {'numberValue': v} if isinstance(v, (int, float)) else {'stringValue': v}} for v in row]} for row in group],
            'fields': 'userEnteredValue'}})
    payload = serial({'requests': requests}).encode('utf-8')
    return payload, base64.b64encode(gzip.compress(payload, compresslevel=6, mtime=0)).decode('ascii')


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    # Reuse the verified exporter and add EN through the same schema.
    export.OUT = OUT / 'source_matrices'
    source_code = pathlib.Path(export.__file__).read_text(encoding='utf-8')
    source_code = source_code.replace("for loc in ('CN', 'JP'):", "for loc in ('CN', 'EN', 'JP'):")
    scope = dict(export.__dict__)
    scope['__name__'] = 'unified_source_export'
    exec(compile(source_code, export.__file__, 'exec'), scope)
    scope['OUT'] = export.OUT
    scope['main']()
    source_plan = json.loads((export.OUT / 'PLAN.json').read_text(encoding='utf-8'))
    glossary_bytes = (GLOSSARY / 'GLOSSARY_TONG_HOP.json').read_bytes()
    canonical = json.loads(glossary_bytes.decode('utf-8-sig'))
    literals = set()

    def collect(value):
        if isinstance(value, str):
            literals.add(value)
        elif isinstance(value, list):
            for v in value: collect(v)
        elif isinstance(value, dict):
            for v in value.values(): collect(v)
    collect(canonical)
    glossary_specs = [
        ('01_DA_CO_BAN_VI.csv','GL_01_HienCo'),
        ('02_THUAT_NGU_NGUON_CU.csv','GL_02_NguonCu'),
        ('03_CHO_PHAN_LOAI_TU_DOT_TRUOC.csv','GL_03_ChoPhanLoai'),
        ('04_MAU_THUAN_CAN_DOI_CHIEU.csv','GL_04_MauThuan'),
        ('05_UNG_VIEN_BANG_EN.csv','GL_05_UngVienBang'),
        ('06_UNG_VIEN_CANH_EN.csv','GL_06_UngVienCanh'),
        ('07_CAP_EN_VI_CO_SAN_CHUA_DUYET.csv','GL_07_CapENVI'),
        ('08_UNG_VIEN_201_THEO_NGON_NGU.csv','GL_08_201_TheoLocale'),
        ('09_UNG_VIEN_CAN_PHAN_LOAI.csv','GL_09_CanPhanLoai')]
    specs = []
    for entry in source_plan['sheets']:
        if entry['title'] != 'ThongTin':
            specs.append({'title': 'NG_'+entry['title'], 'path': str(export.OUT / entry['file']), 'description': entry['description'], 'kind': 'source'})
    glossary_inputs = []
    prefix_decoded = 0
    for filename, title in glossary_specs:
        b = (GLOSSARY / filename).read_bytes()
        with (GLOSSARY / filename).open(encoding='utf-8-sig', newline='') as stream:
            matrix = list(csv.reader(stream))
        for row in matrix:
            for i, v in enumerate(row):
                # Remove only documented CSV formula-escaping with canonical evidence.
                if len(v)>1 and v[0]=="'" and v[1] in '=+-@\t\r' and v not in literals and v[1:] in literals:
                    row[i] = v[1:]
                    prefix_decoded += 1
        if title == 'GL_01_HienCo':
            fields = ['id','domain','cn','en','jp','vi','status','author','reviewer','refs','note','vi_old']
            old_header = matrix[0]
            matrix = [fields] + [[row[old_header.index(k)] for k in fields] for row in matrix[1:]]
            # Directly restore scalar source values from JSON for the main glossary.
            entries = {r['id']: r for r in canonical['existing_candidate_r05']}
            for row in matrix[1:]:
                original = entries[row[0]]
                for k in fields:
                    if k != 'refs': row[fields.index(k)] = str(original.get(k) or '')
        path = OUT / (title+'.json')
        path.write_text(serial(matrix), encoding='utf-8')
        specs.append({'title':title,'path':str(path),'description':filename+'; trạng thái và phạm vi theo nguồn r06, không tạo phê duyệt mới.','kind':'glossary'})
        glossary_inputs.append({'file':filename,'sha256':hashlib.sha256(b).hexdigest(),'rows':len(matrix)-1})
    raw_text = glossary_bytes.decode('utf-8')
    raw_rows = [['ID nguồn','Nội dung gốc','Tệp']]+[[f'GLOSSARY_TONG_HOP.json::part/{i//12000:05}',raw_text[i:i+12000],'GLOSSARY_TONG_HOP.json'] for i in range(0,len(raw_text),12000)]
    raw_path = OUT/'GL_10_DuLieuGoc.json'
    raw_path.write_text(serial(raw_rows),encoding='utf-8')
    assert ''.join(r[1] for r in raw_rows[1:]).encode('utf-8') == glossary_bytes
    specs.append({'title':'GL_10_DuLieuGoc','path':str(raw_path),'description':'JSON glossary nguyên vẹn, giữ đủ nguồn/ngữ cảnh và chi tiết review.','kind':'raw_glossary'})
    chunk_dir=OUT/'payloads';chunk_dir.mkdir()
    plan=[];chunks=[];special=[];sentinels=[]
    for index, spec in enumerate(specs):
        rows=json.loads(pathlib.Path(spec['path']).read_text(encoding='utf-8'))
        cols=len(rows[0]);assert all(len(row)==cols for row in rows)
        assert all(isinstance(v,(str,int,float)) for row in rows for v in row)
        assert all(not isinstance(v,str) or len(v.encode('utf-16-le'))//2<=49000 for row in rows for v in row)
        sheet_id=2101030001+index
        spec.update({'sheetId':sheet_id,'row_count':len(rows),'columns':cols,'characters':[sum(len(str(row[c])) for row in rows[1:]) for c in range(cols)],'matrix_sha256':hashlib.sha256(pathlib.Path(spec['path']).read_bytes()).hexdigest()})
        for i in sorted({0,1,len(rows)//2,len(rows)-1}):sentinels.append({'title':spec['title'],'row':i+1,'values':rows[i]})
        for ri,row in enumerate(rows):
            for ci,v in enumerate(row):
                if isinstance(v,str) and (any(ord(ch)<32 and ch not in '\n\r\t' for ch in v) or v.startswith('=')):
                    special.append({'title':spec['title'],'row':ri+1,'column':ci+1,'value':v})
        start=0
        batch_size=100 if spec['title'].endswith('DuLieuGoc') else 5000
        while start<len(rows):
            end=min(start+batch_size,len(rows))
            while True:
                payload,b64=encode_requests(sheet_id,start,rows[start:end])
                if len(payload)<=1700000 and len(b64)<=1000000:break
                assert end-start>1
                end=start+max(1,(end-start)//2)
                batch_size=end-start
            n=len(chunks);filename=f'{n:04}.b64'
            (chunk_dir/filename).write_text(b64,encoding='ascii')
            chunks.append({'number':n,'file':filename,'title':spec['title'],'sheetId':sheet_id,'start':start,'end':end,'row_count':end-start,'payload_bytes':len(payload),'base64_chars':len(b64),'payload_sha256':hashlib.sha256(payload).hexdigest()})
            start=end
        plan.append(spec)
    (OUT/'PLAN.json').write_text(json.dumps({'sheets':plan,'chunks':chunks,'nav_sheetId':2101030000},ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'SENTINELS.json').write_text(serial(sentinels),encoding='utf-8')
    (OUT/'SPECIAL.json').write_text(serial(special),encoding='utf-8')
    (OUT/'GLOSSARY_INPUTS.json').write_text(json.dumps({'json_sha256':hashlib.sha256(glossary_bytes).hexdigest(),'csv_inputs':glossary_inputs,'csv_formula_prefixes_decoded':prefix_decoded},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'sheet_count':len(plan),'chunks':len(chunks),'new_cells':sum(s['row_count']*s['columns'] for s in plan),'data_rows':sum(s['row_count']-1 for s in plan),'glossary_rows':sum(s['row_count']-1 for s in plan if s['kind']=='glossary'),'special':len(special)},ensure_ascii=False))


if __name__=='__main__':main()
