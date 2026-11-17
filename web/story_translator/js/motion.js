/**
 * motion.js
 * Small, optional polish: replays the "line enter" animation when the user moves to another line and
 * tells the list when it is worth animating. Never changes data or behaviour; if anything here fails the app runs as before.
 */
(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
    let lastLine = '', lastIndex = -1, lastList = '';

    const wrap = (name, after) => {
        const original = window[name];
        if (typeof original !== 'function') return;
        window[name] = function (...args) {
            const result = original.apply(this, args);
            try { after(); } catch (_) { /* animation is optional */ }
            return result;
        };
    };

    const replay = (selectors, dx, dy) => {
        for (const selector of selectors) {
            const node = document.querySelector(selector);
            if (!node) continue;
            node.style.setProperty('--tram-dx', dx + 'px');
            node.style.setProperty('--tram-dy', dy + 'px');
            node.classList.remove('tram-enter');
            void node.offsetWidth; // restart the animation
            node.classList.add('tram-enter');
        }
    };

    wrap('renderCurrentLine', () => {
        const item = filteredLines?.[currentIndex];
        const key = item ? (currentChapterData?.chapter_id || '') + ':' + item.line_id : '';
        const moved = key && key !== lastLine;
        const direction = currentIndex > lastIndex ? 1 : -1;
        lastLine = key; lastIndex = currentIndex;
        if (!moved || reduce.matches) return;
        replay(['.dialogue-speech-box', '#currentLineCollaboration', '.translation-input-box'], 14 * direction, 6);
    });

    wrap('renderListMode', () => {
        const container = document.getElementById('listModeContainer');
        if (!container) return;
        const key = (currentChapterData?.chapter_id || '') + ':' + (filteredLines?.length || 0) + ':' + (filteredLines?.[0]?.line_id || '');
        // Same chapter and filter (e.g. a re-render after saving): do not replay the entrance.
        container.dataset.motion = key !== lastList && !reduce.matches ? 'on' : 'off';
        lastList = key;
    });
})();
