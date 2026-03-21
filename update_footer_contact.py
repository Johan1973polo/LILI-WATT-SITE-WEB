#!/usr/bin/env python3
"""
Script pour s'assurer que tous les footers ont le bon numéro et l'adresse
"""
import re
from pathlib import Path

# Fichiers HTML à vérifier
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

# Info de contact correcte
correct_phone = "Tél : +33 (0)1 84 16 08 56"
correct_address_line1 = "59 rue de Ponthieu, Bureau 326"
correct_address_line2 = "75008 Paris"

total_changes = 0

for html_file in html_files:
    file_path = base_path / html_file

    if not file_path.exists():
        print(f"⚠️  Fichier non trouvé : {html_file}")
        continue

    print(f"\n📝 Vérification de {html_file}...")

    # Lire le contenu
    content = file_path.read_text(encoding='utf-8')
    original_content = content

    # Vérifier si le footer contient déjà les bonnes infos
    has_correct_phone = correct_phone in content
    has_correct_address = correct_address_line1 in content and correct_address_line2 in content

    if has_correct_phone and has_correct_address:
        print(f"  ✅ Footer déjà à jour")
    else:
        print(f"  ℹ️  Footer nécessite une mise à jour")
        # Vous pouvez ajouter ici la logique de mise à jour si nécessaire

print(f"\n🎉 Vérification terminée !")
