(() => {
    const groups = [['Chuong_STm00','Chương 0'],['Chuong_STm01','Chương 1'],['Chuong_STm02','Chương 2'],['03_BangText_UI_KyNang','Bảng Achievement']];
    const group = document.getElementById('group'), file = document.getElementById('file'), blocks = document.getElementById('blocks'), status = document.getElementById('status'), more = document.getElementById('more');
    let data, shown = 0, serial = 0;
    const node = (tag,text,cls) => { const e=document.createElement(tag); if(text!==undefined)e.textContent=text; if(cls)e.className=cls; return e; };
    for(const [value,label] of groups){const option=node('option',label);option.value=value;group.append(option);}
    function render(){
        const selected=data?.files.find(item=>item.file_id===file.value); if(!selected)return;
        const end=Math.min(shown+40,selected.blocks.length);
        for(const row of selected.blocks.slice(shown,end)){
            const card=node('article',undefined,'block');card.append(node('h2',`${selected.file_id} · Khối ${row.order}${row.kind?' · '+row.kind:''}${row.speaker_vi?' · '+row.speaker_vi:''}`));
            const grid=node('div',undefined,'texts');
            for(const [key,label] of [['en','EN'],['jp','JP'],['cn','CN'],['vi','VI']]){
                const panel=node('section');panel.append(node('h3',label));panel.append(node('p',row[key] || ''));grid.append(panel);
            }
            card.append(grid);blocks.append(card);
        }
        shown=end;more.hidden=shown>=selected.blocks.length;status.textContent=`${selected.file_id}: ${selected.blocks.length} khối · đang hiển thị ${shown}`;
    }
    function selectFile(){shown=0;blocks.replaceChildren();render();}
    async function selectGroup(){
        const request=++serial;status.textContent='Đang tải dữ liệu…';blocks.replaceChildren();more.hidden=true;file.replaceChildren();
        try{
            const response=await fetch('/api/sheet_reference?group='+encodeURIComponent(group.value),{cache:'no-store'});if(!response.ok)throw Error('Không tải được nguồn Merge từ Google Sheet.');
            const result=await response.json();if(request!==serial)return;data=result;
            for(const item of data.files){const option=node('option',`${item.file_id} (${item.blocks.length} khối)`);option.value=item.file_id;file.append(option);}
            selectFile();
        }catch(error){if(request===serial)status.textContent=error.message;}
    }
    group.addEventListener('change',selectGroup);file.addEventListener('change',selectFile);more.addEventListener('click',render);selectGroup();
})();
