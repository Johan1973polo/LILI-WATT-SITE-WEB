#!/usr/bin/env python3
"""
LILIWATT — Vidéo publicitaire V4
- Nouvelle voix ojsdYNTmnPdf7yAl8rI5
- Logo = logo sans fond.png
- logoanimé.mp4 au début (rapide, vitesse originale) + à la fin
- PAS de logo overlay, PAS de textes
- Musique piano à 12%
"""

import os
import numpy as np
from PIL import Image
from moviepy import (
    VideoClip, VideoFileClip, AudioFileClip,
    CompositeAudioClip, concatenate_videoclips
)
from moviepy.video.fx import CrossFadeIn, CrossFadeOut
from moviepy.audio.fx import MultiplyVolume, AudioLoop

W, H = 1280, 720
FPS = 25

BASE = os.path.expanduser("~/Desktop/liliwatt-website")
VIDEO_DIR = os.path.expanduser("~/Desktop/video liliwatt")
MUSIC_PATH = os.path.join(BASE, "musique_piano_v2.mp3")
VOIX_PATH = os.path.join(BASE, "voix_liliwatt_v4.mp3")
OUTPUT = os.path.expanduser("~/Desktop/pub_liliwatt_finale.mp4")


def fit_video(clip):
    cw, ch = clip.size
    scale = max(W / cw, H / ch)
    nw, nh = int(cw * scale), int(ch * scale)
    resized = clip.resized((nw, nh))
    x1, y1 = (nw - W) // 2, (nh - H) // 2
    return resized.cropped(x1=x1, y1=y1, x2=x1 + W, y2=y1 + H)


def load_vid(name):
    path = os.path.join(VIDEO_DIR, name)
    if os.path.exists(path):
        return fit_video(VideoFileClip(path))
    return None


def main():
    print("=" * 60)
    print("  LILIWATT — Vidéo V4")
    print("  Nouvelle voix · Pas de textes · Logo animé début+fin")
    print("=" * 60)

    # Measure voice duration
    voix = AudioFileClip(VOIX_PATH)
    voice_dur = voix.duration
    voix.close()
    print(f"\n📊 Durée voix off: {voice_dur:.2f}s")

    # === CLIP ORDER ===
    # 1. logoanimé.mp4 — DÉBUT, vitesse originale (rapide, ~6s)
    # 2. energie.mp4
    # 3. agence .mp4
    # 4. repartition.mp4
    # 5. exterieur.mp4
    # 6. liste fournisseurs .mp4
    # 7. personne travaille.mp4
    # 8. logoanimé.mp4 — FIN, vitesse originale (rapide, ~6s)

    clip_names = [
        "logoanimé.mp4",          # 1 - DÉBUT (rapide)
        "energie.mp4",             # 2
        "agence .mp4",             # 3
        "repartition.mp4",         # 4
        "exterieur.mp4",           # 5
        "liste fournisseurs .mp4", # 6
        "personne travaille.mp4",  # 7
        "logoanimé.mp4",          # 8 - FIN (rapide)
    ]

    # Load all clips at original speed
    raw_clips = []
    for name in clip_names:
        c = load_vid(name)
        if c:
            raw_clips.append((name, c))
            print(f"  Chargé: {name} ({c.duration:.2f}s)")
        else:
            print(f"  ⚠️ Non trouvé: {name}")

    # Logo animé clips (first and last) keep original speed
    # Middle clips need to be stretched to fill remaining time
    logo_clip_first = raw_clips[0][1]  # ~6s original speed
    logo_clip_last = raw_clips[-1][1]  # ~6s original speed

    middle_clips_raw = raw_clips[1:-1]  # 6 clips

    crossfade = 0.3
    n_total = len(raw_clips)
    n_crossfades = n_total - 1

    # Fixed durations for logo clips
    logo_first_dur = logo_clip_first.duration  # original speed
    logo_last_dur = logo_clip_last.duration    # original speed

    # Time budget for middle clips
    # total = logo_first + middle_total + logo_last - n_crossfades * crossfade = voice_dur
    # middle_total = voice_dur - logo_first - logo_last + n_crossfades * crossfade
    middle_total = voice_dur - logo_first_dur - logo_last_dur + n_crossfades * crossfade
    n_middle = len(middle_clips_raw)
    middle_clip_dur = middle_total / n_middle

    print(f"\n📊 Logo début: {logo_first_dur:.2f}s (vitesse originale)")
    print(f"📊 Logo fin: {logo_last_dur:.2f}s (vitesse originale)")
    print(f"📊 {n_middle} clips milieu × {middle_clip_dur:.2f}s = {middle_total:.2f}s")
    print(f"📊 {n_crossfades} crossfades × {crossfade}s")
    actual = logo_first_dur + middle_total + logo_last_dur - n_crossfades * crossfade
    print(f"📊 Durée finale: {actual:.2f}s (voix: {voice_dur:.2f}s)")

    # === BUILD CLIPS ===
    final_clips = []

    # 1. Logo animé DÉBUT — vitesse originale, pas de texte, pas d'overlay
    print(f"\n[1/{n_total}] logoanimé.mp4 (début, rapide)")
    c = logo_clip_first
    c = c.with_effects([CrossFadeIn(0.3), CrossFadeOut(crossfade)])
    final_clips.append(c)

    # 2-7. Middle clips — stretched to fill time
    for i, (name, raw) in enumerate(middle_clips_raw):
        idx = i + 2
        target_dur = middle_clip_dur
        print(f"[{idx}/{n_total}] {name} → {target_dur:.2f}s")

        # Stretch by slowing down
        speed_factor = raw.duration / target_dur

        def make_frame_factory(clip, spd, tgt):
            def frame(t):
                src_t = min(t * spd, clip.duration - 0.04)
                try:
                    return clip.get_frame(src_t)
                except:
                    return np.zeros((H, W, 3), dtype=np.uint8)
            return frame

        stretched = VideoClip(
            make_frame_factory(raw, speed_factor, target_dur),
            duration=target_dur
        )

        if idx < n_total:
            stretched = stretched.with_effects([CrossFadeOut(crossfade)])
        final_clips.append(stretched)

    # 8. Logo animé FIN — vitesse originale
    print(f"[{n_total}/{n_total}] logoanimé.mp4 (fin, rapide)")
    c_last = load_vid("logoanimé.mp4")  # Reload fresh
    # No crossfade out, just fade to black at end
    final_clips.append(c_last)

    # === CONCATENATE ===
    print("\n🔗 Assemblage...")
    video = concatenate_videoclips(final_clips, method="compose", padding=-crossfade)
    print(f"   Durée assemblée: {video.duration:.2f}s")

    # === AUDIO ===
    print("\n🔊 Audio...")
    audio_tracks = []

    if os.path.exists(MUSIC_PATH):
        music = AudioFileClip(MUSIC_PATH)
        if music.duration < video.duration:
            music = music.with_effects([AudioLoop(duration=video.duration)])
        else:
            music = music.subclipped(0, video.duration)
        music = music.with_effects([MultiplyVolume(0.12)])
        audio_tracks.append(music)
        print(f"   ✅ Musique: {music.duration:.1f}s (12%)")

    voix = AudioFileClip(VOIX_PATH)
    if voix.duration > video.duration:
        voix = voix.subclipped(0, video.duration)
    audio_tracks.append(voix)
    print(f"   ✅ Voix: {voix.duration:.2f}s")

    audio_final = CompositeAudioClip(audio_tracks)
    video = video.with_audio(audio_final)

    # === EXPORT ===
    print(f"\n🎬 Export → {OUTPUT}")
    video.write_videofile(
        OUTPUT, fps=FPS, codec='libx264',
        audio_codec='aac', bitrate='8000k',
        preset='medium', threads=4, logger='bar'
    )

    sz = os.path.getsize(OUTPUT)
    print(f"\n{'=' * 60}")
    print(f"  ✅ VIDÉO EXPORTÉE !")
    print(f"  📁 {OUTPUT}")
    print(f"  ⏱️  {video.duration:.2f}s | 💾 {sz/(1024*1024):.1f} MB")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
