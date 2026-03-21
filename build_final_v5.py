#!/usr/bin/env python3
"""
LILIWATT — Vidéo publicitaire V5
- Voix ojsdYNTmnPdf7yAl8rI5
- Pas de textes sauf "liliwatt.fr" à la fin
- Logo animé début + fin
- Fin prolongée: image figée + liliwatt.fr + musique continue
- agence .mp4 : crop haut + logo overlay en grand
- Nouvelle musique piano+cordes
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    VideoClip, VideoFileClip, AudioFileClip,
    CompositeAudioClip, concatenate_videoclips
)
from moviepy.video.fx import CrossFadeIn, CrossFadeOut
from moviepy.audio.fx import MultiplyVolume, AudioLoop, AudioFadeOut

W, H = 1280, 720
FPS = 25
END_FREEZE_DURATION = 8.0  # 8 seconds: logo + liliwatt.fr + contact info

FOND = (10, 6, 24)
VIOLET = (124, 58, 237)
FUCHSIA = (217, 70, 239)
LAVANDE = (167, 139, 250)
BLANC = (255, 255, 255)

BASE = os.path.expanduser("~/Desktop/liliwatt-website")
VIDEO_DIR = os.path.expanduser("~/Desktop/video liliwatt")
LOGO_PATH = os.path.join(VIDEO_DIR, "logo sans fond.png")
MUSIC_PATH = os.path.join(BASE, "musique_douce.mp3")
VOIX_PATH = os.path.join(BASE, "voix_liliwatt_femme.mp3")
OUTPUT = os.path.expanduser("~/Desktop/pub_liliwatt_finale.mp4")


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


def fit_video(clip, align_top=False):
    """Resize + crop to fill 1280x720. align_top=True crops from top instead of center."""
    cw, ch = clip.size
    scale = max(W / cw, H / ch)
    nw, nh = int(cw * scale), int(ch * scale)
    resized = clip.resized((nw, nh))
    x1 = (nw - W) // 2
    if align_top:
        y1 = 0  # Keep top of the video
    else:
        y1 = (nh - H) // 2
    return resized.cropped(x1=x1, y1=y1, x2=x1 + W, y2=y1 + H)


def load_vid(name, align_top=False):
    path = os.path.join(VIDEO_DIR, name)
    if os.path.exists(path):
        return fit_video(VideoFileClip(path), align_top=align_top)
    return None


def load_logo():
    if os.path.exists(LOGO_PATH):
        return Image.open(LOGO_PATH).convert('RGBA')
    return None


def make_agence_clip(target_dur):
    """Agence clip: crop from TOP + logo overlay in the center"""
    raw = load_vid("agence .mp4", align_top=True)
    logo = load_logo()

    if not raw:
        return VideoClip(lambda t: np.zeros((H, W, 3), dtype=np.uint8), duration=target_dur)

    speed = raw.duration / target_dur

    def frame(t):
        src_t = min(t * speed, raw.duration - 0.04)
        try:
            img = Image.fromarray(raw.get_frame(src_t))
        except:
            img = Image.new('RGB', (W, H), FOND)

        img = img.convert('RGBA')

        # Overlay logo in the center, big and visible
        if logo:
            la = ease_out(min(1.0, t / 1.5))
            lw = 400  # Big logo
            lh = int(logo.height * lw / logo.width)
            lr = logo.resize((lw, lh), Image.LANCZOS)

            if lr.mode == 'RGBA':
                r, g, b, a = lr.split()
                a = a.point(lambda x: int(x * la))
                lr = Image.merge('RGBA', (r, g, b, a))

            lx = (W - lw) // 2
            ly = (H - lh) // 2

            # Subtle glow behind logo
            img = add_glow(img, W // 2, ly + lh // 2, int(200 * la), VIOLET, 0.2 * la)
            img.paste(lr, (lx, ly), lr)

        return np.array(img.convert('RGB'))

    return VideoClip(frame, duration=target_dur)


def make_end_freeze(last_frame_arr):
    """Frozen last frame → logo + liliwatt.fr + contact info"""
    logo = load_logo()

    contact_lines = [
        ("contact@liliwatt.fr", 20),
        ("Tél : +33 (0)1 84 16 08 56", 20),
        ("59 rue de Ponthieu, Bureau 326", 18),
        ("75008 Paris", 18),
        ("Lun-Ven : 9h-18h", 18),
    ]

    def frame(t):
        # Start from frozen frame, progressively darken to near-black
        img = Image.fromarray(last_frame_arr).convert('RGBA')
        dark_a = int(min(220, 60 + t * 40))
        dark = Image.new('RGBA', (W, H), (10, 6, 24, dark_a))
        img = Image.alpha_composite(img, dark)

        # Glow
        gp = ease_out(min(1.0, t / 2.0))
        img = add_glow(img, W // 2, 200, int(350 * gp), VIOLET, 0.12 * gp)
        img = add_glow(img, W // 2, 200, int(200 * gp), FUCHSIA, 0.08 * gp)

        # Logo (top area)
        if logo and t > 0.3:
            la = ease_out(min(1.0, (t - 0.3) / 1.0))
            lw = 260
            lh = int(logo.height * lw / logo.width)
            lr = logo.resize((lw, lh), Image.LANCZOS)
            if lr.mode == 'RGBA':
                r, g, b, a = lr.split()
                a = a.point(lambda x: int(x * la))
                lr = Image.merge('RGBA', (r, g, b, a))
            lx, ly = (W - lw) // 2, 60
            img = add_glow(img, W // 2, ly + lh // 2, int(150 * la), VIOLET, 0.3 * la)
            img.paste(lr, (lx, ly), lr)

        # "liliwatt.fr" — big, centered
        if t > 1.0:
            ta = ease_out(min(1.0, (t - 1.0) / 0.7))
            yo = int(12 * (1 - ta))
            font_url = get_bold(50)
            txt = "liliwatt.fr"
            ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            bbox = d.textbbox((0, 0), txt, font=font_url)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2
            img = add_glow(img, W // 2, 295 + yo, int(100 * ta), FUCHSIA, 0.25 * ta)
            d.text((tx + 2, 275 + yo), txt, fill=(0, 0, 0, int(160 * ta)), font=font_url)
            d.text((tx, 273 + yo), txt, fill=(*FUCHSIA, int(255 * ta)), font=font_url)
            img = Image.alpha_composite(img, ov)

        # Separator line
        if t > 2.0:
            la = ease_out(min(1.0, (t - 2.0) / 0.5))
            ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            line_w = int(300 * la)
            lx = (W - line_w) // 2
            d.line([(lx, 340), (lx + line_w, 340)], fill=(*VIOLET, int(180 * la)), width=2)
            img = Image.alpha_composite(img, ov)

        # Contact info — appears line by line
        if t > 2.5:
            ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            y_start = 370
            for i, (line, fsize) in enumerate(contact_lines):
                line_start = 2.5 + i * 0.35
                if t > line_start:
                    la = ease_out(min(1.0, (t - line_start) / 0.5))
                    yo = int(10 * (1 - la))
                    f = get_font(fsize)
                    bbox = d.textbbox((0, 0), line, font=f)
                    tw = bbox[2] - bbox[0]
                    tx = (W - tw) // 2
                    ty = y_start + i * 38 + yo

                    # First line (email) slightly brighter
                    if i == 0:
                        color = (*BLANC, int(255 * la))
                    elif i == 1:
                        color = (*BLANC, int(240 * la))
                    else:
                        color = (*LAVANDE, int(220 * la))

                    d.text((tx, ty), line, fill=color, font=f)
            img = Image.alpha_composite(img, ov)

        # "Analyse gratuite · Sans engagement" — pill at bottom
        if t > 4.5:
            sa = ease_out(min(1.0, (t - 4.5) / 0.6))
            font_sub = get_font(20)
            sub = "Analyse gratuite · Sans engagement"
            ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            bbox = d.textbbox((0, 0), sub, font=font_sub)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2
            d.rounded_rectangle(
                [tx - 20, 580, tx + tw + 20, 612],
                radius=16,
                fill=(124, 58, 237, int(110 * sa))
            )
            d.text((tx, 585), sub, fill=(*BLANC, int(255 * sa)), font=font_sub)
            img = Image.alpha_composite(img, ov)

        return np.array(img.convert('RGB'))

    return VideoClip(frame, duration=END_FREEZE_DURATION)


def make_stretched_clip(name, target_dur):
    """Load a clip and stretch it to target duration"""
    raw = load_vid(name)
    if not raw:
        return VideoClip(lambda t: np.zeros((H, W, 3), dtype=np.uint8), duration=target_dur)

    speed = raw.duration / target_dur

    def frame(t):
        src_t = min(t * speed, raw.duration - 0.04)
        try:
            return raw.get_frame(src_t)
        except:
            return np.zeros((H, W, 3), dtype=np.uint8)

    return VideoClip(frame, duration=target_dur)


def main():
    print("=" * 60)
    print("  LILIWATT — Vidéo V5")
    print("  Fin prolongée + Logo agence + Nouvelle musique")
    print("=" * 60)

    voix = AudioFileClip(VOIX_PATH)
    voice_dur = voix.duration
    voix.close()
    print(f"\n📊 Voix off: {voice_dur:.2f}s")
    print(f"📊 Freeze fin: +{END_FREEZE_DURATION}s")
    total_target = voice_dur + END_FREEZE_DURATION
    print(f"📊 Durée totale cible: {total_target:.2f}s")

    # Clip order:
    # 1. logoanimé.mp4 (début, rapide ~6s)
    # 2. energie.mp4 (stretched)
    # 3. agence .mp4 (stretched, crop TOP, logo overlay)
    # 4. repartition.mp4 (stretched)
    # 5. exterieur.mp4 (stretched)
    # 6. liste fournisseurs .mp4 (stretched)
    # 7. logoanimé.mp4 (fin, rapide ~6s)
    # 8. FREEZE + liliwatt.fr (5s)

    # Logo animé clips at original speed
    logo_first = load_vid("logoanimé.mp4")
    logo_last = load_vid("logoanimé.mp4")

    crossfade = 0.3
    # 7 video clips + 1 freeze = 8 segments, 7 crossfades
    n_crossfades = 7

    # Time budget for 5 middle clips
    logo_dur = logo_first.duration  # ~6.04s
    time_for_middle = voice_dur - logo_dur - logo_dur + (n_crossfades - 1) * crossfade
    # Actually let me recalculate properly:
    # total = logo + mid1 + mid2 + mid3 + mid4 + mid5 + logo + freeze - 7*crossfade
    # voice_dur + freeze = logo + 5*mid + logo + freeze - 7*crossfade
    # voice_dur = 2*logo + 5*mid - 7*crossfade
    # 5*mid = voice_dur - 2*logo + 7*crossfade
    n_middle = 5
    mid_dur = (voice_dur - 2 * logo_dur + n_crossfades * crossfade) / n_middle
    actual_main = 2 * logo_dur + n_middle * mid_dur - (n_crossfades - 1) * crossfade
    # Wait, let me count segments properly:
    # Segments: logo, mid1, mid2, mid3, mid4, mid5, logo, freeze = 8
    # Crossfades between them: 7
    # Total = sum(durations) - 7 * crossfade
    # We want: total = voice_dur + freeze_dur
    # sum(durations) = total + 7*crossfade = voice_dur + freeze_dur + 7*0.3
    # sum = 2*logo_dur + 5*mid_dur + freeze_dur
    # So: 2*logo_dur + 5*mid_dur + freeze_dur = voice_dur + freeze_dur + 7*0.3
    # 2*logo_dur + 5*mid_dur = voice_dur + 2.1
    # 5*mid_dur = voice_dur + 2.1 - 2*logo_dur
    mid_dur = (voice_dur + 7 * crossfade - 2 * logo_dur) / n_middle

    total_check = 2 * logo_dur + n_middle * mid_dur + END_FREEZE_DURATION - 7 * crossfade
    print(f"\n📊 Logo début/fin: {logo_dur:.2f}s chacun")
    print(f"📊 5 clips milieu: {mid_dur:.2f}s chacun")
    print(f"📊 Freeze fin: {END_FREEZE_DURATION:.1f}s")
    print(f"📊 Total calculé: {total_check:.2f}s (cible: {total_target:.2f}s)")

    # Build clips
    clips = []

    # 1. Logo animé DÉBUT
    print(f"\n[1/8] logoanimé.mp4 (début, rapide {logo_dur:.1f}s)")
    c = logo_first.with_effects([CrossFadeIn(0.3), CrossFadeOut(crossfade)])
    clips.append(c)

    # 2. energie.mp4
    print(f"[2/8] energie.mp4 → {mid_dur:.2f}s")
    c = make_stretched_clip("energie.mp4", mid_dur)
    c = c.with_effects([CrossFadeOut(crossfade)])
    clips.append(c)

    # 3. agence .mp4 — CROP TOP + LOGO BIG
    print(f"[3/8] agence .mp4 → {mid_dur:.2f}s (crop haut + logo)")
    c = make_agence_clip(mid_dur)
    c = c.with_effects([CrossFadeOut(crossfade)])
    clips.append(c)

    # 4. repartition.mp4
    print(f"[4/8] repartition.mp4 → {mid_dur:.2f}s")
    c = make_stretched_clip("repartition.mp4", mid_dur)
    c = c.with_effects([CrossFadeOut(crossfade)])
    clips.append(c)

    # 5. exterieur.mp4
    print(f"[5/8] exterieur.mp4 → {mid_dur:.2f}s")
    c = make_stretched_clip("exterieur.mp4", mid_dur)
    c = c.with_effects([CrossFadeOut(crossfade)])
    clips.append(c)

    # 6. liste fournisseurs .mp4
    print(f"[6/8] liste fournisseurs .mp4 → {mid_dur:.2f}s")
    c = make_stretched_clip("liste fournisseurs .mp4", mid_dur)
    c = c.with_effects([CrossFadeOut(crossfade)])
    clips.append(c)

    # 7. Logo animé FIN
    print(f"[7/8] logoanimé.mp4 (fin, rapide {logo_dur:.1f}s)")
    c = logo_last.with_effects([CrossFadeOut(crossfade)])
    clips.append(c)

    # Get last frame from logo animé for freeze
    last_frame = logo_last.get_frame(logo_last.duration - 0.1)

    # 8. FREEZE + liliwatt.fr
    print(f"[8/8] Image figée + liliwatt.fr ({END_FREEZE_DURATION}s)")
    freeze_clip = make_end_freeze(last_frame)
    clips.append(freeze_clip)

    # Concatenate
    print("\n🔗 Assemblage...")
    video = concatenate_videoclips(clips, method="compose", padding=-crossfade)
    print(f"   Durée: {video.duration:.2f}s")

    # Audio
    print("\n🔊 Audio...")
    audio_tracks = []

    if os.path.exists(MUSIC_PATH):
        music = AudioFileClip(MUSIC_PATH)
        if music.duration < video.duration:
            music = music.with_effects([AudioLoop(duration=video.duration)])
        else:
            music = music.subclipped(0, video.duration)
        # Volume 15% + fade out 4 seconds at the very end → stops exactly with video
        fade_out_dur = 4.0
        music = music.with_effects([
            MultiplyVolume(0.15),
            AudioFadeOut(fade_out_dur)
        ])
        audio_tracks.append(music)
        print(f"   ✅ Musique douce: {music.duration:.1f}s (15%, fade out {fade_out_dur}s)")

    voix = AudioFileClip(VOIX_PATH)
    audio_tracks.append(voix)
    print(f"   ✅ Voix: {voix.duration:.2f}s")
    print(f"   → Musique fade out pile à {video.duration:.1f}s")

    audio_final = CompositeAudioClip(audio_tracks)
    video = video.with_audio(audio_final)

    # Export
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
