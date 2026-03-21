#!/usr/bin/env python3
"""
LILIWATT — Vidéo publicitaire finale
Vrais clips vidéo + textes blancs contour violet en bas + voix off + musique piano
Synchronisation parfaite voix/vidéo
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    VideoClip, VideoFileClip, ImageClip, AudioFileClip,
    CompositeAudioClip, CompositeVideoClip, concatenate_videoclips
)
from moviepy.video.fx import CrossFadeIn, CrossFadeOut
from moviepy.audio.fx import MultiplyVolume, AudioLoop

# === CONFIG ===
W, H = 1280, 720
FPS = 25

FOND = (10, 6, 24)       # #0A0618
VIOLET = (124, 58, 237)   # #7C3AED
FUCHSIA = (217, 70, 239)  # #D946EF
LAVANDE = (167, 139, 250) # #A78BFA
BLANC = (255, 255, 255)   # #FFFFFF

BASE = os.path.expanduser("~/Desktop/liliwatt-website")
VIDEO_DIR = os.path.expanduser("~/Desktop/video liliwatt")
LOGO_PATH = os.path.join(BASE, "assets/images/logo-liliwatt.png")
MUSIC_PATH = os.path.join(BASE, "musique_piano_v2.mp3")
VOIX_PATH = os.path.join(BASE, "voix_liliwatt_v3.mp3")
OUTPUT = os.path.expanduser("~/Desktop/pub_liliwatt_finale.mp4")


# === FONTS ===
def get_font(size, bold=False):
    paths = [
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for fp in paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except:
                continue
    return ImageFont.load_default()

def get_bold(sz):
    return get_font(sz, bold=True)


# === HELPERS ===
def ease_out(t):
    t = min(1.0, max(0.0, t))
    return 1 - (1 - t) ** 3

def add_glow(img, x, y, radius, color, intensity=0.5):
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for r in range(radius, 0, -4):
        a = int(intensity * 255 * (1 - r / radius) ** 2)
        d.ellipse([x-r, y-r, x+r, y+r], fill=(*color, min(255, a)))
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    return Image.alpha_composite(img, ov)

def fit_video(clip):
    """Resize + center crop to fill 1280x720"""
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

def load_logo():
    for p in [LOGO_PATH, os.path.join(VIDEO_DIR, "logo.png")]:
        if os.path.exists(p):
            return Image.open(p).convert('RGBA')
    return None

def text_center_x(draw, text, font, w=W):
    bbox = draw.textbbox((0, 0), text, font=font)
    return (w - (bbox[2] - bbox[0])) // 2

def draw_text_bottom(img, text, font, y_from_bottom=100, color=BLANC,
                     stroke_color=VIOLET, stroke_width=3, bg_opacity=100):
    """Draw text at the bottom with semi-transparent background bar + violet stroke"""
    img_rgba = img if img.mode == 'RGBA' else img.convert('RGBA')
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (W - tw) // 2
    ty = H - y_from_bottom

    # Semi-transparent black background bar
    pad_x, pad_y = 30, 12
    d.rounded_rectangle(
        [tx - pad_x, ty - pad_y, tx + tw + pad_x, ty + th + pad_y],
        radius=8,
        fill=(0, 0, 0, bg_opacity)
    )

    # Text with violet stroke
    if stroke_width > 0:
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx*dx + dy*dy <= stroke_width*stroke_width:
                    d.text((tx + dx, ty + dy), text, fill=(*stroke_color, 255), font=font)

    # White text on top
    d.text((tx, ty), text, fill=(*color, 255), font=font)

    return Image.alpha_composite(img_rgba, ov)

def draw_text_bottom_animated(img, text, font, t, start_t, dur=2.5,
                               y_from_bottom=100, color=BLANC,
                               stroke_color=VIOLET, stroke_width=3):
    """Animated text: fade in from bottom with timing"""
    if t < start_t or t > start_t + dur:
        return img

    progress = ease_out(min(1.0, (t - start_t) / 0.6))
    # Fade out at end
    fade_out = 1.0
    if t > start_t + dur - 0.4:
        fade_out = max(0, 1.0 - (t - (start_t + dur - 0.4)) / 0.4)

    alpha = progress * fade_out
    if alpha < 0.05:
        return img

    y_offset = int(20 * (1 - progress))
    actual_y = y_from_bottom - y_offset

    img_rgba = img if img.mode == 'RGBA' else img.convert('RGBA')
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (W - tw) // 2
    ty = H - actual_y

    # Semi-transparent background
    pad_x, pad_y = 30, 12
    d.rounded_rectangle(
        [tx - pad_x, ty - pad_y, tx + tw + pad_x, ty + th + pad_y],
        radius=8,
        fill=(0, 0, 0, int(100 * alpha))
    )

    # Stroke
    al = int(255 * alpha)
    if stroke_width > 0:
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx*dx + dy*dy <= stroke_width*stroke_width:
                    d.text((tx+dx, ty+dy), text, fill=(*stroke_color, al), font=font)

    d.text((tx, ty), text, fill=(*color, al), font=font)
    return Image.alpha_composite(img_rgba, ov)


# ======================================================================
#  Define clip order and timing
# ======================================================================
# Voice = 44.67s
# 6 clips × 6.04s = 36.24s raw
# With 5 crossfades of 0.3s = 36.24 - 1.5 = 34.74s
# Need to stretch clips to match voice duration
# Each clip needs to be ~44.67/6 ≈ 7.45s → speed factor ~0.81

VOICE_DURATION = 44.67  # Will be measured precisely

# Clip order as specified:
# 1. logoanimé.mp4 (OUVERTURE)
# 2. energie.mp4 (LE PROBLÈME)
# 3. agence .mp4 (QUI SOMMES-NOUS / LILIWATT)
# 4. repartition.mp4 (FOURNISSEURS DU MARCHÉ)
# 5. exterieur.mp4 (CLIENTS)
# 6. liste fournisseurs .mp4 (FINAL / + logo overlay)

CLIP_ORDER = [
    "logoanimé.mp4",
    "energie.mp4",
    "agence .mp4",
    "repartition.mp4",
    "exterieur.mp4",
    "liste fournisseurs .mp4",
]

# Text overlays per sequence (texts at bottom)
TEXTS = [
    # Seq 1 - Logo
    [
        (0.5, 5.5, "LILIWATT — Courtage Énergie", 42),
    ],
    # Seq 2 - Problème
    [
        (0.5, 4.0, "60% des professionnels surpaient leur énergie", 38),
        (4.5, 7.5, "Jusqu'à 18% de trop chaque année", 42),
    ],
    # Seq 3 - LILIWATT
    [
        (0.5, 6.5, "Nous analysons · Nous comparons · Nous négocions", 36),
    ],
    # Seq 4 - Répartition / fournisseurs
    [
        (0.5, 4.0, "Accès à tous les fournisseurs du marché", 38),
        (4.5, 7.5, "Le meilleur tarif, garanti", 42),
    ],
    # Seq 5 - Clients
    [
        (0.5, 3.5, "Restaurants · Boulangeries · Hôtels · Laveries", 36),
        (4.0, 7.5, "1 460€ économisés en moyenne par an", 42),
    ],
    # Seq 6 - Final
    [
        (0.3, 3.0, "Sans frais · Sans coupure · Sans démarche", 38),
        (3.5, 5.5, "LILIWATT", 72),
        (5.5, 8.0, "liliwatt.fr — Analyse gratuite", 42),
    ],
]


def make_clip_with_text(clip_name, texts_def, target_duration, seq_index):
    """Load a video clip, slow it to target_duration, add text overlays"""

    raw_clip = load_vid(clip_name)
    if raw_clip is None:
        print(f"    ⚠️  Clip {clip_name} non trouvé, fond noir")
        raw_clip_dur = target_duration
    else:
        raw_clip_dur = raw_clip.duration

    logo = load_logo() if seq_index in [0, 5] else None

    def frame(t):
        # Map t to source clip time (stretch)
        if raw_clip:
            src_t = t * (raw_clip.duration / target_duration)
            src_t = min(src_t, raw_clip.duration - 0.04)
            try:
                img = Image.fromarray(raw_clip.get_frame(src_t))
            except:
                img = Image.new('RGB', (W, H), FOND)
        else:
            img = Image.new('RGB', (W, H), FOND)

        img = img.convert('RGBA')

        # Scene-specific overlays
        if seq_index == 0:
            # LOGO intro: darken + logo + glow
            dark = Image.new('RGBA', (W, H), (10, 6, 24, 80))
            img = Image.alpha_composite(img, dark)

            if logo:
                la = ease_out(min(1.0, t / 1.5))
                lw = int(250 * (0.9 + 0.1 * ease_out(min(1.0, t/2))))
                lh = int(logo.height * lw / logo.width)
                lr = logo.resize((lw, lh), Image.LANCZOS)
                if lr.mode == 'RGBA':
                    r, g, b, a = lr.split()
                    a = a.point(lambda x: int(x * la))
                    lr = Image.merge('RGBA', (r, g, b, a))
                lx = (W - lw) // 2
                ly = 80
                img = add_glow(img, W//2, ly + lh//2, int(150*la), VIOLET, 0.3*la)
                img.paste(lr, (lx, ly), lr)

        elif seq_index == 5:
            # CTA Final: darken more + logo + glow
            dark = Image.new('RGBA', (W, H), (10, 6, 24, 140))
            img = Image.alpha_composite(img, dark)

            gp = ease_out(min(1.0, t / 1.5))
            img = add_glow(img, W//2, H//2-80, int(350*gp), VIOLET, 0.15*gp)
            img = add_glow(img, W//2, H//2-80, int(200*gp), FUCHSIA, 0.1*gp)

            if logo:
                la = ease_out(min(1.0, t / 1.2))
                lw = int(300 * (0.85 + 0.15*ease_out(min(1.0, t/1.8))))
                lh = int(logo.height * lw / logo.width)
                lr = logo.resize((lw, lh), Image.LANCZOS)
                if lr.mode == 'RGBA':
                    r, g, b, a = lr.split()
                    a = a.point(lambda x: int(x * la))
                    lr = Image.merge('RGBA', (r, g, b, a))
                lx, ly = (W-lw)//2, 50
                img = add_glow(img, W//2, ly+lh//2, int(200*la), VIOLET, 0.4*la)
                img.paste(lr, (lx, ly), lr)
        else:
            # Other scenes: slight darken for text readability
            dark = Image.new('RGBA', (W, H), (6, 6, 15, 60))
            img = Image.alpha_composite(img, dark)

        # Text overlays at bottom
        for (t_start, t_end, text, fontsize) in texts_def:
            dur = t_end - t_start
            f = get_bold(fontsize)
            # Choose y position based on whether it's the main or sub text
            y_pos = 100
            if fontsize >= 60:
                y_pos = 200  # Big text higher
            elif fontsize <= 36:
                y_pos = 80

            img = draw_text_bottom_animated(
                img, text, f, t, t_start, dur=dur,
                y_from_bottom=y_pos, stroke_width=2
            )

        # Fade out on last scene
        if seq_index == 5 and t > target_duration - 1.0:
            fade = max(0, 1.0 - (t - (target_duration - 1.0)) / 1.0)
            arr = np.array(img.convert('RGB')).astype(float) * fade
            return arr.astype(np.uint8)

        return np.array(img.convert('RGB'))

    return VideoClip(frame, duration=target_duration)


# ======================================================================
#  MAIN
# ======================================================================
def main():
    print("=" * 60)
    print("  LILIWATT — Vidéo publicitaire FINALE V3")
    print("  Voix + Musique + Clips réels + Textes synchro")
    print("=" * 60)

    # Measure actual voice duration
    voix = AudioFileClip(VOIX_PATH)
    voice_dur = voix.duration
    voix.close()
    print(f"\n📊 Durée voix off: {voice_dur:.2f}s")

    # Calculate crossfade
    crossfade = 0.3
    n_clips = len(CLIP_ORDER)
    n_crossfades = n_clips - 1
    # total_dur = n_clips * clip_dur - n_crossfades * crossfade = voice_dur
    # clip_dur = (voice_dur + n_crossfades * crossfade) / n_clips
    target_clip_dur = (voice_dur + n_crossfades * crossfade) / n_clips
    actual_total = n_clips * target_clip_dur - n_crossfades * crossfade

    print(f"📊 Clips: {n_clips} × {target_clip_dur:.2f}s")
    print(f"📊 Crossfades: {n_crossfades} × {crossfade}s")
    print(f"📊 Durée finale vidéo: {actual_total:.2f}s (= voix {voice_dur:.2f}s)")

    # Build clips
    clips = []
    for i, clip_name in enumerate(CLIP_ORDER):
        print(f"\n[{i+1}/{n_clips}] {clip_name} → {target_clip_dur:.2f}s")
        c = make_clip_with_text(clip_name, TEXTS[i], target_clip_dur, i)

        if i == 0:
            c = c.with_effects([CrossFadeIn(0.3)])
        if i < n_clips - 1:
            c = c.with_effects([CrossFadeOut(crossfade)])
        clips.append(c)

    # Concatenate
    print("\n🔗 Assemblage avec fondus...")
    video = concatenate_videoclips(clips, method="compose", padding=-crossfade)
    print(f"   Durée assemblée: {video.duration:.2f}s")

    # === AUDIO ===
    print("\n🔊 Préparation audio...")
    audio_tracks = []

    # Music
    if os.path.exists(MUSIC_PATH):
        music = AudioFileClip(MUSIC_PATH)
        if music.duration < video.duration:
            music = music.with_effects([AudioLoop(duration=video.duration)])
        else:
            music = music.subclipped(0, video.duration)
        music = music.with_effects([MultiplyVolume(0.12)])
        audio_tracks.append(music)
        print(f"   ✅ Musique: {music.duration:.1f}s (vol 12%)")

    # Voice
    voix = AudioFileClip(VOIX_PATH)
    if voix.duration > video.duration:
        voix = voix.subclipped(0, video.duration)
    audio_tracks.append(voix)
    print(f"   ✅ Voix off: {voix.duration:.2f}s")

    audio_final = CompositeAudioClip(audio_tracks)
    video = video.with_audio(audio_final)

    # === EXPORT ===
    print(f"\n🎬 Export → {OUTPUT}")
    print(f"   {W}x{H} | {FPS}fps | bitrate=8000k")

    video.write_videofile(
        OUTPUT, fps=FPS, codec='libx264',
        audio_codec='aac', bitrate='8000k',
        preset='medium', threads=4, logger='bar'
    )

    sz = os.path.getsize(OUTPUT)
    print(f"\n{'=' * 60}")
    print(f"  ✅ VIDÉO FINALE EXPORTÉE !")
    print(f"  📁 {OUTPUT}")
    print(f"  📐 {W}x{H} | {FPS} fps")
    print(f"  ⏱️  {video.duration:.2f} secondes")
    print(f"  💾 {sz/(1024*1024):.1f} MB")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
