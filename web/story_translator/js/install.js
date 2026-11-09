(() => {
    const button = document.getElementById('installAppBtn');
    const dialog = document.getElementById('installHelpDialog');
    const closeButton = document.getElementById('installHelpClose');
    const dismissButton = document.getElementById('installHelpDismiss');
    const text = document.getElementById('installHelpText');
    const steps = document.getElementById('installHelpSteps');
    if (!button) return;

    let deferredPrompt = null;
    const isIos = /iPhone|iPad|iPod/i.test(navigator.userAgent);
    const isStandalone = window.matchMedia?.('(display-mode: standalone)').matches || window.navigator.standalone === true;

    const openHelp = (mode) => {
        if (!dialog || !text || !steps) return;
        if (mode === 'ios') {
            text.textContent = 'Safari không hiện hộp cài đặt tự động. Bạn có thể thêm một lối tắt của TramVH vào Màn hình chính:';
            steps.innerHTML = '<li>Nhấn nút Chia sẻ trong Safari.</li><li>Chọn “Thêm vào Màn hình chính”.</li><li>Nhấn “Thêm” để hoàn tất.</li>';
        } else if (mode === 'shortcut') {
            text.textContent = 'Trình duyệt hiện tại chưa hỗ trợ cài PWA tự động. Hãy thêm lối tắt TramVH vào Màn hình chính:';
            steps.innerHTML = '<li>Mở menu của trình duyệt (⋮ hoặc Chia sẻ).</li><li>Chọn “Thêm vào màn hình chính” hoặc “Tạo lối tắt”.</li><li>Xác nhận tên TramVH rồi nhấn “Thêm”.</li>';
        } else {
            text.textContent = 'TramVH đã được cài trên thiết bị này. Bạn có thể mở ứng dụng từ Màn hình chính.';
            steps.innerHTML = '';
        }
        if (typeof dialog.showModal === 'function') dialog.showModal();
        else dialog.setAttribute('open', '');
    };

    const closeHelp = () => {
        if (typeof dialog?.close === 'function') dialog.close();
        else dialog?.removeAttribute('open');
    };

    button.addEventListener('click', async () => {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            await deferredPrompt.userChoice.catch(() => undefined);
            deferredPrompt = null;
            return;
        }
        openHelp(isStandalone ? 'installed' : (isIos ? 'ios' : 'shortcut'));
    });

    closeButton?.addEventListener('click', closeHelp);
    dismissButton?.addEventListener('click', closeHelp);
    dialog?.addEventListener('click', (event) => {
        if (event.target === dialog) closeHelp();
    });

    window.addEventListener('beforeinstallprompt', (event) => {
        event.preventDefault();
        deferredPrompt = event;
    });
    window.addEventListener('appinstalled', () => {
        deferredPrompt = null;
    });

    if ('serviceWorker' in navigator && location.protocol !== 'file:') {
        navigator.serviceWorker.register('./service-worker.js', { scope: './' }).catch(() => undefined);
    }
})();
