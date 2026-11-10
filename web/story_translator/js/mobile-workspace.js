(() => {
    const mobile = () => matchMedia('(max-width:700px)').matches;
    const reference=document.getElementById('referenceQuoteBox');
    const referenceDetails=document.createElement('details'), referenceTitle=document.createElement('summary');
    referenceDetails.className='mobile-reference-details';referenceTitle.textContent='Bản dịch cũ (tham khảo)';referenceDetails.append(referenceTitle);
    const referenceLayout=()=>{
        if(mobile() && !referenceDetails.isConnected){reference.before(referenceDetails);referenceDetails.append(reference);}
        else if(!mobile() && referenceDetails.isConnected){referenceDetails.before(reference);referenceDetails.remove();}
        referenceDetails.hidden=reference.style.display==='none';
    };
    new MutationObserver(referenceLayout).observe(reference,{attributes:true,attributeFilter:['style']});
    matchMedia('(max-width:700px)').addEventListener('change',referenceLayout);referenceLayout();
    const scope = document.querySelector('.scope-disclosure');
    const scopeText = document.createElement('span'); scopeText.className='mobile-scope-summary'; scope.querySelector('summary').append(scopeText);
    const nav = document.createElement('nav'); nav.className='mobile-line-nav'; nav.setAttribute('aria-label','Chuyển câu');
    const previous=document.createElement('button'), next=document.createElement('button'), counter=document.createElement('span');
    previous.type=next.type='button';previous.textContent='← Câu trước';next.textContent='Câu kế →';
    previous.onclick=()=>{navigateLine(-1);document.querySelector('.dialogue-speech-box')?.scrollIntoView({block:'start'});};
    next.onclick=()=>{navigateLine(1);document.querySelector('.dialogue-speech-box')?.scrollIntoView({block:'start'});};
    nav.append(previous,counter,next);document.body.append(nav);
    const refresh=()=>{
        scopeText.textContent=['chapterSelect','sceneSelect','filterSelect'].map(id=>{const s=document.getElementById(id);return s?.selectedOptions[0]?.textContent;}).filter(Boolean).join(' · ');
        const game=document.getElementById('tabGameMode').classList.contains('active');
        nav.hidden=!game || !filteredLines.length;document.body.classList.toggle('mobile-vn-nav',game && filteredLines.length>0);
        counter.textContent=document.getElementById('counterIndicator').textContent;
        previous.disabled=currentIndex<=0;next.disabled=currentIndex>=filteredLines.length-1;
    };
    new MutationObserver(refresh).observe(document.getElementById('counterIndicator'),{childList:true,subtree:true});
    new MutationObserver(refresh).observe(document.getElementById('tabGameMode'),{attributes:true,attributeFilter:['class']});
    new MutationObserver(refresh).observe(document.querySelector('.selectors-wrap'),{childList:true,subtree:true});
    document.querySelector('.selectors-wrap').addEventListener('change',refresh);refresh();
    // Follow the visible area when the on-screen keyboard opens.
    const updateViewport=()=>{
        if(!mobile())return;
        const viewport=window.visualViewport, dialog=document.getElementById('collaborationDialog');
        const keyboard=viewport && viewport.height < innerHeight-140;
        document.documentElement.style.setProperty('--mobile-visible-height',`${viewport?.height || innerHeight}px`);
        document.documentElement.style.setProperty('--mobile-visible-top',`${viewport?.offsetTop || 0}px`);
        document.body.classList.toggle('mobile-keyboard-open',!!keyboard);
        if(dialog.open && dialog.contains(document.activeElement))requestAnimationFrame(()=>document.activeElement?.scrollIntoView({block:'nearest'}));
    };
    window.visualViewport?.addEventListener('resize',updateViewport);window.visualViewport?.addEventListener('scroll',updateViewport);
    window.addEventListener('resize',updateViewport);updateViewport();
    const loading=document.getElementById('chapterLoadingOverlay');
    const retry=document.createElement('button');retry.type='button';retry.className='mobile-loading-retry';retry.textContent='Tải lại trang';retry.onclick=()=>location.reload();
    const wait=document.createElement('p');wait.className='mobile-loading-wait';wait.textContent='Kết nối đang chậm. Bạn có thể chờ thêm hoặc tải lại trang.';
    loading.querySelector('.chapter-loading-card').append(wait,retry);let timer;
    const loadingState=()=>{clearTimeout(timer);loading.classList.remove('mobile-loading-slow');if(!loading.hidden)timer=setTimeout(()=>loading.classList.add('mobile-loading-slow'),15000);};
    new MutationObserver(loadingState).observe(loading,{attributes:true,attributeFilter:['hidden']});loadingState();
})();
