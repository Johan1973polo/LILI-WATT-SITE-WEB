#!/usr/bin/env python3
"""
LILIWATT — Vidéo publicitaire 60 secondes
Vrais clips vidéo + textes animés + musique piano + voix off ElevenLabs
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    VideoClip, VideoFileClip, AudioFileClip,
    CompositeAudioClip, concatenate_videoclips
)
from moviepy.video.fx import CrossFadeIn, CrossFadeOut
from moviepy.audio.fx import MultiplyVolume, AudioLoop

# === CONFIG ===
W, H = 1280, 720
FPS = 25

FOND = (10, 6, 24)
VIOLET = (124, 58, 237)
FUCHSIA = (217, 70, 239)
LAVANDE = (167, 139, 250)
BLANC = (240, 238, 255)
VERT = (34, 197, 94)
ROUGE = (239, 68, 68)

BASE = os.path.expanduser("~/Desktop/liliwatt-website")
VIDEO_DIR = os.path.expanduser("~/Desktop/video liliwatt")
LOGO_PATH = os.path.join(BASE, "assets/images/logo-liliwatt.png")
MUSIC_PATH = os.path.join(BASE, "musique_piano.mp3")
VOIX_PATH = os.path.join(BASE, "voix_liliwatt.mp3")
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

def get_bold_font(size):
    return get_font(size, bold=True)

def ease_out(t):
    t = min(1.0, max(0.0, t))
    return 1 - (1 - t) ** 3

def add_glow(img, x, y, radius, color, intensity=0.5):
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for r in range(radius, 0, -4):
        alpha = int(intensity * 255 * (1 - r / radius) ** 2)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(*color, min(255, alpha)))
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    return Image.alpha_composite(img, overlay)

def load_logo():
    for p in [LOGO_PATH, os.path.join(VIDEO_DIR, "logo.png")]:
        if os.path.exists(p):
            return Image.open(p).convert('RGBA')
    return None

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

def text_center(draw, text, font, w=W):
    bbox = draw.textbbox((0, 0), text, font=font)
    return (w - (bbox[2] - bbox[0])) // 2


# ======================================================================
#  SCENE 1: INTRO + LOGO (0-8s)
# ======================================================================
def make_scene1():
    dur = 8.0
    logo = load_logo()
    logo_vid = load_vid("logoanimé.mp4")

    def frame(t):
        if logo_vid and t < logo_vid.duration:
            try:
                img = Image.fromarray(logo_vid.get_frame(t))
                dark = Image.new('RGBA', (W, H), (10, 6, 24, 100))
                img = Image.alpha_composite(img.convert('RGBA'), dark).convert('RGB')
            except:
                img = Image.new('RGB', (W, H), FOND)
        else:
            img = Image.new('RGB', (W, H), FOND)

        img = img.convert('RGBA')
        gp = ease_out(min(1.0, t / 2.5))
        img = add_glow(img, W//2, H//2-30, int(400*gp), VIOLET, 0.12*gp)
        img = add_glow(img, W//2, H//2-30, int(250*gp), FUCHSIA, 0.08*gp)

        if logo:
            la = ease_out(min(1.0, t / 2.0))
            sc = 0.85 + 0.15 * ease_out(min(1.0, t / 2.5))
            lw = int(300 * sc)
            lh = int(logo.height * lw / logo.width)
            lr = logo.resize((lw, lh), Image.LANCZOS)
            if lr.mode == 'RGBA':
                r, g, b, a = lr.split()
                a = a.point(lambda x: int(x * la))
                lr = Image.merge('RGBA', (r, g, b, a))
            lx, ly = (W-lw)//2, (H-lh)//2-80
            img = add_glow(img, W//2, ly+lh//2, int(180*la), VIOLET, 0.35*la)
            img.paste(lr, (lx, ly), lr)

        if t > 3.0:
            a = ease_out(min(1.0, (t-3.0)/1.0))
            yo = int(15*(1-a))
            f = get_bold_font(36)
            txt = "Vous payez votre énergie trop cher."
            ov = Image.new('RGBA', (W,H), (0,0,0,0))
            d = ImageDraw.Draw(ov)
            tx = text_center(d, txt, f)
            d.text((tx+2, H//2+62+yo), txt, fill=(0,0,0,int(180*a)), font=f)
            d.text((tx, H//2+60+yo), txt, fill=(*BLANC,int(255*a)), font=f)
            img = Image.alpha_composite(img, ov)

        if t > 5.0:
            a = ease_out(min(1.0, (t-5.0)/0.8))
            f = get_font(26)
            txt = "Et vous ne le savez pas."
            ov = Image.new('RGBA', (W,H), (0,0,0,0))
            d = ImageDraw.Draw(ov)
            tx = text_center(d, txt, f)
            d.text((tx, H//2+115), txt, fill=(*LAVANDE,int(220*a)), font=f)
            img = Image.alpha_composite(img, ov)

        return np.array(img.convert('RGB'))

    c = VideoClip(frame, duration=dur)
    if logo_vid: logo_vid.close()
    return c


# ======================================================================
#  SCENE 2: LE PROBLÈME (8-18s) — 10s
# ======================================================================
def make_scene2():
    dur = 10.0
    bg = load_vid("energie.mp4")

    def frame(t):
        if bg:
            try:
                img = Image.fromarray(bg.get_frame(t % bg.duration))
            except:
                img = Image.new('RGB', (W,H), FOND)
        else:
            img = Image.new('RGB', (W,H), FOND)

        dark = Image.new('RGBA', (W,H), (6,6,15,160))
        img = Image.alpha_composite(img.convert('RGBA'), dark)

        if t > 0.5:
            a = ease_out(min(1.0, (t-0.5)/0.8))
            yo = int(12*(1-a))
            f = get_font(28)
            txt = "Le marché de l'énergie est ouvert."
            ov = Image.new('RGBA', (W,H), (0,0,0,0))
            d = ImageDraw.Draw(ov)
            tx = text_center(d, txt, f)
            d.text((tx+2, 122+yo), txt, fill=(0,0,0,int(160*a)), font=f)
            d.text((tx, 120+yo), txt, fill=(*BLANC,int(255*a)), font=f)
            img = Image.alpha_composite(img, ov)

        if t > 2.5:
            a = ease_out(min(1.0, (t-2.5)/0.8))
            f = get_font(24)
            txt = "Les prix varient. Les offres se multiplient."
            ov = Image.new('RGBA', (W,H), (0,0,0,0))
            d = ImageDraw.Draw(ov)
            tx = text_center(d, txt, f)
            d.text((tx, 170), txt, fill=(*LAVANDE,int(220*a)), font=f)
            img = Image.alpha_composite(img, ov)

        if t > 4.0:
            np_ = ease_out(min(1.0, (t-4.0)/1.2))
            fb = get_bold_font(180)
            t18 = "18%"
            img = add_glow(img, W//2, 370, int(180*np_), FUCHSIA, 0.45*np_)
            img = add_glow(img, W//2, 370, int(120*np_), VIOLET, 0.3*np_)
            tmp = img.convert('RGB')
            dr = ImageDraw.Draw(tmp)
            tx = text_center(dr, t18, fb)
            dr.text((tx+3, 273), t18, fill=(0,0,0), font=fb)
            dr.text((tx, 270), t18, fill=FUCHSIA, font=fb)
            img = tmp.convert('RGBA')

        if t > 6.5:
            a = ease_out(min(1.0, (t-6.5)/0.7))
            f = get_font(22)
            txt = "Vous surpayez peut-être 18% chaque année"
            ov = Image.new('RGBA', (W,H), (0,0,0,0))
            d = ImageDraw.Draw(ov)
            d.rectangle([0,H-80,W,H], fill=(10,6,24,int(200*a)))
            tx = text_center(d, txt, f)
            d.text((tx, H-60), txt, fill=(*BLANC,int(255*a)), font=f)
            img = Image.alpha_composite(img, ov)

        return np.array(img.convert('RGB'))

    return VideoClip(frame, duration=dur)


# ======================================================================
#  SCENE 3: QUI SOMMES-NOUS (18-30s) — 12s
# ======================================================================
def make_scene3():
    dur = 12.0
    bg = load_vid("agence .mp4") or load_vid("personne travaille.mp4")
    lines = [("Analyse gratuite", VERT), ("Comparaison marché complet", VERT), ("Négociation professionnelle", VERT)]

    def frame(t):
        if bg:
            try:
                img = Image.fromarray(bg.get_frame(t % bg.duration))
            except:
                img = Image.new('RGB', (W,H), FOND)
        else:
            img = Image.new('RGB', (W,H), FOND)

        dark = Image.new('RGBA', (W,H), (6,6,15,170))
        img = Image.alpha_composite(img.convert('RGBA'), dark)

        # "LILIWATT" letter by letter
        if t > 0.5:
            ft = get_bold_font(72)
            word = "LILIWATT"
            shown = min(len(word), int((t-0.5)/0.15)+1)
            partial = word[:shown]
            ov = Image.new('RGBA', (W,H), (0,0,0,0))
            d = ImageDraw.Draw(ov)
            full_bbox = d.textbbox((0,0), word, font=ft)
            ftw = full_bbox[2]-full_bbox[0]
            tx = (W-ftw)//2
            d.text((tx+3, 103), partial, fill=(0,0,0,200), font=ft)
            d.text((tx, 100), partial, fill=(*FUCHSIA,255), font=ft)
            img = Image.alpha_composite(img, ov)

        if t > 2.5:
            a = ease_out(min(1.0, (t-2.5)/0.7))
            f = get_font(26)
            txt = "est né d'une conviction simple."
            ov = Image.new('RGBA', (W,H), (0,0,0,0))
            d = ImageDraw.Draw(ov)
            tx = text_center(d, txt, f)
            d.text((tx, 190), txt, fill=(*LAVANDE,int(255*a)), font=f)
            img = Image.alpha_composite(img, ov)

        if t > 4.0:
            a = ease_out(min(1.0, (t-4.0)/0.8))
            f = get_bold_font(28)
            txt = "Chaque professionnel mérite le juste prix."
            ov = Image.new('RGBA', (W,H), (0,0,0,0))
            d = ImageDraw.Draw(ov)
            tx = text_center(d, txt, f)
            yo = int(12*(1-a))
            d.text((tx+2, 252+yo), txt, fill=(0,0,0,int(180*a)), font=f)
            d.text((tx, 250+yo), txt, fill=(*BLANC,int(255*a)), font=f)
            img = Image.alpha_composite(img, ov)

        fl, fc = get_font(30), get_bold_font(32)
        for i, (line, color) in enumerate(lines):
            st = 6.0 + i*1.5
            if t > st:
                p = ease_out(min(1.0, (t-st)/0.7))
                yb = 340 + i*70
                yo = int(20*(1-p))
                al = int(255*p)
                ov = Image.new('RGBA', (W,H), (0,0,0,0))
                d = ImageDraw.Draw(ov)
                bbox = d.textbbox((0,0), line, font=fl)
                tw = bbox[2]-bbox[0]
                pw = tw+110
                px = (W-pw)//2
                d.rounded_rectangle([px, yb+yo-10, px+pw, yb+yo+48], radius=24, fill=(10,6,24,int(190*p)))
                cx = px+20
                d.text((cx, yb+yo), "✓", fill=(*color,al), font=fc)
                d.text((cx+45, yb+yo+2), line, fill=(*BLANC,al), font=fl)
                img = Image.alpha_composite(img, ov)

        return np.array(img.convert('RGB'))

    return VideoClip(frame, duration=dur)


# ======================================================================
#  SCENE 4: NOS CLIENTS (30-42s) — 12s
# ======================================================================
def make_scene4():
    dur = 12.0
    bg = load_vid("exterieur.mp4") or load_vid("repartition.mp4")
    sectors = ["Restaurants", "Boulangeries", "Hôtels", "Laveries", "PME"]

    def frame(t):
        if bg:
            try:
                img = Image.fromarray(bg.get_frame(t % bg.duration))
            except:
                img = Image.new('RGB', (W,H), FOND)
        else:
            img = Image.new('RGB', (W,H), FOND)

        dark = Image.new('RGBA', (W,H), (6,6,15,155))
        img = Image.alpha_composite(img.convert('RGBA'), dark)

        if t > 0.5:
            f = get_bold_font(34)
            vc = min(len(sectors), int((t-0.5)/1.2)+1)
            stxt = " · ".join(sectors[:vc])
            ov = Image.new('RGBA', (W,H), (0,0,0,0))
            d = ImageDraw.Draw(ov)
            a = ease_out(min(1.0, (t-0.5)/0.6))
            tx = text_center(d, stxt, f)
            d.text((tx+2, 102), stxt, fill=(0,0,0,int(160*a)), font=f)
            d.text((tx, 100), stxt, fill=(*LAVANDE,int(255*a)), font=f)
            img = Image.alpha_composite(img, ov)

        if t > 5.0:
            cp = ease_out(min(1.0, (t-5.0)/2.0))
            val = int(1460*cp)
            tv = f"{val:,}€".replace(",", " ")
            fc = get_bold_font(120)
            img = add_glow(img, W//2, 340, int(160*cp), ROUGE, 0.4*cp)
            img = add_glow(img, W//2, 340, int(100*cp), FUCHSIA, 0.25*cp)
            tmp = img.convert('RGB')
            dr = ImageDraw.Draw(tmp)
            tx = text_center(dr, tv, fc)
            dr.text((tx+3, 263), tv, fill=(0,0,0), font=fc)
            dr.text((tx, 260), tv, fill=ROUGE, font=fc)
            img = tmp.convert('RGBA')

        if t > 6.5:
            a = ease_out(min(1.0, (t-6.5)/0.7))
            f = get_font(26)
            txt = "économisés en moyenne par an"
            ov = Image.new('RGBA', (W,H), (0,0,0,0))
            d = ImageDraw.Draw(ov)
            tx = text_center(d, txt, f)
            d.text((tx, 410), txt, fill=(*BLANC,int(220*a)), font=f)
            img = Image.alpha_composite(img, ov)

        if t > 8.5:
            a = ease_out(min(1.0, (t-8.5)/0.8))
            f = get_bold_font(28)
            txt = "0€ de frais  ·  3 semaines  ·  Sans coupure"
            ov = Image.new('RGBA', (W,H), (0,0,0,0))
            d = ImageDraw.Draw(ov)
            d.rectangle([0,H-90,W,H], fill=(10,6,24,int(210*a)))
            tx = text_center(d, txt, f)
            d.text((tx, H-68), txt, fill=(*VERT,int(255*a)), font=f)
            img = Image.alpha_composite(img, ov)

        return np.array(img.convert('RGB'))

    return VideoClip(frame, duration=dur)


# ======================================================================
#  SCENE 5: SIMPLICITÉ (42-52s) — 10s
# ======================================================================
def make_scene5():
    dur = 10.0
    bg = load_vid("personne travaille.mp4") or load_vid("liste fournisseurs .mp4")
    impact = [("Sans frais.", 1.5), ("Sans coupure.", 4.0), ("Sans démarche.", 6.5)]

    def frame(t):
        if bg:
            try:
                img = Image.fromarray(bg.get_frame(t % bg.duration))
            except:
                img = Image.new('RGB', (W,H), FOND)
        else:
            img = Image.new('RGB', (W,H), FOND)

        dark = Image.new('RGBA', (W,H), (6,6,15,175))
        img = Image.alpha_composite(img.convert('RGBA'), dark)

        if t > 0.3:
            a = ease_out(min(1.0, (t-0.3)/0.6))
            f = get_bold_font(32)
            txt = "LILIWATT s'occupe de tout."
            ov = Image.new('RGBA', (W,H), (0,0,0,0))
            d = ImageDraw.Draw(ov)
            tx = text_center(d, txt, f)
            d.text((tx+2, 102), txt, fill=(0,0,0,int(180*a)), font=f)
            d.text((tx, 100), txt, fill=(*FUCHSIA,int(255*a)), font=f)
            bbox = d.textbbox((0,0), txt, font=f)
            tw = bbox[2]-bbox[0]
            d.rectangle([tx, 145, tx+int(tw*a), 148], fill=(*FUCHSIA,int(200*a)))
            img = Image.alpha_composite(img, ov)

        fi = get_bold_font(64)
        for txt, st in impact:
            if t > st:
                p = ease_out(min(1.0, (t-st)/0.6))
                et = st + 2.2
                if t > et and txt != impact[-1][0]:
                    fade = max(0, 1.0-(t-et)/0.4)
                else:
                    fade = 1.0
                al = p * fade
                yo = int(25*(1-p))
                if al > 0.05:
                    img = add_glow(img, W//2, 330+yo, int(100*al), VIOLET, 0.3*al)
                    ov = Image.new('RGBA', (W,H), (0,0,0,0))
                    d = ImageDraw.Draw(ov)
                    tx = text_center(d, txt, fi)
                    d.text((tx+3, 303+yo), txt, fill=(0,0,0,int(200*al)), font=fi)
                    d.text((tx, 300+yo), txt, fill=(*BLANC,int(255*al)), font=fi)
                    img = Image.alpha_composite(img, ov)

        return np.array(img.convert('RGB'))

    return VideoClip(frame, duration=dur)


# ======================================================================
#  SCENE 6: CTA FINAL (52-63s) — 11s
# ======================================================================
def make_scene6():
    dur = 11.0
    logo = load_logo()

    def frame(t):
        img = Image.new('RGB', (W,H), FOND).convert('RGBA')
        gp = ease_out(min(1.0, t/1.5))
        img = add_glow(img, W//2, H//2-60, int(450*gp), VIOLET, 0.18*gp)
        img = add_glow(img, W//2, H//2-60, int(300*gp), FUCHSIA, 0.12*gp)

        if logo:
            la = ease_out(min(1.0, t/1.3))
            sc = 0.8+0.2*ease_out(min(1.0, t/2.0))
            lw = int(350*sc)
            lh = int(logo.height*lw/logo.width)
            lr = logo.resize((lw,lh), Image.LANCZOS)
            if lr.mode == 'RGBA':
                r,g,b,a = lr.split()
                a = a.point(lambda x: int(x*la))
                lr = Image.merge('RGBA', (r,g,b,a))
            lx, ly = (W-lw)//2, 80
            img = add_glow(img, W//2, ly+lh//2, int(220*la), VIOLET, 0.45*la)
            img.paste(lr, (lx,ly), lr)

        if t > 1.5:
            a = ease_out(min(1.0, (t-1.5)/0.8))
            f = get_bold_font(44)
            txt = "Votre énergie mérite mieux."
            ov = Image.new('RGBA', (W,H), (0,0,0,0))
            d = ImageDraw.Draw(ov)
            tx = text_center(d, txt, f)
            yo = int(15*(1-a))
            d.text((tx+2, 332+yo), txt, fill=(0,0,0,int(180*a)), font=f)
            d.text((tx, 330+yo), txt, fill=(*BLANC,int(255*a)), font=f)
            img = Image.alpha_composite(img, ov)

        if t > 2.8:
            a = ease_out(min(1.0, (t-2.8)/0.7))
            f = get_bold_font(60)
            txt = "liliwatt.fr"
            ov = Image.new('RGBA', (W,H), (0,0,0,0))
            d = ImageDraw.Draw(ov)
            tx = text_center(d, txt, f)
            img = add_glow(img, W//2, 445, int(130*a), FUCHSIA, 0.35*a)
            d.text((tx+2, 418), txt, fill=(0,0,0,int(180*a)), font=f)
            d.text((tx, 416), txt, fill=(*FUCHSIA,int(255*a)), font=f)
            img = Image.alpha_composite(img, ov)

        if t > 4.0:
            a = ease_out(min(1.0, (t-4.0)/0.7))
            f = get_font(26)
            txt = "Analyse gratuite · Sans engagement"
            ov = Image.new('RGBA', (W,H), (0,0,0,0))
            d = ImageDraw.Draw(ov)
            tx = text_center(d, txt, f)
            bbox = d.textbbox((0,0), txt, font=f)
            tw = bbox[2]-bbox[0]
            d.rounded_rectangle([tx-25, 508, tx+tw+25, 550], radius=22, fill=(124,58,237,int(130*a)))
            d.text((tx, 514), txt, fill=(*BLANC,int(255*a)), font=f)
            img = Image.alpha_composite(img, ov)

        img = img.convert('RGB')
        if t > dur - 1.0:
            fade = max(0, 1.0 - (t - (dur - 1.0)) / 1.0)
            arr = np.array(img).astype(float) * fade
            return arr.astype(np.uint8)

        return np.array(img)

    return VideoClip(frame, duration=dur)


# ======================================================================
#  MAIN
# ======================================================================
def main():
    print("=" * 60)
    print("  LILIWATT — Vidéo publicitaire FINALE avec voix off")
    print("=" * 60)

    print("\n[1/6] Scène 1 — Intro + Logo (0-8s)...")
    s1 = make_scene1()
    print("[2/6] Scène 2 — Le Problème (8-18s)...")
    s2 = make_scene2()
    print("[3/6] Scène 3 — Qui sommes-nous (18-30s)...")
    s3 = make_scene3()
    print("[4/6] Scène 4 — Nos Clients (30-42s)...")
    s4 = make_scene4()
    print("[5/6] Scène 5 — Simplicité (42-52s)...")
    s5 = make_scene5()
    print("[6/6] Scène 6 — CTA Final (52-63s)...")
    s6 = make_scene6()

    print("\nAssemblage avec fondus enchaînés...")
    cf = 0.5
    scenes = [s1, s2, s3, s4, s5, s6]
    clips = []
    for i, s in enumerate(scenes):
        c = s
        if i == 0:
            c = c.with_effects([CrossFadeIn(0.3)])
        if i < len(scenes) - 1:
            c = c.with_effects([CrossFadeOut(cf)])
        clips.append(c)

    video = concatenate_videoclips(clips, method="compose", padding=-cf)
    print(f"  Durée brute vidéo: {video.duration:.1f}s")

    # === AUDIO ===
    print("\nPréparation audio...")
    audio_tracks = []

    if os.path.exists(MUSIC_PATH):
        music = AudioFileClip(MUSIC_PATH)
        if music.duration < video.duration:
            music = music.with_effects([AudioLoop(duration=video.duration)])
        else:
            music = music.subclipped(0, video.duration)
        music = music.with_effects([MultiplyVolume(0.12)])
        audio_tracks.append(music)
        print(f"  ✅ Musique: {music.duration:.1f}s (vol 12%)")

    if os.path.exists(VOIX_PATH):
        voix = AudioFileClip(VOIX_PATH)
        # Trim voice to video duration if needed
        if voix.duration > video.duration:
            voix = voix.subclipped(0, video.duration)
        audio_tracks.append(voix)
        print(f"  ✅ Voix off: {voix.duration:.1f}s")

        # Adjust video duration to match voice if voice is longer
        if voix.duration > video.duration:
            print(f"  ⚠️  Voix plus longue que vidéo — vidéo ajustée")
    else:
        print("  ⚠️  Pas de voix off")

    if audio_tracks:
        audio_final = CompositeAudioClip(audio_tracks)
        video = video.with_audio(audio_final)

    # === EXPORT ===
    print(f"\n🎬 Rendu → {OUTPUT}")
    print(f"   {W}x{H} | {FPS}fps | ~{video.duration:.1f}s | bitrate=5000k")

    video.write_videofile(
        OUTPUT, fps=FPS, codec='libx264',
        audio_codec='aac', bitrate='5000k',
        preset='medium', threads=4, logger='bar'
    )

    sz = os.path.getsize(OUTPUT)
    print(f"\n{'=' * 60}")
    print(f"  ✅ VIDÉO FINALE EXPORTÉE !")
    print(f"  📁 {OUTPUT}")
    print(f"  📐 {W}x{H} | {FPS} fps")
    print(f"  ⏱️  {video.duration:.1f} secondes")
    print(f"  💾 {sz/(1024*1024):.1f} MB")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
