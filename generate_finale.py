#!/usr/bin/env python3
"""
LILIWATT — Vidéo publicitaire finale 30 secondes
Avec visuels fal.ai + musique disco funk
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy import (
    VideoClip, ImageClip, AudioFileClip, CompositeAudioClip,
    CompositeVideoClip, concatenate_videoclips, ColorClip
)
from moviepy.video.fx import CrossFadeIn, CrossFadeOut

# === CONFIG ===
W, H = 1280, 720
FPS = 25

# Couleurs LILIWATT
FOND = (10, 6, 24)  # #0A0618
FOND_DARK = (6, 6, 15)  # #06060F
VIOLET = (124, 58, 237)
FUCHSIA = (217, 70, 239)
LAVANDE = (167, 139, 250)
BLANC = (240, 238, 255)
VERT = (34, 197, 94)
ROUGE = (239, 68, 68)

BASE = os.path.expanduser("~/Desktop/liliwatt-website")
GEN_IMG = os.path.join(BASE, "images", "generated")
LOGO_PATH = os.path.join(BASE, "assets/images/logo-liliwatt.png")
MUSIC_PATH = os.path.join(BASE, "musique_disco.mp3")
OUTPUT = os.path.join(BASE, "pub_liliwatt_finale.mp4")


# === FONT HELPERS ===
def get_font(size, bold=False):
    paths = [
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
    ]
    for fp in paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()

def get_bold_font(size):
    return get_font(size, bold=True)


# === UTILITY ===
def ease_out(t):
    return 1 - (1 - min(1.0, max(0.0, t))) ** 3

def ease_in_out(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)

def create_gradient_bg(w, h, color1, color2):
    img = Image.new('RGB', (w, h))
    draw = ImageDraw.Draw(img)
    for i in range(h):
        ratio = i / h
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        draw.line([(0, i), (w, i)], fill=(r, g, b))
    return img

def add_glow(img, x, y, radius, color, intensity=0.5):
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for r in range(radius, 0, -3):
        alpha = int(intensity * 255 * (1 - r / radius) ** 2)
        c = (*color, min(255, alpha))
        draw.ellipse([x - r, y - r, x + r, y + r], fill=c)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    return Image.alpha_composite(img, overlay)

def load_logo():
    if os.path.exists(LOGO_PATH):
        return Image.open(LOGO_PATH).convert('RGBA')
    return None

def load_gen_image(name):
    path = os.path.join(GEN_IMG, f"{name}.png")
    if os.path.exists(path):
        return Image.open(path).convert('RGB')
    return None

def ken_burns_crop(img, w, h, zoom, pan_x=0.5, pan_y=0.5):
    """Apply Ken Burns zoom + crop to target size"""
    img_w = int(w * zoom)
    img_h = int(h * zoom)
    resized = img.resize((img_w, img_h), Image.LANCZOS)
    left = int((img_w - w) * pan_x)
    top = int((img_h - h) * pan_y)
    return resized.crop((left, top, left + w, top + h))

def draw_text_with_shadow(draw, pos, text, font, fill, shadow_color=(0,0,0), offset=2):
    x, y = pos
    draw.text((x + offset, y + offset), text, fill=shadow_color, font=font)
    draw.text((x, y), text, fill=fill, font=font)

def text_center_x(draw, text, font, y, img_width=W):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    return (img_width - tw) // 2


# === SCENE 1: LOGO INTRO (0-4 sec) ===
def make_scene1():
    duration = 4.0
    logo = load_logo()

    def make_frame(t):
        img = Image.new('RGB', (W, H), FOND)

        # Multiple glow layers
        img_rgba = img.convert('RGBA')
        glow_progress = ease_out(t / 2.0)

        # Big ambient glow
        img_rgba = add_glow(img_rgba, W // 2, H // 2, int(350 * glow_progress), VIOLET, 0.12 * glow_progress)
        img_rgba = add_glow(img_rgba, W // 2, H // 2 - 30, int(200 * glow_progress), FUCHSIA, 0.08 * glow_progress)

        # Logo
        if logo:
            logo_alpha = ease_out(min(1.0, t / 1.5))
            # Scale animation
            scale = 0.8 + 0.2 * ease_out(min(1.0, t / 2.0))
            logo_w = int(280 * scale)
            logo_h = int(logo.height * logo_w / logo.width)
            logo_resized = logo.resize((logo_w, logo_h), Image.LANCZOS)

            if logo_resized.mode == 'RGBA':
                r, g, b, a = logo_resized.split()
                a = a.point(lambda x: int(x * logo_alpha))
                logo_resized = Image.merge('RGBA', (r, g, b, a))

            lx = (W - logo_w) // 2
            ly = (H - logo_h) // 2 - 30

            # Glow behind logo
            img_rgba = add_glow(img_rgba, W // 2, ly + logo_h // 2,
                               int(160 * logo_alpha), VIOLET, 0.35 * logo_alpha)

            img_rgba.paste(logo_resized, (lx, ly), logo_resized)

        # Subtle tagline at bottom
        if t > 2.5:
            ta = ease_out(min(1.0, (t - 2.5) / 1.0))
            font_tag = get_font(22)
            tag = "Courtier en énergie pour professionnels"
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            bbox = od.textbbox((0, 0), tag, font=font_tag)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2
            od.text((tx, H // 2 + 100), tag, fill=(*LAVANDE, int(200 * ta)), font=font_tag)
            img_rgba = Image.alpha_composite(img_rgba, overlay)

        img = img_rgba.convert('RGB')
        return np.array(img)

    return VideoClip(make_frame, duration=duration)


# === SCENE 2: LE PROBLÈME - RESTAURANT (4-9 sec) ===
def make_scene2():
    duration = 5.0
    bg = load_gen_image("restaurant")

    def make_frame(t):
        if bg:
            zoom = 1.05 + 0.05 * (t / duration)
            img = ken_burns_crop(bg, W, H, zoom, 0.5, 0.4)
            # Dark overlay
            dark = Image.new('RGBA', (W, H), (6, 6, 15, 160))
            img = Image.alpha_composite(img.convert('RGBA'), dark).convert('RGB')
        else:
            img = create_gradient_bg(W, H, FOND, (26, 10, 46))

        draw = ImageDraw.Draw(img)

        # Bottom text bar
        if t > 0.5:
            bar_alpha = ease_out(min(1.0, (t - 0.5) / 0.6))
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            # Semi-transparent bar at bottom
            od.rectangle([0, H - 160, W, H], fill=(6, 6, 15, int(200 * bar_alpha)))
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)

        # Text lines
        font_main = get_bold_font(34)
        font_sub = get_font(26)

        texts = [
            (1.0, "Des restaurateurs. Des boulangers.", font_main, BLANC),
            (1.8, "Des hôteliers. Des commerçants.", font_sub, LAVANDE),
        ]

        for start, text, font, color in texts:
            if t > start:
                progress = ease_out(min(1.0, (t - start) / 0.7))
                y_off = int(15 * (1 - progress))
                overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                od = ImageDraw.Draw(overlay)
                bbox = od.textbbox((0, 0), text, font=font)
                tw = bbox[2] - bbox[0]
                tx = (W - tw) // 2
                idx = texts.index((start, text, font, color))
                ty = H - 140 + idx * 45 + y_off
                od.text((tx + 2, ty + 2), text, fill=(0, 0, 0, int(180 * progress)), font=font)
                od.text((tx, ty), text, fill=(*color, int(255 * progress)), font=font)
                img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

        return np.array(img)

    return VideoClip(make_frame, duration=duration)


# === SCENE 3: 18% - BOULANGER (9-14 sec) ===
def make_scene3():
    duration = 5.0
    bg = load_gen_image("boulanger")

    def make_frame(t):
        if bg:
            zoom = 1.05 + 0.05 * (t / duration)
            img = ken_burns_crop(bg, W, H, zoom, 0.5, 0.45)
            dark = Image.new('RGBA', (W, H), (6, 6, 15, 170))
            img = Image.alpha_composite(img.convert('RGBA'), dark).convert('RGB')
        else:
            img = create_gradient_bg(W, H, FOND, (26, 10, 46))

        draw = ImageDraw.Draw(img)

        # "Ils surpaient jusqu'à"
        if t > 0.5:
            a = ease_out(min(1.0, (t - 0.5) / 0.8))
            font = get_font(28)
            text = "Ils surpaient jusqu'à"
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            bbox = od.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2
            od.text((tx + 2, 202), text, fill=(0, 0, 0, int(180 * a)), font=font)
            od.text((tx, 200), text, fill=(*BLANC, int(255 * a)), font=font)
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)

        # Big 18%
        if t > 1.5:
            num_p = ease_out(min(1.0, (t - 1.5) / 1.0))
            font_big = get_bold_font(160)
            text_18 = "18%"

            # Glow
            img_rgba = img.convert('RGBA')
            img_rgba = add_glow(img_rgba, W // 2, 370, int(150 * num_p), FUCHSIA, 0.4 * num_p)
            img_rgba = add_glow(img_rgba, W // 2, 370, int(100 * num_p), VIOLET, 0.3 * num_p)
            img = img_rgba.convert('RGB')
            draw = ImageDraw.Draw(img)

            bbox = draw.textbbox((0, 0), text_18, font=font_big)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = (W - tw) // 2
            ty = 280

            # Shadow
            draw.text((tx + 3, ty + 3), text_18, fill=(0, 0, 0), font=font_big)
            draw.text((tx, ty), text_18, fill=FUCHSIA, font=font_big)

        # "sur leur facture d'énergie"
        if t > 3.0:
            a = ease_out(min(1.0, (t - 3.0) / 0.7))
            font = get_font(26)
            text = "sur leur facture d'énergie"
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            bbox = od.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2
            od.text((tx, 480), text, fill=(*LAVANDE, int(255 * a)), font=font)
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

        return np.array(img)

    return VideoClip(make_frame, duration=duration)


# === SCENE 4: LA SOLUTION - CONSEILLER (14-20 sec) ===
def make_scene4():
    duration = 6.0
    bg = load_gen_image("conseiller")

    lines = [
        ("Analyse de votre contrat", VERT),
        ("Comparaison du marché", VERT),
        ("Négociation du meilleur tarif", VERT),
    ]

    def make_frame(t):
        if bg:
            zoom = 1.03 + 0.04 * (t / duration)
            img = ken_burns_crop(bg, W, H, zoom, 0.5, 0.4)
            dark = Image.new('RGBA', (W, H), (6, 6, 15, 175))
            img = Image.alpha_composite(img.convert('RGBA'), dark).convert('RGB')
        else:
            img = create_gradient_bg(W, H, FOND, (26, 10, 46))

        draw = ImageDraw.Draw(img)

        # Title "LILIWATT change ça."
        if t > 0.3:
            a = ease_out(min(1.0, (t - 0.3) / 0.7))
            font_title = get_bold_font(44)
            text = "LILIWATT change ça."
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            bbox = od.textbbox((0, 0), text, font=font_title)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2
            od.text((tx + 2, 142), text, fill=(0, 0, 0, int(200 * a)), font=font_title)
            od.text((tx, 140), text, fill=(*BLANC, int(255 * a)), font=font_title)
            # Underline
            od.rectangle([tx, 195, tx + int(tw * a), 198], fill=(*FUCHSIA, int(255 * a)))
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)

        # Checklist lines
        font_line = get_font(32)
        font_check = get_bold_font(34)

        for i, (line, color) in enumerate(lines):
            start_time = 1.5 + i * 1.0
            if t > start_time:
                progress = ease_out(min(1.0, (t - start_time) / 0.7))
                y_base = 280 + i * 75
                y_offset = int(25 * (1 - progress))
                alpha = int(255 * progress)

                overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                od = ImageDraw.Draw(overlay)

                # Background pill for each line
                bbox = od.textbbox((0, 0), line, font=font_line)
                tw = bbox[2] - bbox[0]
                pill_w = tw + 100
                pill_x = (W - pill_w) // 2
                od.rounded_rectangle(
                    [pill_x, y_base + y_offset - 8, pill_x + pill_w, y_base + y_offset + 50],
                    radius=25,
                    fill=(10, 6, 24, int(180 * progress))
                )

                # Checkmark
                check_x = pill_x + 20
                od.text((check_x, y_base + y_offset), "✓", fill=(*color, alpha), font=font_check)

                # Text
                text_x = check_x + 45
                od.text((text_x, y_base + y_offset + 2), line, fill=(*BLANC, alpha), font=font_line)

                img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
                draw = ImageDraw.Draw(img)

        return np.array(img)

    return VideoClip(make_frame, duration=duration)


# === SCENE 5: LES CHIFFRES - ÉCONOMIE (20-25 sec) ===
def make_scene5():
    duration = 5.0
    bg = load_gen_image("economie")

    stats = [
        {"value": 1460, "suffix": "€", "label": "économisés / an", "color": ROUGE},
        {"value": 0, "suffix": "€", "label": "de frais", "color": VERT},
        {"value": 3, "suffix": " sem.", "label": "pour changer", "color": LAVANDE},
    ]

    def make_frame(t):
        if bg:
            zoom = 1.05 + 0.04 * (t / duration)
            img = ken_burns_crop(bg, W, H, zoom)
            dark = Image.new('RGBA', (W, H), (6, 6, 15, 190))
            img = Image.alpha_composite(img.convert('RGBA'), dark).convert('RGB')
        else:
            img = Image.new('RGB', (W, H), FOND)

        draw = ImageDraw.Draw(img)

        # Animated particles
        img_rgba = img.convert('RGBA')
        for j in range(12):
            seed = j * 137 + 42
            px = int((seed * 7 + int(t * 25) * (j + 1)) % W)
            py = int((seed * 13 + int(t * 15) * (j + 2)) % H)
            size = 2 + (seed % 3)
            alpha_p = 25 + (seed % 40)
            particle = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            pd = ImageDraw.Draw(particle)
            pd.ellipse([px - size, py - size, px + size, py + size],
                      fill=(*VIOLET, alpha_p))
            img_rgba = Image.alpha_composite(img_rgba, particle)
        img = img_rgba.convert('RGB')
        draw = ImageDraw.Draw(img)

        # Title
        if t > 0.2:
            ta = ease_out(min(1.0, (t - 0.2) / 0.5))
            font_title = get_bold_font(38)
            title = "Résultats concrets"
            bbox = draw.textbbox((0, 0), title, font=font_title)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2
            draw.text((tx + 2, 72), title, fill=(0, 0, 0), font=font_title)
            draw.text((tx, 70), title, fill=BLANC, font=font_title)

        # Stats
        font_num = get_bold_font(80)
        font_label = get_font(22)
        col_width = W // 3

        for i, stat in enumerate(stats):
            start_time = 0.8 + i * 1.0
            if t > start_time:
                progress = ease_out(min(1.0, (t - start_time) / 0.9))
                current_val = int(stat["value"] * progress)
                text_val = f"{current_val}{stat['suffix']}"
                cx = col_width * i + col_width // 2

                # Glow
                img_rgba = img.convert('RGBA')
                img_rgba = add_glow(img_rgba, cx, 310, int(70 * progress), stat["color"], 0.25 * progress)
                img = img_rgba.convert('RGB')
                draw = ImageDraw.Draw(img)

                # Number
                bbox = draw.textbbox((0, 0), text_val, font=font_num)
                tw = bbox[2] - bbox[0]
                tx = cx - tw // 2
                draw.text((tx + 2, 262), text_val, fill=(0, 0, 0), font=font_num)
                draw.text((tx, 260), text_val, fill=stat["color"], font=font_num)

                # Label
                if progress > 0.4:
                    label_a = min(1.0, (progress - 0.4) / 0.6)
                    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                    od = ImageDraw.Draw(overlay)
                    lbbox = od.textbbox((0, 0), stat["label"], font=font_label)
                    ltw = lbbox[2] - lbbox[0]
                    lx = cx - ltw // 2
                    od.text((lx, 380), stat["label"],
                           fill=(*BLANC, int(200 * label_a)), font=font_label)
                    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
                    draw = ImageDraw.Draw(img)

        # Dividers
        if t > 1.2:
            div_a = min(1.0, (t - 1.2) / 0.5)
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            for i in range(1, 3):
                x = col_width * i
                od.line([(x, 240), (x, 400)], fill=(*VIOLET, int(80 * div_a)), width=1)
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

        # Bottom text
        if t > 3.5:
            ba = ease_out(min(1.0, (t - 3.5) / 0.8))
            font_bot = get_font(24)
            txt = "Gratuitement. Sans coupure. En trois semaines."
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            bbox = od.textbbox((0, 0), txt, font=font_bot)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2
            od.text((tx, 500), txt, fill=(*LAVANDE, int(255 * ba)), font=font_bot)
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

        return np.array(img)

    return VideoClip(make_frame, duration=duration)


# === SCENE 6: CTA FINAL (25-30 sec) ===
def make_scene6():
    duration = 5.0
    logo = load_logo()

    def make_frame(t):
        img = Image.new('RGB', (W, H), FOND)
        img_rgba = img.convert('RGBA')

        # Multi-layer glow
        glow_p = ease_out(min(1.0, t / 1.5))
        img_rgba = add_glow(img_rgba, W // 2, H // 2 - 50, int(400 * glow_p), VIOLET, 0.15 * glow_p)
        img_rgba = add_glow(img_rgba, W // 2, H // 2 - 50, int(250 * glow_p), FUCHSIA, 0.1 * glow_p)
        img_rgba = add_glow(img_rgba, W // 2, H // 2 - 50, int(150 * glow_p), (255, 255, 255), 0.05 * glow_p)

        # Logo - large
        if logo:
            logo_alpha = ease_out(min(1.0, t / 1.2))
            scale = 0.85 + 0.15 * ease_out(min(1.0, t / 1.5))
            logo_w = int(320 * scale)
            logo_h = int(logo.height * logo_w / logo.width)
            logo_resized = logo.resize((logo_w, logo_h), Image.LANCZOS)

            if logo_resized.mode == 'RGBA':
                r, g, b, a = logo_resized.split()
                a = a.point(lambda x: int(x * logo_alpha))
                logo_resized = Image.merge('RGBA', (r, g, b, a))

            lx = (W - logo_w) // 2
            ly = 100

            img_rgba = add_glow(img_rgba, W // 2, ly + logo_h // 2,
                               int(200 * logo_alpha), VIOLET, 0.4 * logo_alpha)
            img_rgba.paste(logo_resized, (lx, ly), logo_resized)

        # "Votre énergie mérite mieux."
        if t > 1.2:
            fa = ease_out(min(1.0, (t - 1.2) / 0.8))
            font_main = get_bold_font(42)
            text = "Votre énergie mérite mieux."
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            bbox = od.textbbox((0, 0), text, font=font_main)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2
            y_off = int(15 * (1 - fa))
            od.text((tx + 2, 352 + y_off), text, fill=(0, 0, 0, int(180 * fa)), font=font_main)
            od.text((tx, 350 + y_off), text, fill=(*BLANC, int(255 * fa)), font=font_main)
            img_rgba = Image.alpha_composite(img_rgba, overlay)

        # "liliwatt.fr"
        if t > 2.2:
            url_a = ease_out(min(1.0, (t - 2.2) / 0.7))
            font_url = get_bold_font(56)
            url = "liliwatt.fr"
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            bbox = od.textbbox((0, 0), url, font=font_url)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2

            # URL glow
            img_rgba = add_glow(img_rgba, W // 2, 460, int(120 * url_a), FUCHSIA, 0.3 * url_a)

            od.text((tx + 2, 432), url, fill=(0, 0, 0, int(180 * url_a)), font=font_url)
            od.text((tx, 430), url, fill=(*FUCHSIA, int(255 * url_a)), font=font_url)
            img_rgba = Image.alpha_composite(img_rgba, overlay)

        # "Analyse gratuite en 60 secondes"
        if t > 3.2:
            sub_a = ease_out(min(1.0, (t - 3.2) / 0.7))
            font_sub = get_font(26)
            sub = "Analyse gratuite en 60 secondes"
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            bbox = od.textbbox((0, 0), sub, font=font_sub)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2

            # Background pill
            od.rounded_rectangle(
                [tx - 20, 515, tx + tw + 20, 555],
                radius=20,
                fill=(124, 58, 237, int(120 * sub_a))
            )
            od.text((tx, 520), sub, fill=(*BLANC, int(255 * sub_a)), font=font_sub)
            img_rgba = Image.alpha_composite(img_rgba, overlay)

        img = img_rgba.convert('RGB')

        # Fade out last 0.5s
        if t > duration - 0.5:
            fade = 1.0 - (t - (duration - 0.5)) / 0.5
            arr = np.array(img).astype(float) * fade
            return arr.astype(np.uint8)

        return np.array(img)

    return VideoClip(make_frame, duration=duration)


# === MAIN ASSEMBLY ===
def main():
    print("=" * 50)
    print("LILIWATT — Vidéo publicitaire FINALE")
    print("=" * 50)

    print("\n[1/6] Scène 1 — Logo intro...")
    scene1 = make_scene1()

    print("[2/6] Scène 2 — Le Problème (restaurant)...")
    scene2 = make_scene2()

    print("[3/6] Scène 3 — 18% (boulanger)...")
    scene3 = make_scene3()

    print("[4/6] Scène 4 — La Solution (conseiller)...")
    scene4 = make_scene4()

    print("[5/6] Scène 5 — Les Chiffres (économie)...")
    scene5 = make_scene5()

    print("[6/6] Scène 6 — CTA Final...")
    scene6 = make_scene6()

    print("\nAssemblage avec fondus enchaînés...")

    crossfade = 0.5
    scenes = [scene1, scene2, scene3, scene4, scene5, scene6]

    clips = []
    for i, scene in enumerate(scenes):
        clip = scene
        if i == 0:
            clip = clip.with_effects([CrossFadeIn(0.5)])
        if i < len(scenes) - 1:
            clip = clip.with_effects([CrossFadeOut(crossfade)])
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose", padding=-crossfade)

    # Add music
    print("\nAjout de la musique disco funk...")
    if os.path.exists(MUSIC_PATH):
        music = AudioFileClip(MUSIC_PATH)
        # Trim to video duration
        if music.duration > video.duration:
            music = music.subclipped(0, video.duration)
        # Lower volume to 20%
        from moviepy.audio.fx import MultiplyVolume
        music = music.with_effects([MultiplyVolume(0.20)])

        video = video.with_audio(music)
        print(f"  Musique ajoutée ({music.duration:.1f}s)")
    else:
        print("  Pas de musique trouvée, vidéo muette")

    print(f"\nRendu vidéo → {OUTPUT}")
    print(f"Résolution: {W}x{H} | FPS: {FPS} | Durée: ~{video.duration:.1f}s")

    video.write_videofile(
        OUTPUT,
        fps=FPS,
        codec='libx264',
        audio_codec='aac',
        preset='medium',
        threads=4,
        logger='bar'
    )

    print(f"\n{'=' * 50}")
    print(f"VIDÉO FINALE GÉNÉRÉE !")
    print(f"Fichier : {OUTPUT}")
    print(f"Résolution : {W}x{H}")
    print(f"Durée : ~{video.duration:.1f} secondes")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
