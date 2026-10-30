/**
 * AppController.js
 * Bộ điều phối trung tâm khởi tạo ứng dụng, đăng ký lắng nghe sự kiện và chuỗi nạp dữ liệu ban đầu
 */

const AppController = {
    async init() {
        updateThemeButton();
        await loadCharactersMetadata();
        loadProfile();
        await loadChaptersList();
        await loadGlossaryTerms();
        initAudio();
    }
};
