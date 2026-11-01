/** The list previews the current version before opening any editor. */
function renderListMode() {
    const container=document.getElementById('listModeContainer');if(!container)return;container.replaceChildren();
    const label=(tag,cls,text)=>{const e=document.createElement(tag);e.className=cls;e.textContent=text;return e;};
    let rendered=0;
    const more=document.createElement('button');more.className='btn-direction collab-load-more';more.type='button';
    const append=()=>{
        more.remove();const end=Math.min(filteredLines.length,rendered+80);
        for(let idx=rendered;idx<end;idx++){
            const item=filteredLines[idx],card=document.createElement('div');card.className='table-row-card';card.dataset.lineId=item.line_id;
            const top=label('div','table-row-top',''),speaker=label('div','table-row-speaker',item.speaker || 'Dẫn chuyện');speaker.append(label('span','collab-line-id','#'+item.line_id));top.append(speaker);card.append(top,label('p','table-row-en',item.en || ''),CollaborationView.summary(item));
            const buttons=label('div','collab-actions','');
            for(const [text,handler]of [[Collaboration.hasText(item)?'Đề xuất sửa':'Dịch câu này',()=>CollaborationView.openEdit(item)],['Xem lịch sử',()=>CollaborationView.openHistory(item)],['Báo vấn đề',()=>CollaborationView.openEdit(item,undefined,{mode:'report'})]]){const button=label('button','btn-direction',text);button.type='button';button.addEventListener('click',handler);buttons.append(button);}card.append(buttons);container.append(card);
        }
        rendered=end;if(rendered<filteredLines.length){more.textContent=`Xem thêm câu (${rendered}/${filteredLines.length})`;container.append(more);}
    };
    more.onclick=append;append();
}
