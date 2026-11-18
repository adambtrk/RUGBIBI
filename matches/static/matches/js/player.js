const video = document.getElementById('match-video');
const controls = document.getElementById('player-controls');
const status = document.getElementById('seek-status');

function seekTo(seconds) {
    if (!Number.isFinite(video.duration)) {
        status.textContent = 'Attendez le chargement de la vidéo.';
        return;
    }
    video.currentTime = Math.max(0, Math.min(seconds, video.duration));
    status.textContent = '';
}

controls.hidden = false;
document.getElementById('backward').addEventListener('click', () => seekTo(video.currentTime - 10));
document.getElementById('forward').addEventListener('click', () => seekTo(video.currentTime + 10));
document.getElementById('playback-speed').addEventListener('change', event => {
    video.playbackRate = Number(event.target.value);
});
document.getElementById('seek-form').addEventListener('submit', event => {
    event.preventDefault();
    const parts = document.getElementById('seek-time').value.split(':').map(Number);
    seekTo(parts[0] * 60 + parts[1]);
});
video.addEventListener('error', () => {
    document.getElementById('video-error').hidden = false;
}, true);
