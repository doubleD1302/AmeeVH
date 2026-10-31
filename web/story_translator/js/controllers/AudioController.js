/**
 * AudioController.js
 * Quản lý khởi tạo âm thanh, danh sách phát nhạc vòng lặp 2 bài (Title Screen & Official Web Themes) và voice clip
 */

const BGM_PLAYLIST = [
    {
        id: "launch_title",
        title: "Title Screen Theme (Nhạc Màn Hình Khởi Động)",
        shortName: "Màn Hình Khởi Động",
        src: "official_assets/bgm/bgm_01_launch_title.mp3",
        duration: "3:17",
        tag: "1/2"
    },
    {
        id: "official_web_theme",
        title: "Official Website Theme (Nhạc Trang Chủ Official)",
        shortName: "Trang Chủ Official",
        src: "official_assets/bgm/bgm_02_official_web_theme.mp3",
        duration: "1:54",
        tag: "2/2"
    }
];

let currentBgmIndex = 0;
let isBgmPlaying = false;

function initAudio() {
    const bgm = document.getElementById("bgmAudio");
    if (!bgm) return;
    bgm.volume = 0.35;
    bgm.src = BGM_PLAYLIST[currentBgmIndex].src;
    
    // Tự động chuyển tiếp bài tiếp theo khi kết thúc bài hiện tại (vòng lặp 2 bài vô tận)
    bgm.addEventListener("ended", () => {
        nextBgm(true);
    });

    updateBgmUI();
}

function updateBgmUI() {
    const btn = document.getElementById("bgmToggleBtn");
    const track = BGM_PLAYLIST[currentBgmIndex];
    if (btn) {
        btn.title = `Nhạc [${track.tag}]: ${track.title} (Bấm để ${isBgmPlaying ? 'Tạm Dừng' : 'Phát'}, Alt+M)`;
        btn.setAttribute("aria-label", btn.title);
        btn.setAttribute("aria-pressed", String(isBgmPlaying));
        if (isBgmPlaying) {
            btn.classList.add("active");
            btn.innerHTML = tramIcon("pause");
        } else {
            btn.classList.remove("active");
            btn.innerHTML = tramIcon("music");
        }
    }
}

function toggleBgm() {
    const bgm = document.getElementById("bgmAudio");
    if (!bgm) return;

    if (bgm.paused) {
        const track = BGM_PLAYLIST[currentBgmIndex];
        if (!bgm.src || !bgm.src.includes(track.src)) {
            bgm.src = track.src;
        }
        bgm.play().then(() => {
            isBgmPlaying = true;
            updateBgmUI();
            showToastAlert(`🎵 [${track.tag}] Đang phát: ${track.shortName}`);
        }).catch(err => {
            console.warn("Autoplay block or error:", err);
            showToastAlert(`🎵 Bấm một nút bất kỳ trên web để cấp quyền phát âm thanh`);
        });
    } else {
        bgm.pause();
        isBgmPlaying = false;
        updateBgmUI();
        showToastAlert(`⏸️ Đã tạm dừng nhạc nền`);
    }
}

function nextBgm(isAuto = false) {
    const bgm = document.getElementById("bgmAudio");
    if (!bgm) return;

    currentBgmIndex = (currentBgmIndex + 1) % BGM_PLAYLIST.length;
    const track = BGM_PLAYLIST[currentBgmIndex];
    bgm.src = track.src;

    if (isBgmPlaying || isAuto) {
        bgm.play().then(() => {
            isBgmPlaying = true;
            updateBgmUI();
            showToastAlert(`⏭️ [${track.tag}] Chuyển bài: ${track.shortName}`);
        }).catch(err => {
            console.warn("BGM playback err:", err);
        });
    } else {
        updateBgmUI();
        showToastAlert(`🎵 Đã chọn bài [${track.tag}]: ${track.shortName}`);
    }
}

function prevBgm() {
    const bgm = document.getElementById("bgmAudio");
    if (!bgm) return;

    currentBgmIndex = (currentBgmIndex - 1 + BGM_PLAYLIST.length) % BGM_PLAYLIST.length;
    const track = BGM_PLAYLIST[currentBgmIndex];
    bgm.src = track.src;

    if (isBgmPlaying) {
        bgm.play().then(() => {
            isBgmPlaying = true;
            updateBgmUI();
            showToastAlert(`⏮️ [${track.tag}] Lùi bài: ${track.shortName}`);
        }).catch(err => {
            console.warn("BGM playback err:", err);
        });
    } else {
        updateBgmUI();
        showToastAlert(`🎵 Đã chọn bài [${track.tag}]: ${track.shortName}`);
    }
}

// Voice Clip Playback (Authentic Character Voice)
function playVoice(lang) {
    if (filteredLines.length === 0) return;
    const line = filteredLines[currentIndex];
    const spk = (line.speaker || "").trim().toLowerCase();
    const charData = charactersDict[spk] || charactersDict[spk.split(" ").pop()];
    if (!charData) return;

    const voices = lang === "jp" ? charData.voices_jp : charData.voices_cn;
    if (!voices || voices.length === 0) return;

    const chosenWav = voices[0];
    const audio = document.getElementById("voiceAudio");
    if (!audio) return;
    audio.src = `official_assets/${chosenWav}`;
    audio.play();
    showToastAlert(`🔊 Đang phát giọng ${charData.nameEN} (${lang.toUpperCase()})...`);
}
