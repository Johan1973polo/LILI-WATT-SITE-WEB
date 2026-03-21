#!/usr/bin/env python3
"""
Script pour remplacer tous les logos par le logo transparent dans les fichiers HTML
"""
import re
from pathlib import Path

# Fichiers HTML à modifier
html_files = [
    "index.html",
    "blog.html",
    "contact.html",
    "recrutement.html",
    "apropos.html",
    "offres.html",
    "blog-article.html",
    "extracteur.html",
    "templates/blog.html",
    "templates/extracteur.html"
]

base_path = Path("/Users/strategyglobal/Desktop/liliwatt-website")

def replace_navbar_logo(content):
    """Remplace le logo dans la navbar par le logo transparent"""

    # Pattern pour la navbar avec vidéo animée et fallback image
    pattern_video = re.compile(
        r'<video[^>]*class="navbar-logo-video"[^>]*>.*?'
        r'<source[^>]*src="[^"]*logo-animation\.mp4"[^>]*>.*?'
        r'<img[^>]*src="[^"]*logo-liliwatt\.png"[^>]*>.*?'
        r'</video>',
        re.DOTALL
    )

    replacement_video = '''<img src="/assets/images/logo-transparent.png"
             alt="LILIWATT - Courtier en énergie B2B"
             class="navbar-logo"
             style="height: 45px; width: auto; background: transparent;">'''

    content = pattern_video.sub(replacement_video, content)

    # Pattern pour les images logo simples dans navbar
    pattern_img = re.compile(
        r'<img[^>]*src="[^"]*logo-liliwatt\.png"[^>]*class="logo-liliwatt"[^>]*>',
        re.DOTALL
    )

    replacement_img = '''<img src="/assets/images/logo-transparent.png"
             alt="LILIWATT - Courtier en énergie B2B"
             class="navbar-logo"
             style="height: 45px; width: auto; background: transparent;">'''

    content = pattern_img.sub(replacement_img, content)

    return content

def replace_footer_logo(content):
    """Remplace le logo dans le footer"""

    # Pattern pour le footer avec vidéo
    pattern_footer_video = re.compile(
        r'<video[^>]*autoplay[^>]*muted[^>]*loop[^>]*playsinline[^>]*>.*?'
        r'<source[^>]*src="[^"]*logo-animation\.mp4"[^>]*>.*?'
        r'<img[^>]*src="[^"]*logo-liliwatt\.png"[^>]*>.*?'
        r'</video>',
        re.DOTALL
    )

    replacement_footer = '''<img src="/assets/images/logo-transparent.png"
                 alt="LILIWATT"
                 class="footer-logo-img"
                 style="height: 80px; width: auto; background: transparent;">'''

    content = pattern_footer_video.sub(replacement_footer, content)

    return content

# Traiter chaque fichier HTML
for html_file in html_files:
    file_path = base_path / html_file

    if not file_path.exists():
        print(f"⚠️  Fichier non trouvé : {html_file}")
        continue

    print(f"📝 Traitement de {html_file}...")

    # Lire le contenu
    content = file_path.read_text(encoding='utf-8')

    # Remplacer les logos
    content = replace_navbar_logo(content)
    content = replace_footer_logo(content)

    # Écrire le contenu modifié
    file_path.write_text(content, encoding='utf-8')

    print(f"✅ {html_file} modifié")

print("\n🎉 Tous les fichiers HTML ont été mis à jour !")
