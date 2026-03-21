#!/usr/bin/env python3
"""
LILIWATT — Vidéo publicitaire 30 secondes
Slideshow cinématique premium avec moviepy + PIL
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy import (
    ImageClip, CompositeVideoClip, concatenate_videoclips,
    ColorClip, TextClip
)

# === CONFIG ===
W, H = 1280, 720
FPS = 25
DURATION = 30

# Couleurs LILIWATT
FOND = (6, 6, 15)
VIOLET = (124, 58, 237)
FUCHSIA = (217, 70, 239)
LAVANDE = (167, 139, 250)
BLANC = (240, 238, 255)
VERT = (34, 197, 94)
ROUGE = (239, 68, 68)

# Paths
BASE = os.path.expanduser("~/Desktop/liliwatt-website")
LOGO_PATH = os.path.join(BASE, "assets/images/logo-liliwatt.png")
IMG_DIR = os.path.join(BASE, "images")
OUTPUT = os.path.join(BASE, "pub_liliwatt.mp4")

# Font helpers
def get_font(size, bold=False):
    """Get a system font that works on macOS"""
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()

def get_bold_font(size):
    bold_paths = [
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
    ]
    for fp in bold_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return get_font(size)

# === UTILITY FUNCTIONS ===

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def create_gradient_bg(w, h, color1, color2, direction='vertical'):
    """Create a gradient background"""
    img = Image.new('RGB', (w, h))
    draw = ImageDraw.Draw(img)
    for i in range(h if direction == 'vertical' else w):
        ratio = i / (h if direction == 'vertical' else w)
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        if direction == 'vertical':
            draw.line([(0, i), (w, i)], fill=(r, g, b))
        else:
            draw.line([(i, 0), (i, h)], fill=(r, g, b))
    return img

def add_glow(img, x, y, radius, color, intensity=0.5):
    """Add a glow effect at position"""
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for r in range(radius, 0, -2):
        alpha = int(intensity * 255 * (1 - r / radius) ** 2)
        c = (*color, alpha)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=c)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    return Image.alpha_composite(img, overlay)

def load_logo():
    """Load and prepare the LILIWATT logo"""
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert('RGBA')
        return logo
    return None

def ease_in_out(t):
    """Smooth easing function"""
    return t * t * (3 - 2 * t)

def ease_out(t):
    return 1 - (1 - t) ** 3


# === SCENE 1: ACCROCHE (0-5 sec, 125 frames) ===
def make_scene1():
    duration = 5.0
    frames_total = int(duration * FPS)

    logo = load_logo()
    text_main = "Vous payez votre énergie trop cher."
    text_sub = "Et vous ne le savez pas."

    def make_frame(t):
        img = Image.new('RGB', (W, H), FOND)
        draw = ImageDraw.Draw(img)

        # Logo fade in (0 to 1.5s)
        if logo:
            logo_alpha = min(1.0, t / 1.5)
            logo_alpha = ease_out(logo_alpha)
            logo_resized = logo.copy()
            logo_w = 200
            logo_h = int(logo_resized.height * logo_w / logo_resized.width)
            logo_resized = logo_resized.resize((logo_w, logo_h), Image.LANCZOS)
            # Apply alpha
            if logo_resized.mode == 'RGBA':
                r, g, b, a = logo_resized.split()
                a = a.point(lambda x: int(x * logo_alpha))
                logo_resized = Image.merge('RGBA', (r, g, b, a))
            img_rgba = img.convert('RGBA')
            lx = (W - logo_w) // 2
            ly = 120
            img_rgba.paste(logo_resized, (lx, ly), logo_resized)
            img = img_rgba.convert('RGB')
            draw = ImageDraw.Draw(img)

            # Add glow behind logo
            if logo_alpha > 0.3:
                glow_img = img.convert('RGBA')
                glow_img = add_glow(glow_img, W // 2, ly + logo_h // 2,
                                   int(150 * logo_alpha), VIOLET, 0.3 * logo_alpha)
                img = glow_img.convert('RGB')
                draw = ImageDraw.Draw(img)

        # Main text - letter by letter (1s to 3.5s)
        font_main = get_bold_font(42)
        if t > 1.0:
            text_progress = min(1.0, (t - 1.0) / 2.5)
            chars_to_show = int(len(text_main) * text_progress)
            visible_text = text_main[:chars_to_show]

            bbox = draw.textbbox((0, 0), visible_text, font=font_main)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2
            # Also measure full text to center properly
            full_bbox = draw.textbbox((0, 0), text_main, font=font_main)
            full_tw = full_bbox[2] - full_bbox[0]
            tx = (W - full_tw) // 2

            draw.text((tx, 340), visible_text, fill=BLANC, font=font_main)

        # Sub text fade in (3.5s to 5s)
        if t > 3.5:
            sub_alpha = min(1.0, (t - 3.5) / 1.0)
            sub_alpha = ease_out(sub_alpha)
            font_sub = get_font(30)
            bbox = draw.textbbox((0, 0), text_sub, font=font_sub)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2
            y_offset = int(10 * (1 - sub_alpha))

            # Draw with alpha by using overlay
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            odraw = ImageDraw.Draw(overlay)
            color_with_alpha = (*LAVANDE, int(255 * sub_alpha))
            odraw.text((tx, 420 + y_offset), text_sub, fill=color_with_alpha, font=font_sub)
            img_rgba = img.convert('RGBA')
            img = Image.alpha_composite(img_rgba, overlay).convert('RGB')

        return np.array(img)

    clip = ImageClip(make_frame(0), duration=duration)
    clip = clip.with_effects([])

    # Build frame by frame
    def frame_func(t):
        return make_frame(t)

    from moviepy import VideoClip
    clip = VideoClip(frame_func, duration=duration)
    return clip


# === SCENE 2: LE PROBLÈME (5-10 sec) ===
def make_scene2():
    duration = 5.0

    # Try to find a relevant image
    img_candidates = [
        os.path.join(IMG_DIR, "Analyse complète de vos contrats.png"),
        os.path.join(IMG_DIR, "auditgratuit.png"),
    ]
    bg_image = None
    for path in img_candidates:
        if os.path.exists(path):
            bg_image = Image.open(path).convert('RGB')
            break

    def make_frame(t):
        # Background
        if bg_image:
            # Ken Burns effect: slow zoom 1.0 -> 1.08
            zoom = 1.0 + 0.08 * (t / duration)
            img_w = int(W * zoom)
            img_h = int(H * zoom)
            resized = bg_image.resize((img_w, img_h), Image.LANCZOS)
            # Crop center
            left = (img_w - W) // 2
            top = (img_h - H) // 2
            cropped = resized.crop((left, top, left + W, top + H))
            # Darken overlay
            dark = Image.new('RGBA', (W, H), (6, 6, 15, 180))
            img = cropped.convert('RGBA')
            img = Image.alpha_composite(img, dark).convert('RGB')
        else:
            img = create_gradient_bg(W, H, FOND, (26, 10, 46))

        draw = ImageDraw.Draw(img)

        # Main text slide in from left (0.5s to 2s)
        if t > 0.5:
            progress = min(1.0, (t - 0.5) / 1.5)
            progress = ease_out(progress)

            font_text = get_font(28)
            line1 = "60% des professionnels surpaient"
            line2 = "leur énergie chaque année"

            x_offset = int(-300 * (1 - progress))
            alpha = progress

            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            odraw = ImageDraw.Draw(overlay)
            c = (*BLANC, int(255 * alpha))
            odraw.text((100 + x_offset, 250), line1, fill=c, font=font_text)
            odraw.text((100 + x_offset, 290), line2, fill=c, font=font_text)

            img_rgba = img.convert('RGBA')
            img = Image.alpha_composite(img_rgba, overlay).convert('RGB')
            draw = ImageDraw.Draw(img)

        # Big "18%" number (2s to 5s)
        if t > 2.0:
            num_progress = min(1.0, (t - 2.0) / 1.0)
            num_progress = ease_out(num_progress)

            font_big = get_bold_font(140)
            text_18 = "18%"

            bbox = draw.textbbox((0, 0), text_18, font=font_big)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = (W - tw) // 2 + 150
            ty = 350

            scale = 0.5 + 0.5 * num_progress

            # Draw with gradient effect (violet to fuchsia)
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            odraw = ImageDraw.Draw(overlay)

            # Glow
            glow_overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            glow_overlay = add_glow(glow_overlay, tx + tw // 2, ty + th // 2,
                                   int(120 * num_progress), VIOLET, 0.4 * num_progress)
            img_rgba = img.convert('RGBA')
            img = Image.alpha_composite(img_rgba, glow_overlay).convert('RGB')
            draw = ImageDraw.Draw(img)

            # The number itself
            alpha_val = int(255 * num_progress)
            draw.text((tx, ty), text_18, fill=(*FUCHSIA,), font=font_big)

            # Label under the number
            if t > 2.8:
                label_a = min(1.0, (t - 2.8) / 0.8)
                font_label = get_font(22)
                label = "de surcoût en moyenne"
                lbbox = draw.textbbox((0, 0), label, font=font_label)
                ltw = lbbox[2] - lbbox[0]
                lx = tx + (tw - ltw) // 2

                overlay2 = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                od2 = ImageDraw.Draw(overlay2)
                od2.text((lx, ty + th + 20), label, fill=(*LAVANDE, int(255 * label_a)), font=font_label)
                img = Image.alpha_composite(img.convert('RGBA'), overlay2).convert('RGB')

        return np.array(img)

    from moviepy import VideoClip
    return VideoClip(make_frame, duration=duration)


# === SCENE 3: LA SOLUTION (10-18 sec, 8 seconds) ===
def make_scene3():
    duration = 8.0

    # Try to find a relevant image
    img_candidates = [
        os.path.join(IMG_DIR, "accompagnement.png"),
        os.path.join(IMG_DIR, "Négociation.png"),
    ]
    bg_image = None
    for path in img_candidates:
        if os.path.exists(path):
            bg_image = Image.open(path).convert('RGB')
            break

    lines = [
        "LILIWATT analyse votre contrat",
        "Compare tous les fournisseurs",
        "Négocie le meilleur tarif",
    ]

    def make_frame(t):
        # Background gradient
        img = create_gradient_bg(W, H, FOND, (26, 10, 46))

        # If we have an image, composite it on the right
        if bg_image:
            zoom = 1.0 + 0.05 * (t / duration)
            panel_w = W // 2
            panel_h = H
            img_ratio = bg_image.width / bg_image.height
            panel_ratio = panel_w / panel_h
            if img_ratio > panel_ratio:
                new_h = int(panel_h * zoom)
                new_w = int(new_h * img_ratio)
            else:
                new_w = int(panel_w * zoom)
                new_h = int(new_w / img_ratio)
            resized = bg_image.resize((new_w, new_h), Image.LANCZOS)
            left = (new_w - panel_w) // 2
            top = (new_h - panel_h) // 2
            cropped = resized.crop((left, top, left + panel_w, top + panel_h))

            # Darken
            dark = Image.new('RGBA', (panel_w, panel_h), (6, 6, 15, 140))
            panel = cropped.convert('RGBA')
            panel = Image.alpha_composite(panel, dark).convert('RGB')
            img.paste(panel, (W // 2, 0))

        draw = ImageDraw.Draw(img)

        # Title
        font_title = get_bold_font(38)
        title = "La Solution"
        if t > 0.3:
            ta = min(1.0, (t - 0.3) / 0.8)
            ta = ease_out(ta)
            bbox = draw.textbbox((0, 0), title, font=font_title)
            y_off = int(20 * (1 - ta))
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.text((80, 140 + y_off), title, fill=(*VIOLET, int(255 * ta)), font=font_title)
            # Underline
            tw = bbox[2] - bbox[0]
            od.rectangle([80, 190 + y_off, 80 + int(tw * ta), 193 + y_off], fill=(*FUCHSIA, int(255 * ta)))
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)

        # Lines appearing one by one
        font_line = get_font(30)
        check_font = get_bold_font(30)

        for i, line in enumerate(lines):
            start_time = 1.5 + i * 1.2
            if t > start_time:
                progress = min(1.0, (t - start_time) / 0.8)
                progress = ease_out(progress)

                y_base = 260 + i * 70
                y_offset = int(30 * (1 - progress))
                alpha = int(255 * progress)

                overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                od = ImageDraw.Draw(overlay)

                # Checkmark
                od.text((80, y_base + y_offset), "✓", fill=(*VERT, alpha), font=check_font)

                # Text
                od.text((120, y_base + y_offset), line, fill=(*BLANC, alpha), font=font_line)

                img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
                draw = ImageDraw.Draw(img)

        return np.array(img)

    from moviepy import VideoClip
    return VideoClip(make_frame, duration=duration)


# === SCENE 4: LES CHIFFRES (18-24 sec, 6 seconds) ===
def make_scene4():
    duration = 6.0

    stats = [
        {"value": 1460, "suffix": "€", "label": "économisés en moyenne / an", "color": ROUGE},
        {"value": 0, "suffix": "€", "label": "de frais", "color": VERT},
        {"value": 3, "suffix": " sem.", "label": "pour changer", "color": LAVANDE},
    ]

    def make_frame(t):
        img = Image.new('RGB', (W, H), FOND)
        draw = ImageDraw.Draw(img)

        # Animated purple particles background
        img_rgba = img.convert('RGBA')
        for j in range(15):
            seed = j * 137 + 42
            px = int((seed * 7 + int(t * 30) * (j + 1)) % W)
            py = int((seed * 13 + int(t * 20) * (j + 2)) % H)
            size = 2 + (seed % 4)
            alpha = 30 + (seed % 50)
            particle = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            pd = ImageDraw.Draw(particle)
            pd.ellipse([px - size, py - size, px + size, py + size],
                      fill=(*VIOLET, alpha))
            img_rgba = Image.alpha_composite(img_rgba, particle)
        img = img_rgba.convert('RGB')
        draw = ImageDraw.Draw(img)

        # Title
        font_title = get_bold_font(36)
        if t > 0.2:
            ta = min(1.0, (t - 0.2) / 0.6)
            title = "Nos Résultats"
            bbox = draw.textbbox((0, 0), title, font=font_title)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) // 2, 80), title, fill=BLANC, font=font_title)

        # Stats
        font_num = get_bold_font(72)
        font_label = get_font(22)

        col_width = W // 3

        for i, stat in enumerate(stats):
            start_time = 1.0 + i * 1.2
            if t > start_time:
                progress = min(1.0, (t - start_time) / 1.0)
                progress_ease = ease_out(progress)

                # Counter animation
                current_val = int(stat["value"] * progress_ease)
                text_val = f"{current_val}{stat['suffix']}"

                cx = col_width * i + col_width // 2

                # Number
                bbox = draw.textbbox((0, 0), text_val, font=font_num)
                tw = bbox[2] - bbox[0]
                tx = cx - tw // 2
                ty = 260

                # Glow behind number
                img_rgba = img.convert('RGBA')
                img_rgba = add_glow(img_rgba, cx, ty + 30,
                                   int(80 * progress_ease), stat["color"], 0.25 * progress_ease)
                img = img_rgba.convert('RGB')
                draw = ImageDraw.Draw(img)

                draw.text((tx, ty), text_val, fill=stat["color"], font=font_num)

                # Label
                if progress > 0.5:
                    label_alpha = min(1.0, (progress - 0.5) / 0.5)
                    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                    od = ImageDraw.Draw(overlay)
                    lbbox = draw.textbbox((0, 0), stat["label"], font=font_label)
                    ltw = lbbox[2] - lbbox[0]
                    lx = cx - ltw // 2
                    od.text((lx, 370), stat["label"],
                           fill=(*BLANC, int(200 * label_alpha)), font=font_label)
                    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
                    draw = ImageDraw.Draw(img)

        # Dividers between stats
        if t > 1.5:
            div_a = min(1.0, (t - 1.5) / 0.5)
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            for i in range(1, 3):
                x = col_width * i
                od.line([(x, 230), (x, 400)], fill=(*VIOLET, int(80 * div_a)), width=1)
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

        return np.array(img)

    from moviepy import VideoClip
    return VideoClip(make_frame, duration=duration)


# === SCENE 5: CTA FINAL (24-30 sec, 6 seconds) ===
def make_scene5():
    duration = 6.0
    logo = load_logo()

    def make_frame(t):
        # Premium gradient background
        img = create_gradient_bg(W, H, (26, 10, 46), (60, 20, 80))
        draw = ImageDraw.Draw(img)

        # Central glow
        img_rgba = img.convert('RGBA')
        img_rgba = add_glow(img_rgba, W // 2, H // 2, 300, VIOLET, 0.2)
        img_rgba = add_glow(img_rgba, W // 2, H // 2 - 50, 200, FUCHSIA, 0.15)
        img = img_rgba.convert('RGB')
        draw = ImageDraw.Draw(img)

        # Logo - big, centered, with glow
        if logo:
            logo_alpha = min(1.0, t / 1.2)
            logo_alpha = ease_out(logo_alpha)

            logo_w = 300
            logo_h = int(logo.height * logo_w / logo.width)
            logo_resized = logo.resize((logo_w, logo_h), Image.LANCZOS)

            if logo_resized.mode == 'RGBA':
                r, g, b, a = logo_resized.split()
                a = a.point(lambda x: int(x * logo_alpha))
                logo_resized = Image.merge('RGBA', (r, g, b, a))

            lx = (W - logo_w) // 2
            ly = 130

            # Glow behind logo
            img_rgba = img.convert('RGBA')
            glow_strength = 0.4 * logo_alpha
            img_rgba = add_glow(img_rgba, W // 2, ly + logo_h // 2,
                               int(180 * logo_alpha), VIOLET, glow_strength)
            img_rgba.paste(logo_resized, (lx, ly), logo_resized)
            img = img_rgba.convert('RGB')
            draw = ImageDraw.Draw(img)

        # "Votre énergie mérite mieux."
        if t > 1.5:
            fa = min(1.0, (t - 1.5) / 1.0)
            fa = ease_out(fa)
            font_main = get_bold_font(44)
            text = "Votre énergie mérite mieux."
            bbox = draw.textbbox((0, 0), text, font=font_main)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2
            y_off = int(15 * (1 - fa))

            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.text((tx, 380 + y_off), text, fill=(*BLANC, int(255 * fa)), font=font_main)
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)

        # URL "liliwatt.fr"
        if t > 3.0:
            url_a = min(1.0, (t - 3.0) / 0.8)
            url_a = ease_out(url_a)
            font_url = get_bold_font(48)
            url = "liliwatt.fr"
            bbox = draw.textbbox((0, 0), url, font=font_url)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2

            # Glow behind URL
            img_rgba = img.convert('RGBA')
            img_rgba = add_glow(img_rgba, W // 2, 490, int(100 * url_a), FUCHSIA, 0.3 * url_a)
            img = img_rgba.convert('RGB')
            draw = ImageDraw.Draw(img)

            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.text((tx, 470), url, fill=(*FUCHSIA, int(255 * url_a)), font=font_url)
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)

        # Sub-text
        if t > 4.0:
            sub_a = min(1.0, (t - 4.0) / 0.8)
            sub_a = ease_out(sub_a)
            font_sub = get_font(24)
            sub = "Analyse gratuite en 60 secondes"
            bbox = draw.textbbox((0, 0), sub, font=font_sub)
            tw = bbox[2] - bbox[0]
            tx = (W - tw) // 2
            y_off = int(10 * (1 - sub_a))

            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.text((tx, 545 + y_off), sub, fill=(*LAVANDE, int(255 * sub_a)), font=font_sub)
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

        # Fade out last 0.3s
        if t > duration - 0.3:
            fade = 1.0 - (t - (duration - 0.3)) / 0.3
            arr = np.array(img).astype(float) * fade
            return arr.astype(np.uint8)

        return np.array(img)

    from moviepy import VideoClip
    return VideoClip(make_frame, duration=duration)


# === ASSEMBLY ===
def main():
    print("=" * 50)
    print("LILIWATT — Génération vidéo publicitaire")
    print("=" * 50)

    print("\n[1/5] Création Scène 1 — Accroche...")
    scene1 = make_scene1()

    print("[2/5] Création Scène 2 — Le Problème...")
    scene2 = make_scene2()

    print("[3/5] Création Scène 3 — La Solution...")
    scene3 = make_scene3()

    print("[4/5] Création Scène 4 — Les Chiffres...")
    scene4 = make_scene4()

    print("[5/5] Création Scène 5 — CTA Final...")
    scene5 = make_scene5()

    print("\nAssemblage avec fondus enchaînés...")

    # Add crossfade transitions
    crossfade = 0.5

    # Apply crossfades between scenes
    scenes = [scene1, scene2, scene3, scene4, scene5]

    # Use crossfade transitions
    clips = []
    for i, scene in enumerate(scenes):
        if i == 0:
            clip = scene.with_effects([])
            # Fade in from black for first scene
            from moviepy.video.fx import CrossFadeIn, CrossFadeOut
            clip = clip.with_effects([CrossFadeIn(0.5)])
        else:
            clip = scene

        if i < len(scenes) - 1:
            clip = clip.with_effects([CrossFadeOut(crossfade)])

        clips.append(clip)

    # Concatenate with crossfade method
    final = concatenate_videoclips(clips, method="compose", padding=-crossfade)

    print(f"\nRendu vidéo → {OUTPUT}")
    print(f"Résolution: {W}x{H} | FPS: {FPS} | Durée: ~{final.duration:.1f}s")

    final.write_videofile(
        OUTPUT,
        fps=FPS,
        codec='libx264',
        audio=False,
        preset='medium',
        threads=4,
        logger='bar'
    )

    print(f"\n✅ Vidéo générée avec succès !")
    print(f"📁 Fichier : {OUTPUT}")
    print(f"📐 Résolution : {W}x{H}")
    print(f"🎬 Durée : ~{final.duration:.1f} secondes")


if __name__ == "__main__":
    main()
