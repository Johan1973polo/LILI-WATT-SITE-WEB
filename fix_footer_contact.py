#!/usr/bin/env python3
"""
Script pour mettre à jour le footer Contact sur toutes les pages
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
    "extracteur.html"
]

base_path = Path("/Users/strategyglobal/Desktop/liliwatt-website")

# Le footer correct (comme dans index.html)
correct_footer_contact = """          <h4>Contact</h4>
          <ul>
            <li><a href="mailto:contact@liliwatt.fr">contact@liliwatt.fr</a></li>
            <li>Tél : +33 (0)1 84 16 08 56</li>
            <li>59 rue de Ponthieu, Bureau 326</li>
            <li>75008 Paris</li>
            <li>Lun-Ven : 9h-18h</li>
          </ul>"""

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

    # Pattern pour trouver et remplacer la section Contact du footer
    # Le pattern cherche <h4>Contact</h4> suivi de <ul>...</ul>
    pattern = r'<h4>Contact</h4>\s*<ul>.*?</ul>'

    # Remplacement
    replacement = correct_footer_contact

    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"  ✅ Footer Contact mis à jour")
        total_changes += 1
    else:
        print(f"  ℹ️  Aucun changement nécessaire")

print(f"\n🎉 Terminé ! {total_changes} fichier(s) mis à jour")
