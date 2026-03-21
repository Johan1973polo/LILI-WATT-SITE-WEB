#!/usr/bin/env python3
"""
Script pour supprimer le lien "Extracteur de factures" de la navbar
dans tous les fichiers HTML
"""
import re
from pathlib import Path

# Fichiers HTML à modifier
html_files = [
    "index.html",
    "apropos.html",
    "blog.html",
    "contact.html",
    "recrutement.html",
    "offres.html",
    "blog-article.html",
    "extracteur.html"
]

base_path = Path("/Users/strategyglobal/Desktop/liliwatt-website")

for html_file in html_files:
    file_path = base_path / html_file

    if not file_path.exists():
        print(f"⚠️  Fichier non trouvé : {html_file}")
        continue

    print(f"\n📝 Traitement de {html_file}...")

    # Lire le contenu
    content = file_path.read_text(encoding='utf-8')
    original_content = content

    # Supprimer la ligne contenant "Extracteur de factures" dans la navbar
    # Pattern: <li><a href="/extracteur" class="nav-link badge">Extracteur de factures</a></li>
    pattern = r'<li>\s*<a\s+href="/extracteur"\s+class="nav-link\s+badge">Extracteur de factures</a>\s*</li>\s*\n?'

    content = re.sub(pattern, '', content)

    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"  ✅ Lien Extracteur supprimé de la navbar")
    else:
        print(f"  ℹ️  Aucun changement (lien déjà absent ou différent)")

print(f"\n🎉 Terminé !")
