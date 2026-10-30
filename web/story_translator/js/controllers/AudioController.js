/**
 * AudioController.js
 * Quản lý khởi tạo âm thanh, bật/tắt nhạc nền BGM và phát voice clip nhân vật
 */

function initAudio() {
    const bgm = document.getElementById("bgmAudio");
    if (bgm) bgm.volume = 0.3;
}

function toggleBgm() {
    const bgm = document.getElementById("bgmAudio");
    const btn = document.getElementById("bgmToggleBtn");
    if (!bgm || !btn) return;
    if (bgm.paused) {
        bgm.play();
        btn.classList.add("active");
        btn.innerText = "🔊";
    } else {
        bgm.pause();
        btn.classList.remove("active");
        btn.innerText = "🎵";
    }
}

// Voice Clip Playback (Authentic Character Voice)
function playVoice(lang) {
    if (filteredLines.length === 0) return;
    const line = filteredLines[currentIndex];
    const spk = line.speaker.trim().toLowerCase();
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
