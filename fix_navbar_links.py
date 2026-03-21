#!/usr/bin/env python3
"""
Script pour remplacer tous les liens relatifs par des chemins absolus dans la navbar
"""
import re
from pathlib import Path

# Fichiers HTML à modifier
html_files = [
    "apropos.html",
    "blog.html",
    "contact.html",
    "recrutement.html",
    "offres.html",
    "blog-article.html",
    "extracteur.html",
    "templates/blog.html",
    "templates/extracteur.html"
]

base_path = Path("/Users/strategyglobal/Desktop/liliwatt-website")

# Mapping des remplacements
link_replacements = {
    'href="index.html"': 'href="/"',
    "href='index.html'": "href='/'",

    'href="offres.html"': 'href="/offres"',
    "href='offres.html'": "href='/offres'",

    'href="apropos.html"': 'href="/apropos"',
    "href='apropos.html'": "href='/apropos'",

    'href="blog.html"': 'href="/blog"',
    "href='blog.html'": "href='/blog'",

    'href="contact.html"': 'href="/contact"',
    "href='contact.html'": "href='/contact'",

    'href="recrutement.html"': 'href="/recrutement"',
    "href='recrutement.html'": "href='/recrutement'",

    'href="extracteur.html"': 'href="/extracteur"',
    "href='extracteur.html'": "href='/extracteur'",

    'href="blog-article.html"': 'href="/blog-article"',
    "href='blog-article.html'": "href='/blog-article'",
}

total_changes = 0

for html_file in html_files:
    file_path = base_path / html_file

    if not file_path.exists():
        print(f"⚠️  Fichier non trouvé : {html_file}")
        continue

    print(f"\n📝 Traitement de {html_file}...")

    # Lire le contenu
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    file_changes = 0

    # Remplacer tous les liens
    for old_link, new_link in link_replacements.items():
        count = content.count(old_link)
        if count > 0:
            content = content.replace(old_link, new_link)
            file_changes += count
            print(f"  ✓ {old_link} → {new_link} ({count} occurrence(s))")

    # Écrire le contenu modifié seulement si des changements ont été faits
    if file_changes > 0:
        file_path.write_text(content, encoding='utf-8')
        print(f"  ✅ {file_changes} lien(s) modifié(s)")
        total_changes += file_changes
    else:
        print(f"  ℹ️  Aucun changement nécessaire")

print(f"\n🎉 Terminé ! {total_changes} lien(s) corrigé(s) au total dans {len([f for f in html_files if (base_path / f).exists()])} fichier(s)")
